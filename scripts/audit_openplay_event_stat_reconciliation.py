"""Reconcile selected OpenPlay event actor counts to player-match stats.

This is an internal same-release consistency check, not an independent audit
of who performed each action. Outputs contain aggregate counts only.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/openplay/data-v0.1.0"
MANIFEST = ROOT / "data/openplay_source_manifest.json"
OUTPUT = ROOT / "reports/openplay_event_stat_reconciliation"
COMPS = {"eng", "esp", "ita", "ger", "fra"}
SEASONS = {"1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425"}
KEYS = ["match_id", "team_id", "player_id"]
FAMILIES = {
    "Pass": ("type", "Pass", "passes"),
    "Shot": ("is_shot", True, "shots"),
    "Tackle": ("type", "Tackle", "tackles"),
    "Interception": ("type", "Interception", "interceptions"),
    "Clearance": ("type", "Clearance", "clearances"),
    "Aerial": ("type", "Aerial", "aerials"),
    "BallRecovery": ("type", "BallRecovery", "ball_recoveries"),
    "Dispossessed": ("type", "Dispossessed", "dispossessed"),
    "TakeOn": ("type", "TakeOn", "dribbles"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs() -> dict[str, str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_names = {"player_match_stats.parquet"} | {
        f"events_{comp}_{season}.parquet" for comp in COMPS for season in SEASONS
    }
    entries = {Path(row["path"]).name: row for row in manifest["files"]
               if Path(row["path"]).name in expected_names}
    if set(entries) != expected_names:
        raise ValueError(f"Input manifest incomplete: {sorted(expected_names - set(entries))}")
    fingerprints = {}
    for name, entry in entries.items():
        path = ROOT / entry["path"]
        if path.stat().st_size != entry["bytes"] or sha256(path) != entry["sha256"]:
            raise ValueError(f"Pinned input changed: {entry['path']}")
        fingerprints[entry["path"]] = entry["sha256"]
    return fingerprints


def event_mask(events: pd.DataFrame, selector: tuple[str, object, str]) -> pd.Series:
    column, value, _ = selector
    if column == "is_shot":
        return events[column].fillna(False).eq(value)
    return events[column].eq(value)


def main() -> None:
    fingerprints = verify_inputs()
    stat_fields = sorted({selector[2] for selector in FAMILIES.values()})
    stats = pd.read_parquet(
        RAW / "player_match_stats.parquet",
        columns=["match_id", "comp", "season", "team_id", "player_id",
                 "played", "minutes_played", *stat_fields],
    )
    stats = stats[stats["comp"].isin(COMPS) &
                  stats["season"].astype(str).isin(SEASONS)].copy()
    duplicate_stats = int(stats.duplicated(KEYS).sum())
    if duplicate_stats:
        raise ValueError(f"Duplicate player-match-stat keys in scope: {duplicate_stats}")

    by_cell: list[dict[str, object]] = []
    all_event_rows = 0
    for comp in sorted(COMPS):
        for season in sorted(SEASONS):
            path = RAW / f"events_{comp}_{season}.parquet"
            events = pd.read_parquet(
                path,
                columns=["match_id", "team_id", "player_id", "type", "is_shot"],
            )
            all_event_rows += len(events)
            cell_stats = stats[(stats["comp"] == comp) &
                               (stats["season"].astype(str) == season)]

            for family, selector in FAMILIES.items():
                selected = events[event_mask(events, selector)]
                has_actor = selected["player_id"].notna() & selected["player_id"].gt(0)
                actor_events = selected.loc[has_actor]
                event_counts = actor_events.groupby(KEYS, dropna=False).size().rename(
                    "event_count"
                ).reset_index()
                stat_field = selector[2]
                stat_counts = cell_stats[KEYS + ["played", "minutes_played", stat_field]].rename(
                    columns={stat_field: "stat_count"}
                )
                joined = stat_counts.merge(event_counts, on=KEYS, how="outer",
                                           indicator=True, validate="one_to_one")
                has_event = joined["event_count"].fillna(0).gt(0)
                has_stat_row = joined["_merge"].ne("right_only")
                positive_minutes = (joined["played"].fillna(False) &
                                    joined["minutes_played"].fillna(0).gt(0))
                eligible = has_event & has_stat_row & positive_minutes
                exact = joined["event_count"].fillna(0).eq(joined["stat_count"].fillna(0))
                stats_only = joined["event_count"].fillna(0).eq(0) & \
                    joined["stat_count"].fillna(0).gt(0)

                by_cell.append({
                    "competition": comp,
                    "season": season,
                    "action_family": family,
                    "event_rows": int(len(selected)),
                    "event_rows_with_actor_id": int(has_actor.sum()),
                    "event_rows_without_actor_id": int((~has_actor).sum()),
                    "event_actor_keys": int(len(event_counts)),
                    "event_keys_with_stats_row": int((has_event & has_stat_row).sum()),
                    "event_keys_with_positive_minutes": int(eligible.sum()),
                    "exact_count_matches_positive_minutes": int((eligible & exact).sum()),
                    "mismatched_count_positive_minutes": int((eligible & ~exact).sum()),
                    "event_keys_without_stats_row": int((has_event & ~has_stat_row).sum()),
                    "event_keys_without_positive_minutes": int((has_event & has_stat_row &
                                                                  ~positive_minutes).sum()),
                    "positive_stat_keys_without_event": int(stats_only.sum()),
                })

    detail = pd.DataFrame(by_cell)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    detail.to_csv(OUTPUT / "by_cell_action_family.csv", index=False)
    metric_cols = [column for column in detail.columns
                   if column not in {"competition", "season", "action_family"}]
    totals = detail.groupby("action_family", as_index=False)[metric_cols].sum()
    totals["exact_count_match_share_positive_minutes"] = (
        totals["exact_count_matches_positive_minutes"] /
        totals["event_keys_with_positive_minutes"].replace(0, pd.NA)
    )
    totals.to_csv(OUTPUT / "overall_action_family.csv", index=False)
    summary = {
        "scope": "Big Five, 2017-18 through 2024-25; 40 league-season cells",
        "raw_event_rows_scanned": all_event_rows,
        "player_match_stats_duplicate_keys": duplicate_stats,
        "source_hashes": fingerprints,
        "same_release_consistency_only": True,
        "action_families": totals.to_dict(orient="records"),
        "limitations": [
            "Events and player-match statistics belong to the same OpenPlay release and are not independent validation.",
            "Exact count agreement does not prove the event actor ID names the correct real-world player.",
            "Only nine countable action families are checked; this is not coverage of every WAR input.",
            "Event keys without stats, non-positive exposure, actorless rows, and positive stats without events remain visible.",
            "This audit does not estimate player impact, select weights, or produce WAR.",
        ],
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "cells": int(detail[["competition", "season"]].drop_duplicates().shape[0]),
        "action_families": len(FAMILIES),
        "positive_minute_player_action_keys": int(totals["event_keys_with_positive_minutes"].sum()),
        "exact_count_matches": int(totals["exact_count_matches_positive_minutes"].sum()),
        "positive_minute_mismatches": int(totals["mismatched_count_positive_minutes"].sum()),
        "event_keys_without_stats_row": int(totals["event_keys_without_stats_row"].sum()),
        "event_keys_without_positive_minutes": int(totals["event_keys_without_positive_minutes"].sum()),
        "positive_stat_keys_without_event": int(totals["positive_stat_keys_without_event"].sum()),
        "output": str(OUTPUT.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
