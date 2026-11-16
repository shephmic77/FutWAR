"""Audit independent Wyscout/OpenPlay shot-event alignment for 2017-18.

Pairs shots by fixture, team, half, and nearest event time only. Player names
are withheld from the event-pairing rule and compared afterward. The audit is
aggregate-only: it does not approve identity links or validate every actor.
"""
from __future__ import annotations

import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

import audit_cross_provider_goal_scorer_agreement as source_audit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "cross_provider_shot_actor_alignment"
MAX_TIME_GAP_SECONDS = 5.0
WYSCOUT_PERIOD = {"1H": "FirstHalf", "2H": "SecondHalf"}


def safe_normalize(value: object) -> str:
    """Normalize a provider name without truth-testing pandas.NA."""
    if pd.isna(value):
        return ""
    return source_audit.normalize(value)


def openplay_elapsed_seconds(period: str, minute: object, second: object) -> float:
    """Convert OpenPlay's match clock to elapsed seconds within the half."""
    value = float(minute) * 60.0 + float(second)
    if period == "SecondHalf":
        value -= 45.0 * 60.0
    return value


def mutual_unique_nearest_pairs(
    wyscout: list[tuple[float, str]],
    openplay: list[tuple[float, str]],
) -> tuple[list[tuple[int, int]], int]:
    """Pair only mutually unique nearest shots within the fixed time window."""
    nearest_w: dict[int, int] = {}
    nearest_o: dict[int, int] = {}
    ambiguous = 0
    for i, (w_time, _) in enumerate(wyscout):
        gaps = [abs(w_time - o_time) for o_time, _ in openplay]
        if not gaps:
            continue
        gap = min(gaps)
        if gap <= MAX_TIME_GAP_SECONDS:
            if gaps.count(gap) == 1:
                nearest_w[i] = gaps.index(gap)
            else:
                ambiguous += 1
    for j, (o_time, _) in enumerate(openplay):
        gaps = [abs(o_time - w_time) for w_time, _ in wyscout]
        if not gaps:
            continue
        gap = min(gaps)
        if gap <= MAX_TIME_GAP_SECONDS:
            if gaps.count(gap) == 1:
                nearest_o[j] = gaps.index(gap)
            else:
                ambiguous += 1
    pairs = [(i, j) for i, j in nearest_w.items() if nearest_o.get(j) == i]
    return pairs, ambiguous


