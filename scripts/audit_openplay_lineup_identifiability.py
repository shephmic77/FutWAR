"""Measure how often same-team player-minute histories are hard to separate.

This is a design-matrix diagnostic for the match-level lineup-impact route.
It reports aggregate teammate-pair overlap only; it does not estimate player
effects, validate identity links, or calculate WAR.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/openplay/data-v0.1.0"
OUT = ROOT / "reports/war_prototype/lineup_identifiability"
COMPS = {"eng", "esp", "ger", "ita", "fra"}
SEASONS = {"1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425"}
MINUTES = (300, 600, 900)


def load_valid_lineups() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    matches = pd.read_parquet(
        RAW / "matches.parquet",
        columns=[
            "match_id", "comp", "season", "home_team_id", "away_team_id",
            "home_score_90", "away_score_90", "score_matches_events", "in_v1_scope",
        ],
    )
    matches = matches[
        matches.comp.isin(COMPS)
        & matches.season.astype(str).isin(SEASONS)
        & matches.score_matches_events.fillna(False)
        & matches.in_v1_scope.fillna(False)
    ].dropna(subset=["home_team_id", "away_team_id", "home_score_90", "away_score_90"]).copy()
    matches["season"] = matches.season.astype(str)
    matches["home_team_id"] = matches.home_team_id.astype("int64")
    matches["away_team_id"] = matches.away_team_id.astype("int64")

    lineups = pd.read_parquet(
        RAW / "lineups.parquet",
        columns=[
            "match_id", "comp", "season", "team_id", "player_id", "is_starter",
            "played", "minutes_played",
        ],
    )
    lineups = lineups[
        lineups.comp.isin(COMPS) & lineups.season.astype(str).isin(SEASONS)
    ].copy()
    lineups["season"] = lineups.season.astype(str)
    lineups["minutes_played"] = pd.to_numeric(lineups.minutes_played, errors="coerce")
    lineups["team_id"] = pd.to_numeric(lineups.team_id, errors="coerce")
    lineups["player_id"] = pd.to_numeric(lineups.player_id, errors="coerce")

    match_teams = {
        int(row.match_id): {int(row.home_team_id), int(row.away_team_id)}
        for row in matches.itertuples(index=False)
    }
    valid_ids: set[int] = set()
    audit = {
        "score_reconciled_matches_in_scope": len(matches),
        "lineup_duplicate_player_team_matches": 0,
        "lineup_implausible_minute_matches": 0,
        "lineup_wrong_team_count_matches": 0,
        "lineup_starting_xi_not_11_matches": 0,
        "valid_matches": 0,
    }
    for match_id, group in lineups[lineups.match_id.isin(match_teams)].groupby("match_id", sort=False):
        if group.duplicated(["team_id", "player_id"]).any():
            audit["lineup_duplicate_player_team_matches"] += 1
            continue
        values = group.minutes_played.dropna()
        if values.lt(0).any() or values.gt(140).any():
            audit["lineup_implausible_minute_matches"] += 1
            continue
        teams = set(group.team_id.dropna().astype("int64"))
        if len(teams) != 2 or teams != match_teams[int(match_id)]:
            audit["lineup_wrong_team_count_matches"] += 1
            continue
        starters_ok = True
        for team_id in teams:
            starters = group[
                group.team_id.eq(team_id) & group.is_starter.fillna(False)
            ].player_id.dropna().astype("int64")
            if starters.nunique() != 11:
                starters_ok = False
                break
        if not starters_ok:
            audit["lineup_starting_xi_not_11_matches"] += 1
            continue
        valid_ids.add(int(match_id))
    audit["valid_matches"] = len(valid_ids)
    matches = matches[matches.match_id.isin(valid_ids)].copy()
    lineups = lineups[lineups.match_id.isin(valid_ids)].copy()
    return matches, lineups, audit


def summarize() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    matches, lineups, quality = load_valid_lineups()
    fixture_ids: dict[tuple[str, str, int], list[int]] = {}
    for row in matches.itertuples(index=False):
        for team_id in (int(row.home_team_id), int(row.away_team_id)):
            fixture_ids.setdefault((str(row.comp), str(row.season), team_id), []).append(int(row.match_id))

    played = lineups[
        lineups.player_id.notna()
        & lineups.team_id.notna()
        & lineups.minutes_played.gt(0)
        & lineups.played.fillna(False)
        & lineups.player_id.ne(0)
    ].copy()
    played["player_id"] = played.player_id.astype("int64")
    played["team_id"] = played.team_id.astype("int64")
    group_rows: list[dict[str, object]] = []

    for (comp, season, team_id), group in played.groupby(["comp", "season", "team_id"], sort=False):
        match_ids = sorted(fixture_ids[(str(comp), str(season), int(team_id))])
        player_ids = sorted(group.player_id.unique().astype(int))
        if len(match_ids) < 5 or not player_ids:
            continue
        player_idx = {player_id: i for i, player_id in enumerate(player_ids)}
        match_idx = {match_id: j for j, match_id in enumerate(match_ids)}
        matrix = np.zeros((len(player_ids), len(match_ids)), dtype=np.float32)
        for row in group.itertuples(index=False):
            matrix[player_idx[int(row.player_id)], match_idx[int(row.match_id)]] = float(row.minutes_played)
        season_minutes = matrix.sum(axis=1)

        for cutoff in MINUTES:
            keep = np.flatnonzero(season_minutes >= cutoff)
            n_players = len(keep)
            ii, jj = np.triu_indices(n_players, k=1)
            pair_count = len(ii)
            if pair_count:
                presence = matrix[keep] > 0
                both = np.logical_and(presence[ii], presence[jj]).sum(axis=1)
                either = np.logical_or(presence[ii], presence[jj]).sum(axis=1)
                jaccard = np.divide(both, either, out=np.zeros_like(both, dtype=float), where=either > 0)
                same_presence = np.all(presence[ii] == presence[jj], axis=1)
                same_minutes = np.all(matrix[keep][ii] == matrix[keep][jj], axis=1)
                high_overlap = jaccard >= 0.95
                high_overlap_pairs = int(high_overlap.sum())
                same_presence_pairs = int(same_presence.sum())
                same_minutes_pairs = int(same_minutes.sum())
                median_jaccard = float(np.median(jaccard))
                p90_jaccard = float(np.quantile(jaccard, 0.90))
            else:
                high_overlap_pairs = same_presence_pairs = same_minutes_pairs = 0
                median_jaccard = p90_jaccard = float("nan")
            group_rows.append({
                "league": str(comp),
                "season": str(season),
                "team_season": int(team_id),
                "team_matches": len(match_ids),
                "minutes_cutoff": cutoff,
                "eligible_players": n_players,
                "eligible_pairs": pair_count,
                "jaccard_ge_0_95_pairs": high_overlap_pairs,
                "identical_presence_pairs": same_presence_pairs,
                "identical_minute_history_pairs": same_minutes_pairs,
                "median_pair_jaccard": median_jaccard,
                "p90_pair_jaccard": p90_jaccard,
            })

    by_team = pd.DataFrame(group_rows)
    summaries = []
    for cutoff, rows in by_team.groupby("minutes_cutoff", sort=True):
        pairs = int(rows.eligible_pairs.sum())
        summaries.append({
            "minutes_cutoff": int(cutoff),
            "team_seasons": int(len(rows)),
            "player_team_seasons": int(rows.eligible_players.sum()),
            "player_pairs": pairs,
            "jaccard_ge_0_95_pairs": int(rows.jaccard_ge_0_95_pairs.sum()),
            "jaccard_ge_0_95_share": float(rows.jaccard_ge_0_95_pairs.sum() / pairs) if pairs else None,
            "identical_presence_pairs": int(rows.identical_presence_pairs.sum()),
            "identical_presence_share": float(rows.identical_presence_pairs.sum() / pairs) if pairs else None,
            "identical_minute_history_pairs": int(rows.identical_minute_history_pairs.sum()),
            "identical_minute_history_share": float(rows.identical_minute_history_pairs.sum() / pairs) if pairs else None,
            "pair_weighted_mean_of_team_median_jaccard": float(np.average(rows.median_pair_jaccard.dropna(), weights=rows.loc[rows.median_pair_jaccard.notna(), "eligible_pairs"])) if rows.median_pair_jaccard.notna().any() else None,
        })
    summary = pd.DataFrame(summaries)
    league_rows = []
    for (league, season, cutoff), rows in by_team.groupby(["league", "season", "minutes_cutoff"], sort=True):
        pairs = int(rows.eligible_pairs.sum())
        valid_medians = rows.median_pair_jaccard.notna()
        league_rows.append({
            "league": league,
            "season": season,
            "minutes_cutoff": int(cutoff),
            "team_seasons": int(len(rows)),
            "player_team_seasons": int(rows.eligible_players.sum()),
            "player_pairs": pairs,
            "jaccard_ge_0_95_pairs": int(rows.jaccard_ge_0_95_pairs.sum()),
            "jaccard_ge_0_95_share": float(rows.jaccard_ge_0_95_pairs.sum() / pairs) if pairs else None,
            "identical_presence_pairs": int(rows.identical_presence_pairs.sum()),
            "identical_presence_share": float(rows.identical_presence_pairs.sum() / pairs) if pairs else None,
            "identical_minute_history_pairs": int(rows.identical_minute_history_pairs.sum()),
            "identical_minute_history_share": float(rows.identical_minute_history_pairs.sum() / pairs) if pairs else None,
            "pair_weighted_mean_of_team_median_jaccard": (
                float(np.average(
                    rows.loc[valid_medians, "median_pair_jaccard"],
                    weights=rows.loc[valid_medians, "eligible_pairs"],
                )) if valid_medians.any() else None
            ),
        })
    league_season = pd.DataFrame(league_rows)
    return summary, league_season, quality


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary, league_season, quality = summarize()
    summary.to_csv(OUT / "aggregate_summary.csv", index=False)
    summary.to_json(OUT / "aggregate_summary.json", orient="records", indent=2)
    league_season.to_csv(OUT / "league_season_summary.csv", index=False)
    result = {
        "quality": quality,
        "summary": summary.to_dict(orient="records"),
        "league_season_summary_rows": len(league_season),
    }
    (OUT / "run_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
