"""Check Wyscout shot-actor names against separate OpenPlay match lineups.

Names are linked only within the bridged fixture/team. Event time is checked
against the OpenPlay lineup interval with a conservative four-minute tolerance.
Aggregate outputs are not actor-accuracy estimates or player-value validation.
"""
from __future__ import annotations

import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

import audit_cross_provider_goal_scorer_agreement as source_audit

ROOT = Path(__file__).resolve().parents[1]
OPENPLAY_DIR = ROOT / "data/raw/openplay/data-v0.1.0"
WYSCOUT_DIR = ROOT / "data/raw/wyscout_research/2026-10-10"
OUTPUT = ROOT / "reports/cross_provider_shot_lineup_presence"
FOUR_MINUTES_SECONDS = 4 * 60


def safe_normalize(value: object) -> str:
    if pd.isna(value):
        return ""
    return source_audit.normalize(value)


def main() -> None:
    source_hashes = source_audit.verify_sources()
    open_manifest = json.loads(
        (ROOT / "data/openplay_source_manifest.json").read_text(encoding="utf-8")
    )
    lineup_entry = next((entry for entry in open_manifest["files"]
                         if Path(entry["path"]).name == "lineups.parquet"), None)
    if lineup_entry is None:
        raise ValueError("OpenPlay lineup archive missing from the pinned manifest")
    lineup_path = ROOT / lineup_entry["path"]
    if lineup_path.stat().st_size != lineup_entry["bytes"] or \
            source_audit.sha256(lineup_path) != lineup_entry["sha256"]:
        raise ValueError("Pinned OpenPlay lineup archive changed")
    source_hashes[lineup_entry["path"]] = lineup_entry["sha256"]

    player_rows = json.loads((WYSCOUT_DIR / "players.json").read_text(encoding="utf-8"))
    wyscout_names = {
        int(row["wyId"]): safe_normalize(
            str(row.get("firstName", "")) + " " + str(row.get("lastName", ""))
        ) for row in player_rows
    }
    lineups = pd.read_parquet(
        lineup_path,
        columns=["match_id", "comp", "season", "side", "player", "played",
                 "minute_on", "minute_off"],
    )
    lineups = lineups[(lineups["season"] == "1718") & lineups["played"].fillna(False)].copy()
    lineups["normalized_name"] = lineups["player"].map(safe_normalize)
    lineups = lineups[lineups["normalized_name"].ne("")]
    lineup_groups = {
        (int(match_id), str(side)): group
        for (match_id, side), group in lineups.groupby(["match_id", "side"])
    }
    match_rows = pd.read_parquet(
        lineup_path.parent / "matches.parquet",
        columns=["match_id", "competition", "date", "home_team", "away_team"],
    )
    match_info = {
        int(row.match_id): row._asdict()
        for row in match_rows[match_rows["competition"].isin(
            {league for _, league, _ in source_audit.LEAGUES.values()}
        )]
        .itertuples(index=False)
    }
    wyscout_display_names = {
        int(row["wyId"]): " ".join(
            part for part in (str(row.get("firstName", "")).strip(),
                              str(row.get("lastName", "")).strip()) if part
        ) for row in player_rows
    }

    league_results: list[dict[str, object]] = []
    outside_candidates: list[dict[str, object]] = []
    with zipfile.ZipFile(WYSCOUT_DIR / "matches.zip") as matches_zip, \
            zipfile.ZipFile(WYSCOUT_DIR / "events.zip") as events_zip:
        for country, (code, league, _) in source_audit.LEAGUES.items():
            bridge, match_summary, _ = source_audit.exact_fixture_bridge(
                source_audit.WYSCOUT_COUNTRY[country], code, league, matches_zip
            )
            groups: dict[tuple[int, str], list[tuple[dict, str]]] = defaultdict(list)
            event_file = f"events_{source_audit.WYSCOUT_COUNTRY[country]}.json"
            for event in json.load(events_zip.open(event_file)):
                if event.get("eventName") != "Shot":
                    continue
                wyscout_match_id = int(event.get("matchId") or 0)
                linked = bridge.get(wyscout_match_id)
                if linked is None:
                    continue
                openplay_match_id, side_by_team, _ = linked
                team_id = int(event.get("teamId") or 0)
                side = side_by_team.get(team_id)
                if side not in {"home", "away"}:
                    continue
                player_id = int(event.get("playerId") or 0)
                groups[(openplay_match_id, side)].append(
                    (event, wyscout_names.get(player_id, ""))
                )

            league_counts = Counter()
            for (match_id, side), shots in groups.items():
                lineup_group = lineup_groups.get((match_id, side))
                league_counts["shot_events"] += len(shots)
                if lineup_group is None:
                    league_counts["missing_lineup_group"] += len(shots)
                    continue
                lineup_names = Counter(lineup_group["normalized_name"])
                actor_names = Counter(name for _, name in shots if name)
                variant_map = source_audit.unique_name_aliases(actor_names, lineup_names)
                rows_by_name: dict[str, list] = defaultdict(list)
                for row in lineup_group.itertuples(index=False):
                    rows_by_name[row.normalized_name].append(row)

                for event, actor_name in shots:
                    if not actor_name:
                        league_counts["missing_actor_name"] += 1
                        continue
                    if actor_name in rows_by_name:
                        lineup_name = actor_name
                        if len(rows_by_name[lineup_name]) != 1:
                            league_counts["ambiguous_exact_lineup_name"] += 1
                            continue
                        method = "exact"
                    elif actor_name in variant_map:
                        lineup_name = variant_map[actor_name]
                        if len(rows_by_name.get(lineup_name, [])) != 1:
                            league_counts["ambiguous_variant_lineup_name"] += 1
                            continue
                        method = "variant"
                    else:
                        league_counts["unmatched_lineup_name"] += 1
                        continue

                    league_counts[f"{method}_lineup_name"] += 1
                    row = rows_by_name[lineup_name][0]
                    if pd.isna(row.minute_on) or pd.isna(row.minute_off):
                        league_counts["matched_name_interval_missing"] += 1
                        continue

                    period = event.get("matchPeriod")
                    if period not in {"1H", "2H"}:
                        league_counts["unsupported_period"] += 1
                        continue
                    elapsed = float(event.get("eventSec") or 0.0)
                    match_clock = elapsed + (45 * 60 if period == "2H" else 0)
                    interval_start = float(row.minute_on) * 60.0
                    interval_end = float(row.minute_off) * 60.0
                    if interval_start <= match_clock < interval_end:
                        league_counts[f"{method}_within_recorded_stint"] += 1
                    elif interval_start - FOUR_MINUTES_SECONDS <= match_clock < \
                            interval_end + FOUR_MINUTES_SECONDS:
                        league_counts[f"{method}_within_four_minute_tolerance"] += 1
                    else:
                        league_counts[f"{method}_clearly_outside_stint"] += 1
                        match = match_info.get(match_id, {})
                        outside_candidates.append({
                            "league": league,
                            "openplay_match_id": match_id,
                            "match_date": str(match.get("date", ""))[:10],
                            "home_team": match.get("home_team", ""),
                            "away_team": match.get("away_team", ""),
                            "team_side": side,
                            "wyscout_match_id": int(event.get("matchId") or 0),
                            "wyscout_event_id": event.get("id"),
                            "period": period,
                            "event_seconds_in_period": elapsed,
                            "approx_match_minute": match_clock / 60.0,
                            "actor_name": wyscout_display_names.get(
                                int(event.get("playerId") or 0), actor_name
                            ),
                            "openplay_lineup_name": row.player,
                            "name_match_method": method,
                            "lineup_minute_on": row.minute_on,
                            "lineup_minute_off": row.minute_off,
                        })

            mapped = league_counts["exact_lineup_name"] + league_counts["variant_lineup_name"]
            league_results.append({
                "league": league,
                "linked_fixtures": match_summary["linked_matches"],
                "wyscout_shot_events": league_counts["shot_events"],
                "exact_actor_lineup_name": league_counts["exact_lineup_name"],
                "unique_variant_actor_lineup_name": league_counts["variant_lineup_name"],
                "mapped_name_share": mapped / league_counts["shot_events"]
                    if league_counts["shot_events"] else None,
                "exact_name_within_recorded_stint": league_counts["exact_within_recorded_stint"],
                "variant_name_within_recorded_stint": league_counts["variant_within_recorded_stint"],
                "mapped_name_near_interval_boundary": (
                    league_counts["exact_within_four_minute_tolerance"] +
                    league_counts["variant_within_four_minute_tolerance"]
                ),
                "clearly_outside_recorded_stint_after_tolerance": (
                    league_counts["exact_clearly_outside_stint"] +
                    league_counts["variant_clearly_outside_stint"]
                ),
                "unmatched_or_unresolved_name": (
                    league_counts["unmatched_lineup_name"] +
                    league_counts["missing_actor_name"] +
                    league_counts["ambiguous_exact_lineup_name"] +
                    league_counts["ambiguous_variant_lineup_name"]
                ),
                "lineup_interval_missing": league_counts["matched_name_interval_missing"],
            })

    OUTPUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(league_results).to_csv(OUTPUT / "league_summary.csv", index=False)
    pd.DataFrame(outside_candidates).to_csv(
        OUTPUT / "outside_stint_review_candidates.csv", index=False
    )
    totals = Counter()
    for row in league_results:
        for key, value in row.items():
            if key != "league" and isinstance(value, (int, float)):
                totals[key] += value
    totals["mapped_name_share"] = (
        (totals["exact_actor_lineup_name"] + totals["unique_variant_actor_lineup_name"])
        / totals["wyscout_shot_events"]
        if totals["wyscout_shot_events"] else 0.0
    )
    summary = {
        "scope": "Big Five 2017-18; Wyscout shot actors compared with OpenPlay match lineups",
        "name_variant_rule": "existing one-to-one unique token rule within fixture and team",
        "time_tolerance_seconds": FOUR_MINUTES_SECONDS,
        "time_tolerance_basis": "allows for observed 1-4 minute cross-source substitution timing differences in a separate review sample",
        "source_hashes": source_hashes,
        "league_results": league_results,
        "aggregate_counts": dict(totals),
        "limitations": [
            "A player being listed and plausibly on the pitch means they could have taken the shot; it does not prove they did.",
            "An event outside a recorded lineup interval is a timing-conflict flag, not proof of an incorrect shot actor; independently reviewed cases show the lineup entry minute can be late.",
            "The OpenPlay lineup interval is a separate provider table, but its source lineage is not fully independent of the event release.",
            "Name variants remain candidate links and the four-minute interval tolerance can hide short substitution-time conflicts.",
            "Only shots in the one season shared with Wyscout are checked; this does not validate other event families or seasons.",
            "This audit neither approves player IDs nor validates player scores or WAR.",
        ],
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "linked_fixtures": sum(row["linked_fixtures"] for row in league_results),
        "shot_events": sum(row["wyscout_shot_events"] for row in league_results),
        "mapped_names": sum(row["exact_actor_lineup_name"] +
                             row["unique_variant_actor_lineup_name"] for row in league_results),
        "clearly_outside_stint_after_four_minute_tolerance": sum(
            row["clearly_outside_recorded_stint_after_tolerance"] for row in league_results
        ),
        "output": str(OUTPUT.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
