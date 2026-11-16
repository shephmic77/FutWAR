"""Compare OpenPlay and Wyscout 2017-18 match scores and goal-event actors.

This is an aggregate, independent-provider corroboration audit, not a gold
standard for identities or a validation of general event actor attribution.
Raw archives are read in place and checked against the repository manifests.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import zipfile
from difflib import SequenceMatcher
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WYSCOUT_MANIFEST = ROOT / "data/wyscout_research_manifest.json"
OPENPLAY_MANIFEST = ROOT / "data/openplay_source_manifest.json"
WYSCOUT_DIR = ROOT / "data/raw/wyscout_research/2026-10-10"
OPENPLAY_DIR = ROOT / "data/raw/openplay/data-v0.1.0"
OUTPUT = ROOT / "reports/cross_provider_goal_scorer_audit"
KEEPER_OUTPUT = OUTPUT / "goalkeeper_profile_actor_overlap.csv"
KEEPER_EVENT_OUTPUT = OUTPUT / "wyscout_keeper_event_integrity.csv"

LEAGUES = {
    "England": ("eng", "Premier League", 364),
    "Spain": ("esp", "La Liga", 795),
    "Italy": ("ita", "Serie A", 524),
    "Germany": ("ger", "Bundesliga", 426),
    "France": ("fra", "Ligue 1", 412),
}
WYSCOUT_COUNTRY = {"England": "England", "Spain": "Spain", "Italy": "Italy",
                   "Germany": "Germany", "France": "France"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sources() -> dict[str, str]:
    """Verify every source file used here against its pinned manifest entry."""
    pins: dict[str, str] = {}
    for manifest_path, needed in (
        (WYSCOUT_MANIFEST, {"players.json", "matches.zip", "events.zip"}),
        (OPENPLAY_MANIFEST, {"matches.parquet", "players.parquet"} |
         {f"events_{code}_1718.parquet" for code, _, _ in LEAGUES.values()}),
    ):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest["files"]
        selected = [entry for entry in entries
                    if Path(entry["path"]).name in needed]
        found = {Path(entry["path"]).name for entry in selected}
        if found != needed:
            raise ValueError(f"Manifest entries missing: {sorted(needed - found)}")
        for entry in selected:
            path = ROOT / entry["path"]
            if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
                raise ValueError(f"Pinned source changed: {entry['path']}")
            pins[entry["path"]] = entry["sha256"]
    return pins


def normalize(value: object) -> str:
    """Normalize provider spellings, including literal escaped Unicode."""
    text = str(value or "")
    text = re.sub(r"\\u([0-9a-fA-F]{4})",
                  lambda match: chr(int(match.group(1), 16)), text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def canonicalizer(league: str):
    aliases: dict[tuple[str, str], str] = {}
    for filename in ("club_aliases.json", "identity_club_aliases.json",
                     "wikipedia_club_aliases.json"):
        content = json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))
        for alias_league, pairs in content.items():
            for source, target in pairs.items():
                aliases.setdefault((alias_league, normalize(source)), normalize(target))

    def canonical(team: object) -> str:
        value = normalize(team)
        return aliases.get((league, value), value)

    return canonical


def exact_fixture_bridge(country: str, code: str, league: str,
                          matches_zip: zipfile.ZipFile) -> tuple[dict[int, tuple[int, dict[int, str], tuple]], dict, dict]:
    """Link on date and home/away clubs only; scores are intentionally excluded."""
    canonical = canonicalizer(league)
    op = pd.read_parquet(OPENPLAY_DIR / "matches.parquet", columns=[
        "match_id", "comp", "season", "date", "home_team", "away_team",
        "home_score_90", "away_score_90",
    ])
    op = op[(op["comp"] == code) & (op["season"] == "1718")].copy()
    open_keys: dict[tuple[str, str, str], object] = {}
    open_rows = {}
    for row in op.itertuples(index=False):
        key = (pd.Timestamp(row.date).strftime("%Y-%m-%d"),
               canonical(row.home_team), canonical(row.away_team))
        if key in open_keys:
            raise ValueError(f"Ambiguous OpenPlay fixture key in {league}: {key}")
        open_keys[key] = int(row.match_id)
        open_rows[key] = (int(row.home_score_90), int(row.away_score_90))

    wyscout = json.load(matches_zip.open(f"matches_{country}.json"))
    bridge = {}
    match_rosters: dict[int, dict[int, set[int]]] = {}
    score_checks = 0
    score_mismatches = 0
    for match in wyscout:
        sides = {row["side"]: row for row in match["teamsData"].values()}
        team_text = match["label"].split(",", 1)[0].split(" - ", 1)
        if len(team_text) != 2:
            raise ValueError(f"Cannot parse Wyscout fixture label: {match['label']}")
        date = str(match["dateutc"])[:10]
        key = (date, canonical(team_text[0]), canonical(team_text[1]))
        if key not in open_keys:
            raise ValueError(f"Unmatched Wyscout fixture in {league}: {key}")
        open_id = open_keys[key]
        if open_id in (value[0] for value in bridge.values()):
            raise ValueError(f"Duplicate OpenPlay match link in {league}: {open_id}")
        sides_by_id = {int(row["teamId"]): row["side"] for row in sides.values()}
        match_rosters[int(match["wyId"])] = {}
        for team in sides.values():
            team_id = int(team["teamId"])
            formation = team.get("formation")
            roster: set[int] = set()
            if isinstance(formation, dict):
                for group in ("lineup", "bench"):
                    for player in formation.get(group, []):
                        if isinstance(player, dict) and player.get("playerId"):
                            roster.add(int(player["playerId"]))
                substitutions = formation.get("substitutions")
                if isinstance(substitutions, list):
                    for substitution in substitutions:
                        if isinstance(substitution, dict):
                            for field in ("playerIn", "playerOut"):
                                if substitution.get(field):
                                    roster.add(int(substitution[field]))
            match_rosters[int(match["wyId"])][team_id] = roster
        open_score = open_rows[key]
        wyscout_score = (int(sides["home"]["score"]), int(sides["away"]["score"]))
        score_checks += 1
        score_mismatches += open_score != wyscout_score
        bridge[int(match["wyId"])] = (
            open_id, sides_by_id, (key, open_score, wyscout_score)
        )
    # This ensures no match was silently dropped by the provider join.
    if len(bridge) != len(op):
        raise ValueError(f"Fixture bridge incomplete for {league}: {len(bridge)} vs {len(op)}")
    return bridge, {"openplay_matches": len(op), "wyscout_matches": len(wyscout),
                    "linked_matches": len(bridge), "independent_score_checks": score_checks,
                    "score_mismatches": int(score_mismatches)}, match_rosters


def unique_name_aliases(left: Counter, right: Counter) -> dict[str, str]:
    """Find conservative one-to-one name variants within a match/team.

    Exact names are handled separately. A non-exact candidate requires at least
    two tokens on the shorter name, a unique token mapping (allowing a 0.90
    character similarity for a token of four or more characters), and unique
    pairing in both directions.
    """
    def tokens(name: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", name))

    def covered(shorter: set[str], longer: set[str]) -> bool:
        """Allow a unique one-character encoding loss, not broad fuzzy names."""
        remaining = set(longer)
        for token in sorted(shorter, key=lambda value: (-len(value), value)):
            matches = [candidate for candidate in remaining
                       if candidate == token or (
                           len(token) >= 4 and len(candidate) >= 4
                           and SequenceMatcher(None, token, candidate).ratio() >= 0.90
                       )]
            if len(matches) != 1:
                return False
            remaining.remove(matches[0])
        return True

    left_names = {name for name, count in left.items() if name and count}
    right_names = {name for name, count in right.items() if name and count}
    candidates: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    for left_name in left_names:
        if left_name in right_names:
            continue
        left_tokens = tokens(left_name)
        if len(left_tokens) < 2:
            continue
        for right_name in right_names:
            if right_name == left_name:
                continue
            right_tokens = tokens(right_name)
            shorter, longer = sorted((left_tokens, right_tokens), key=len)
            if len(shorter) >= 2 and covered(shorter, longer):
                candidates[left_name].add(right_name)
                reverse[right_name].add(left_name)
    return {left_name: next(iter(right_names_for_left))
            for left_name, right_names_for_left in candidates.items()
            if len(right_names_for_left) == 1
            and len(reverse[next(iter(right_names_for_left))]) == 1}


def main() -> None:
    pins = verify_sources()
    for filename in ("club_aliases.json", "identity_club_aliases.json",
                     "wikipedia_club_aliases.json"):
        alias_path = ROOT / "data" / filename
        pins[str(alias_path.relative_to(ROOT))] = sha256(alias_path)
    wy_players = json.loads((WYSCOUT_DIR / "players.json").read_text(encoding="utf-8"))
    wy_names = {
        int(player["wyId"]): normalize(
            str(player.get("firstName", "")) + " " + str(player.get("lastName", ""))
        ) for player in wy_players
    }
    if len(wy_names) != len(wy_players):
        raise ValueError("Duplicate Wyscout player profile IDs")
    summaries = []
    roster_summaries = []
    keeper_summaries = []
    keeper_event_summaries = []
    keeper_goal_tag_mismatches = []
    totals = Counter()
    with zipfile.ZipFile(WYSCOUT_DIR / "matches.zip") as matches_zip, \
            zipfile.ZipFile(WYSCOUT_DIR / "events.zip") as events_zip:
        for country, (code, league, competition_id) in LEAGUES.items():
            bridge, match_summary, match_rosters = exact_fixture_bridge(
                WYSCOUT_COUNTRY[country], code, league, matches_zip
            )
            match_ids = {row[0] for row in bridge.values()}
            canonical = canonicalizer(league)
            # This is a narrow candidate identity check: Wyscout players whose
            # profile role is GK and who appear as actors are compared with
            # OpenPlay's played, positive-minute GK lineup stints. It is not a
            # keeper-shot link or proof that either source's role is correct.
            open_lineups = pd.read_parquet(OPENPLAY_DIR / "lineups.parquet", columns=[
                "match_id", "comp", "season", "team", "player", "position",
                "played", "minutes_played",
            ])
            open_lineups = open_lineups[
                (open_lineups["comp"] == code)
                & (open_lineups["season"] == "1718")
                & open_lineups["played"].fillna(False)
                & (open_lineups["minutes_played"].fillna(0) > 0)
                & (open_lineups["position"] == "GK")
            ]
            open_keeper_stints: dict[tuple[int, str], set[str]] = defaultdict(set)
            for row in open_lineups.itertuples(index=False):
                open_keeper_stints[(int(row.match_id), canonical(row.team))].add(
                    normalize(row.player)
                )
            wyscout_gk_ids = {
                int(player["wyId"]): normalize(
                    str(player.get("firstName", "")) + " " + str(player.get("lastName", ""))
                )
                for player in wy_players
                if (player.get("role") or {}).get("code2") == "GK"
            }
            wyscout_keeper_actors: dict[tuple[int, str], set[str]] = defaultdict(set)
            open_players = pd.read_parquet(OPENPLAY_DIR / "players.parquet",
                                           columns=["player_id", "player"])
            open_names = {
                int(row.player_id): normalize(row.player)
                for row in open_players.itertuples(index=False)
                if pd.notna(row.player_id) and pd.notna(row.player)
            }
            event_rows = pd.read_parquet(OPENPLAY_DIR / f"events_{code}_1718.parquet", columns=[
                "match_id", "team", "player_id", "player", "is_goal",
                "q_OwnGoal", "q_GoalDisallowed",
            ])
            event_rows = event_rows[(event_rows["is_goal"] == True) &
                                    (event_rows["q_GoalDisallowed"] != True)].copy()
            open_counters: dict[tuple[int, str, str], Counter] = defaultdict(Counter)
            open_events_without_name = Counter()
            open_goal_event_counts = Counter()
            open_goal_counts_by_match = Counter()
            for row in event_rows.itertuples(index=False):
                is_own_goal = pd.notna(row.q_OwnGoal) and bool(row.q_OwnGoal)
                category = "own_goal" if is_own_goal else "regular_goal"
                name = normalize(row.player) if pd.notna(row.player) else ""
                # The event name is the primary attribution surface. Use the
                # pinned catalog only when the event label itself is absent.
                if not name and pd.notna(row.player_id):
                    name = open_names.get(int(row.player_id), "")
                team_key = (int(row.match_id), canonical(row.team), category)
                open_counters[team_key][name] += 1
                open_goal_event_counts[category] += 1
                open_goal_counts_by_match[int(row.match_id)] += 1
                open_events_without_name[category] += not bool(name)
            if not set(event_rows["match_id"].dropna().astype(int)).issubset(match_ids):
                raise ValueError(f"OpenPlay goal events outside fixture bridge: {league}")

            wy_events = json.load(events_zip.open(f"events_{country}.json"))
            wy_counters: dict[tuple[int, str, str], Counter] = defaultdict(Counter)
            wy_events_without_name = Counter()
            wy_goal_event_counts = Counter()
            wy_goal_counts_by_match = Counter()
            wyscout_keeper_event_counts = Counter()
            wyscout_keeper_conceded_goals_by_match = Counter()
            roster_link_counts = Counter()
            unlinked_actor_types = Counter()
            for event in wy_events:
                player_id = int(event.get("playerId") or 0)
                if not player_id:
                    roster_link_counts["zero_or_missing_actor_rows"] += 1
                else:
                    roster_link_counts["nonzero_actor_rows"] += 1
                    roster_link_counts["actor_id_in_player_catalog"] += player_id in wy_names
                    team_roster = match_rosters[int(event["matchId"])].get(int(event["teamId"]), set())
                    if player_id in team_roster:
                        roster_link_counts["actor_in_same_match_team_roster"] += 1
                    else:
                        roster_link_counts["actor_outside_same_match_team_roster"] += 1
                        unlinked_actor_types[event["eventName"]] += 1
                tags = {int(tag["id"]) for tag in event.get("tags", [])}
                if event.get("eventName") == "Save attempt":
                    subevent = str(event.get("subEventName") or "unknown")
                    team_roster = match_rosters[int(event["matchId"])].get(
                        int(event["teamId"]), set()
                    )
                    is_gk_profile = player_id in wyscout_gk_ids
                    wyscout_keeper_event_counts["save_attempt_rows"] += 1
                    wyscout_keeper_event_counts["save_attempt_rows_with_nonzero_actor"] += bool(player_id)
                    wyscout_keeper_event_counts["save_attempt_rows_with_gk_profile_actor"] += is_gk_profile
                    wyscout_keeper_event_counts["save_attempt_rows_actor_in_same_team_roster"] += bool(
                        player_id and player_id in team_roster
                    )
                    wyscout_keeper_event_counts["save_attempt_rows_gk_profile_and_rostered"] += bool(
                        is_gk_profile and player_id in team_roster
                    )
                    wyscout_keeper_event_counts["save_attempt_rows_non_gk_profile_actor"] += bool(
                        player_id and not is_gk_profile
                    )
                    wyscout_keeper_event_counts["save_attempt_rows_goal_conceded_tag_101"] += 101 in tags
                    wyscout_keeper_event_counts[f"save_attempt_subevent_{subevent}"] += 1
                    wyscout_keeper_conceded_goals_by_match[int(event["matchId"])] += 101 in tags
                if player_id in wyscout_gk_ids:
                    open_match_id, team_sides, fixture = bridge[int(event["matchId"])]
                    team_id = int(event["teamId"])
                    if team_id in team_sides:
                        side = team_sides[team_id]
                        team_name = fixture[0][1] if side == "home" else fixture[0][2]
                        wyscout_keeper_actors[(open_match_id, team_name)].add(
                            wyscout_gk_ids[player_id]
                        )
                # Tag 101 on a Wyscout Save attempt is a keeper's shot-against
                # outcome (goal conceded), not a scorer actor event. It stays
                # out of scorer-name counts; the provider glossary documents
                # that event/tag distinction.
                if 101 in tags and event["eventName"] != "Save attempt":
                    category = "regular_goal"
                elif 102 in tags:
                    category = "own_goal"
                else:
                    continue
                wy_goal_counts_by_match[int(event["matchId"])] += 1
                open_match_id, team_sides, (fixture_key, _, _) = bridge[int(event["matchId"])]
                team_id = int(event["teamId"])
                if team_id not in team_sides:
                    raise ValueError(f"Wyscout event team absent from fixture: {league}")
                side = team_sides[team_id]
                team_name = fixture_key[1] if side == "home" else fixture_key[2]
                team_key = (open_match_id, team_name, category)
                player_name = wy_names.get(player_id, "")
                wy_counters[team_key][player_name] += 1
                wy_goal_event_counts[category] += 1
                wy_events_without_name[category] += not bool(player_name)

            if (roster_link_counts["actor_outside_same_match_team_roster"]
                    or roster_link_counts["actor_id_in_player_catalog"] != roster_link_counts["nonzero_actor_rows"]):
                raise ValueError(f"Wyscout actor/roster/catalog link check failed for {league}")
            roster_summaries.append({
                "league": league,
                "season": "2017-18",
                "matches": len(bridge),
                **{key: int(value) for key, value in roster_link_counts.items()},
                "actor_event_types_outside_roster": dict(unlinked_actor_types),
            })
            keeper_goal_tag_exact_score = 0
            keeper_goal_tag_above_score = 0
            keeper_goal_tag_below_score = 0
            for wyscout_match_id, (_, _, (fixture_key, open_score, _)) in bridge.items():
                score_goals = int(open_score[0]) + int(open_score[1])
                keeper_tags = wyscout_keeper_conceded_goals_by_match[wyscout_match_id]
                keeper_goal_tag_exact_score += keeper_tags == score_goals
                keeper_goal_tag_above_score += keeper_tags > score_goals
                keeper_goal_tag_below_score += keeper_tags < score_goals
                if keeper_tags != score_goals:
                    keeper_goal_tag_mismatches.append({
                        "league": league,
                        "date": fixture_key[0],
                        "home_team": fixture_key[1],
                        "away_team": fixture_key[2],
                        "home_score": int(open_score[0]),
                        "away_score": int(open_score[1]),
                        "scoreboard_goals": score_goals,
                        "tag_101_save_attempt_rows": int(keeper_tags),
                        "tag_minus_score": int(keeper_tags - score_goals),
                    })
            keeper_event_summaries.append({
                "league": league,
                "season": "2017-18",
                **{key: int(value) for key, value in wyscout_keeper_event_counts.items()},
                "save_attempt_goal_tag_matches_equal_score": int(keeper_goal_tag_exact_score),
                "save_attempt_goal_tag_matches_above_score": int(keeper_goal_tag_above_score),
                "save_attempt_goal_tag_matches_below_score": int(keeper_goal_tag_below_score),
            })

            shared_keeper_pairs = sum(
                len(names & open_keeper_stints.get(key, set()))
                for key, names in wyscout_keeper_actors.items()
            )
            shared_keeper_groups = sum(
                bool(names & open_keeper_stints.get(key, set()))
                for key, names in wyscout_keeper_actors.items()
            )
            keeper_summaries.append({
                "league": league,
                "season": "2017-18",
                "linked_fixtures": len(bridge),
                "openplay_played_gk_match_player_names": sum(map(len, open_keeper_stints.values())),
                "openplay_match_team_groups_with_gk": len(open_keeper_stints),
                "wyscout_profile_gk_actor_identities": sum(map(len, wyscout_keeper_actors.values())),
                "wyscout_match_team_groups_with_gk_actor": len(wyscout_keeper_actors),
                "exact_normalized_name_pairs_shared": int(shared_keeper_pairs),
                "match_team_groups_with_any_exact_keeper_name": int(shared_keeper_groups),
            })

            openplay_event_count_matches = 0
            wyscout_event_count_matches = 0
            both_event_count_matches = 0
            for wyscout_match_id, (open_match_id, _, (fixture_key, open_score, _)) in bridge.items():
                score_goals = int(open_score[0]) + int(open_score[1])
                openplay_event_count_matches += open_goal_counts_by_match[open_match_id] == score_goals
                wyscout_event_count_matches += wy_goal_counts_by_match[wyscout_match_id] == score_goals
                both_event_count_matches += (
                    open_goal_counts_by_match[open_match_id] == score_goals
                    and wy_goal_counts_by_match[wyscout_match_id] == score_goals
                )
            match_summary.update({
                "openplay_goal_event_count_matches_equal_score": int(openplay_event_count_matches),
                "wyscout_goal_event_count_matches_equal_score": int(wyscout_event_count_matches),
                "both_goal_event_counts_equal_score": int(both_event_count_matches),
            })

            for category in ("regular_goal", "own_goal"):
                exact_actor_occurrences = token_actor_occurrences = 0
                exact_group_matches = token_group_matches = groups = 0
                for key in set(open_counters) | set(wy_counters):
                    if key[2] != category:
                        continue
                    groups += 1
                    open_counter = open_counters.get(key, Counter())
                    wy_counter = wy_counters.get(key, Counter())
                    exact_actor_occurrences += sum((open_counter & wy_counter).values())
                    exact_group_matches += open_counter == wy_counter
                    aliases = unique_name_aliases(open_counter, wy_counter)
                    reverse_aliases = {right_name: left_name
                                       for left_name, right_name in aliases.items()}
                    normalized_wy = Counter()
                    for name, count in wy_counter.items():
                        normalized_wy[reverse_aliases.get(name, name)] += count
                    token_actor_occurrences += sum((open_counter & normalized_wy).values())
                    token_group_matches += open_counter == normalized_wy
                summaries.append({
                    "league": league,
                    "season": "2017-18",
                    "category": category,
                    "fixtures_linked": match_summary["linked_matches"],
                    "fixture_link_basis": "league + date + home/away clubs; score excluded",
                    "score_checks": match_summary["independent_score_checks"],
                    "score_mismatches": match_summary["score_mismatches"],
                    "openplay_goal_event_count_matches_equal_score": int(openplay_event_count_matches),
                    "wyscout_goal_event_count_matches_equal_score": int(wyscout_event_count_matches),
                    "both_goal_event_counts_equal_score": int(both_event_count_matches),
                    "openplay_goal_actor_events": int(open_goal_event_counts[category]),
                    "wyscout_goal_actor_events": int(wy_goal_event_counts[category]),
                    "openplay_events_without_name": int(open_events_without_name[category]),
                    "wyscout_events_without_name": int(wy_events_without_name[category]),
                    "exact_name_actor_occurrences_shared": int(exact_actor_occurrences),
                    "unique_name_variant_actor_occurrences_shared": int(token_actor_occurrences),
                    "match_team_groups": groups,
                    "exact_name_match_team_groups": int(exact_group_matches),
                    "unique_name_variant_match_team_groups": int(token_group_matches),
                })
                totals.update({
                    f"{category}_openplay_events": int(open_goal_event_counts[category]),
                    f"{category}_wyscout_events": int(wy_goal_event_counts[category]),
                    f"{category}_exact_actor_occurrences": int(exact_actor_occurrences),
                    f"{category}_name_variant_actor_occurrences": int(token_actor_occurrences),
                })
            totals.update({
                "fixtures_linked": match_summary["linked_matches"],
                "independent_score_checks": match_summary["independent_score_checks"],
                "independent_score_mismatches": match_summary["score_mismatches"],
                "openplay_goal_event_count_matches_equal_score": openplay_event_count_matches,
                "wyscout_goal_event_count_matches_equal_score": wyscout_event_count_matches,
                "both_goal_event_counts_equal_score": both_event_count_matches,
            })
            print(f"Audited {league}", flush=True)

    totals["keeper_goal_tag_score_mismatch_fixtures"] = len(keeper_goal_tag_mismatches)
    totals["keeper_goal_tag_rows_above_score"] = sum(
        max(0, row["tag_minus_score"]) for row in keeper_goal_tag_mismatches
    )
    totals["keeper_goal_tag_rows_below_score"] = sum(
        max(0, -row["tag_minus_score"]) for row in keeper_goal_tag_mismatches
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summaries).to_csv(OUTPUT / "aggregate.csv", index=False)
    pd.DataFrame(roster_summaries).to_csv(OUTPUT / "lineup_actor_links.csv", index=False)
    pd.DataFrame(keeper_summaries).to_csv(KEEPER_OUTPUT, index=False)
    pd.DataFrame(keeper_event_summaries).to_csv(KEEPER_EVENT_OUTPUT, index=False)
    pd.DataFrame(keeper_goal_tag_mismatches).sort_values(
        ["league", "date", "home_team", "away_team"]
    ).to_csv(OUTPUT / "keeper_goal_tag_score_mismatches.csv", index=False)
    result = {
        "audit": "cross-provider goal-event actor agreement",
        "scope": "Big Five domestic leagues, 2017-18",
        "fixture_link": "league + calendar date + home/away teams; score excluded",
        "sources": {
            "wyscout_manifest": "data/wyscout_research_manifest.json",
            "openplay_manifest": "data/openplay_source_manifest.json",
            "verified_input_files": len(pins),
            "input_sha256": dict(sorted(pins.items())),
        },
        "totals": dict(totals),
        "wyscout_actor_roster_summary": roster_summaries,
        "goalkeeper_profile_actor_overlap": keeper_summaries,
        "wyscout_keeper_event_integrity": keeper_event_summaries,
        "wyscout_keeper_goal_tag_score_mismatches": keeper_goal_tag_mismatches,
        "caveats": [
            "Name concordance is a bounded corroboration signal, not proof of player-ID correctness.",
            "One-to-one name variants are a sensitivity view, not approved identity links; no links are exported.",
            "Goal-event agreement does not validate pass, defensive, keeper, or other actor attribution.",
            "Keeper name overlap is a screening comparison of Wyscout profile-role GK actors with OpenPlay GK lineup stints, not a validated keeper identity crosswalk or shot-to-keeper assignment.",
            "Wyscout Save attempt tag 101 exceeds the linked scoreboard by one in three fixtures; do not treat the keeper goal-conceded tag as a score-perfect target.",
            "Provider coverage is limited to 2017-18 and cannot validate later seasons.",
        ],
    }
    (OUTPUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