def main() -> None:
    pins = source_audit.verify_sources()
    aliases = {}
    for filename in ("club_aliases.json", "identity_club_aliases.json",
                     "wikipedia_club_aliases.json"):
        path = ROOT / "data" / filename
        aliases[filename] = source_audit.sha256(path)

    players = json.loads((source_audit.WYSCOUT_DIR / "players.json").read_text(encoding="utf-8"))
    player_names = {
        int(player["wyId"]): safe_normalize(
            str(player.get("firstName", "")) + " " + str(player.get("lastName", ""))
        ) for player in players
    }
    rows: list[dict[str, object]] = []

    with zipfile.ZipFile(source_audit.WYSCOUT_DIR / "matches.zip") as matches_zip, \
            zipfile.ZipFile(source_audit.WYSCOUT_DIR / "events.zip") as events_zip:
        for country, (code, league, _) in source_audit.LEAGUES.items():
            bridge, match_summary, _ = source_audit.exact_fixture_bridge(
                source_audit.WYSCOUT_COUNTRY[country], code, league, matches_zip
            )
            canonical = source_audit.canonicalizer(league)

            match_rows = pd.read_parquet(
                source_audit.OPENPLAY_DIR / "matches.parquet",
                columns=["match_id", "comp", "season", "home_team", "away_team"],
            )
            match_rows = match_rows[(match_rows["comp"] == code) &
                                    (match_rows["season"] == "1718")]
            open_teams = {
                int(row.match_id): {"home": canonical(row.home_team),
                                    "away": canonical(row.away_team)}
                for row in match_rows.itertuples(index=False)
            }

            open_events = pd.read_parquet(
                source_audit.OPENPLAY_DIR / f"events_{code}_1718.parquet",
                columns=["match_id", "period", "minute", "second", "team", "player", "is_shot"],
            )
            open_events = open_events[open_events["is_shot"].fillna(False)]
            open_shots: dict[tuple[int, str, str], list[tuple[float, str]]] = defaultdict(list)
            for event in open_events.itertuples(index=False):
                match_id = int(event.match_id)
                team = canonical(event.team)
                side = next((side for side, name in open_teams[match_id].items()
                             if name == team), None)
                period = str(event.period)
                if side and period in {"FirstHalf", "SecondHalf"}:
                    open_shots[(match_id, side, period)].append((
                        openplay_elapsed_seconds(period, event.minute, event.second),
                        safe_normalize(event.player),
                    ))

            wy_shots: dict[tuple[int, str, str], list[tuple[float, str]]] = defaultdict(list)
            event_rows = json.load(events_zip.open(
                f"events_{source_audit.WYSCOUT_COUNTRY[country]}.json"
            ))
            for event in event_rows:
                if event.get("eventName") != "Shot":
                    continue
                match_id = int(event.get("matchId") or 0)
                linked = bridge.get(match_id)
                if linked is None:
                    continue
                open_match_id, sides, _ = linked
                side = sides.get(int(event.get("teamId") or 0))
                period = WYSCOUT_PERIOD.get(event.get("matchPeriod"))
                if not side or not period:
                    continue
                wy_shots[(open_match_id, side, period)].append((
                    float(event.get("eventSec") or 0.0),
                    player_names.get(int(event.get("playerId") or 0), ""),
                ))

            league_counts = Counter()
            exact_names = 0
            comparable_names = 0
            constrained_variants = 0
            time_gaps: list[float] = []
            paired_names: dict[tuple[int, str], list[tuple[str, str]]] = defaultdict(list)
            for key, wy_group in wy_shots.items():
                open_group = open_shots.get(key, [])
                league_counts["wyscout_shots"] += len(wy_group)
                league_counts["openplay_shots"] += len(open_group)
                pairs, ambiguous = mutual_unique_nearest_pairs(wy_group, open_group)
                league_counts["mutually_unique_pairs"] += len(pairs)
                league_counts["ambiguous_nearest_cases"] += ambiguous
                for wy_index, open_index in pairs:
                    wy_time, wy_name = wy_group[wy_index]
                    open_time, open_name = open_group[open_index]
                    time_gaps.append(abs(wy_time - open_time))
                    paired_names[(key[0], key[1])].append((wy_name, open_name))
                    if wy_name and open_name:
                        comparable_names += 1
                        exact_names += wy_name == open_name

            # Apply the existing conservative, one-to-one token-variant rule
            # within each match/team only as a separate sensitivity measure.
            for pairs in paired_names.values():
                left = Counter(wy for wy, op in pairs if wy and op and wy != op)
                right = Counter(op for wy, op in pairs if wy and op and wy != op)
                mapping = source_audit.unique_name_aliases(left, right)
                constrained_variants += sum(mapping.get(wy) == op for wy, op in pairs
                                            if wy and op and wy != op)

            denominator = min(league_counts["wyscout_shots"], league_counts["openplay_shots"])
            rows.append({
                "league": league,
                "linked_fixtures": match_summary["linked_matches"],
                "wyscout_shot_events": league_counts["wyscout_shots"],
                "openplay_shot_events": league_counts["openplay_shots"],
                "mutually_unique_time_pairs": league_counts["mutually_unique_pairs"],
                "pair_share_of_smaller_total": (league_counts["mutually_unique_pairs"] / denominator
                                                  if denominator else None),
                "paired_with_both_names": comparable_names,
                "exact_normalized_actor_names": exact_names,
                "exact_name_share": (exact_names / comparable_names if comparable_names else None),
                "constrained_name_variant_sensitivity": constrained_variants,
                "median_time_gap_seconds": (float(pd.Series(time_gaps).median()) if time_gaps else None),
                "ambiguous_nearest_cases": league_counts["ambiguous_nearest_cases"],
            })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUTPUT / "league_summary.csv", index=False)
    summary = {
        "scope": "Big Five, 2017-18; aggregate event alignment only",
        "max_time_gap_seconds": MAX_TIME_GAP_SECONDS,
        "pair_rule": "same bridged fixture, team side, half; mutual unique nearest event time",
        "actor_names_used_for_pairing": False,
        "raw_source_hashes": pins,
        "alias_map_hashes": aliases,
        "league_results": rows,
        "limitations": [
            "Time/team pairing identifies corresponding shot-event candidates, not actor correctness.",
            "Provider clock precision and event definitions can create missed or false pairs.",
            "Exact actor-name agreement is not a gold-standard identity adjudication.",
            "The constrained name-variant count is a sensitivity analysis, not an approved identity map.",
            "Only 2017-18 is available in both event sources; this does not validate other seasons or action families.",
        ],
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "league_count": len(rows),
        "linked_fixtures": sum(int(row["linked_fixtures"]) for row in rows),
        "shot_pairs": sum(int(row["mutually_unique_time_pairs"]) for row in rows),
        "pair_coverage_weighted": sum(int(row["mutually_unique_time_pairs"]) for row in rows) /
            sum(min(int(row["wyscout_shot_events"]), int(row["openplay_shot_events"])) for row in rows),
        "output": str(OUTPUT.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
