"""Goal-difference companion to the multi-season action/lineup comparison.

Reuses the same fixtures, chronological splits, action candidate table, and
player feature construction as the expected-points experiment. This is an
exploratory team-forecast check, not player impact validation or WAR.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

import audit_openplay_multiseason_halftime_action_lineup as source
import audit_openplay_halftime_action_lineup_forecast as common


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/openplay_multiseason_halftime_action_lineup_goal_difference"
ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0)
MODELS = {
    "context": (False, False, "full"),
    "context_plus_lineup": (False, True, "full"),
    "context_plus_full_action": (True, False, "full"),
    "context_plus_full_action_and_lineup": (True, True, "full"),
    "context_plus_clock_action": (True, False, "clock"),
    "context_plus_clock_action_and_lineup": (True, True, "clock"),
}
COMPARISONS = (
    ("context_plus_full_action_and_lineup", "context_plus_full_action"),
    ("context_plus_clock_action_and_lineup", "context_plus_clock_action"),
    ("context_plus_lineup", "context"),
    ("context_plus_full_action", "context"),
    ("context_plus_clock_action", "context"),
)


def attach_goal_difference(frame: pd.DataFrame) -> pd.DataFrame:
    match_path = source.RAW / "matches.parquet"
    matches = pd.read_parquet(match_path, columns=[
        "match_id", "home_team_id", "away_team_id", "home_score_90", "away_score_90"
    ]).drop_duplicates("match_id")
    indexed = matches.set_index("match_id")
    values = []
    for row in frame.itertuples(index=False):
        match = indexed.loc[row.match_id]
        home_diff = float(match.home_score_90) - float(match.away_score_90)
        values.append(home_diff if int(row.team_id) == int(match.home_team_id) else -home_diff)
    out = frame.copy()
    out["goal_difference"] = values
    return out


def predict(train: pd.DataFrame, other: pd.DataFrame, model_name: str,
            target_col: str, alpha: float) -> tuple[np.ndarray, dict]:
    include_action, include_lineup, action_col = MODELS[model_name]
    x_train, x_other, audit = common.build_design(
        train, other, include_action, include_lineup, action_col)
    model = Ridge(alpha=alpha, solver="lsqr", tol=1e-5)
    model.fit(x_train, train[target_col].to_numpy(dtype=float))
    return model.predict(x_other), audit


def metric(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "mean_prediction_error": float(np.mean(predicted - actual)),
    }


def paired_delta_ci(frame: pd.DataFrame, candidate: str, baseline: str,
                    replicates: int, seed: int) -> dict[str, float | int]:
    # Pair both team perspectives first; resample fixtures, never team rows.
    work = frame.copy()
    work["delta"] = (np.abs(work[f"{candidate}_prediction"] - work.goal_difference)
                     - np.abs(work[f"{baseline}_prediction"] - work.goal_difference))
    per_match = work.groupby("match_id", sort=False).delta.mean().to_numpy()
    rng = np.random.default_rng(seed)
    draws = np.empty(replicates, dtype=float)
    for i in range(replicates):
        draws[i] = rng.choice(per_match, size=len(per_match), replace=True).mean()
    return {
        "mae_delta_candidate_minus_baseline": float(per_match.mean()),
        "paired_match_bootstrap_95_low": float(np.quantile(draws, .025)),
        "paired_match_bootstrap_95_high": float(np.quantile(draws, .975)),
        "bootstrap_replicates": replicates,
        "test_matches": int(len(per_match)),
    }


def paired_delta_by_league(frame: pd.DataFrame, candidate: str, baseline: str,
                           replicates: int, seed: int) -> list[dict]:
    """Match-paired MAE differences within league, preserving both team rows."""
    work = frame.copy()
    work["delta"] = (np.abs(work[f"{candidate}_prediction"] - work.goal_difference)
                     - np.abs(work[f"{baseline}_prediction"] - work.goal_difference))
    match_deltas = (work.groupby(["league", "match_id"], sort=False).delta.mean()
                    .reset_index())
    rows = []
    for league_index, (league, group) in enumerate(match_deltas.groupby("league", sort=True)):
        values = group.delta.to_numpy(dtype=float)
        rng = np.random.default_rng(seed + league_index)
        draws = np.empty(replicates, dtype=float)
        for i in range(replicates):
            draws[i] = rng.choice(values, size=len(values), replace=True).mean()
        rows.append({
            "league": league,
            "candidate": candidate,
            "baseline": baseline,
            "mae_delta_candidate_minus_baseline": float(values.mean()),
            "paired_match_bootstrap_95_low": float(np.quantile(draws, .025)),
            "paired_match_bootstrap_95_high": float(np.quantile(draws, .975)),
            "bootstrap_replicates": replicates,
            "test_matches": int(len(values)),
            "matches_with_candidate_lower_absolute_error": int((values < 0).sum()),
        })
    return rows


def main() -> None:
    frame, audit = source.read_inputs()
    frame = attach_goal_difference(frame)
    fold_rows, prediction_frames = [], []

    for fold_index, season in enumerate(source.TARGET_SEASONS):
        train, validation, test = source.split_fold(frame, season)
        fold = pd.DataFrame({
            "match_id": test.match_id.to_numpy(),
            "league": test.league.to_numpy(),
            "season": test.season.to_numpy(),
            "goal_difference": test.goal_difference.to_numpy(),
        })
        fold_audits = {}
        selected_alpha = {}
        validation_mae = {}
        for model_index, name in enumerate(MODELS):
            best = None
            for alpha in ALPHAS:
                val_pred, _ = predict(train, validation, name, "goal_difference", alpha)
                score = mean_absolute_error(validation.goal_difference, val_pred)
                candidate = (float(score), -float(alpha), float(alpha))
                if best is None or candidate < best:
                    best = candidate
            assert best is not None
            validation_mae[name], _, selected_alpha[name] = best
            trainval = pd.concat([train, validation], ignore_index=True)
            test_pred, design_audit = predict(
                trainval, test, name, "goal_difference", selected_alpha[name])
            fold[f"{name}_prediction"] = test_pred
            fold_audits[name] = design_audit

            fold_rows.append({
                "heldout_season": season,
                "model": name,
                "selected_alpha_on_prior_dates": selected_alpha[name],
                "validation_mae": validation_mae[name],
                "training_matches": int(train.match_id.nunique()),
                "validation_matches": int(validation.match_id.nunique()),
                "test_matches": int(test.match_id.nunique()),
                **metric(test.goal_difference.to_numpy(), test_pred),
                "player_feature_coverage": design_audit.get("other_player_feature_coverage_pct"),
            })
        fold["heldout_season"] = season
        prediction_frames.append(fold)
        print(f"Completed {season}: {test.match_id.nunique():,} held-out matches", flush=True)

    predictions = pd.concat(prediction_frames, ignore_index=True)
    comparisons = []
    league_comparisons = []
    for index, (candidate, baseline) in enumerate(COMPARISONS):
        comparison = {"candidate": candidate, "baseline": baseline}
        comparison.update(paired_delta_ci(
            predictions, candidate, baseline, replicates=5000, seed=20261116 + index))
        comparisons.append(comparison)
        league_comparisons.extend(paired_delta_by_league(
            predictions, candidate, baseline, replicates=5000,
            seed=20261216 + index * 100))

    by_season = []
    for season, group in predictions.groupby("heldout_season", sort=True):
        for candidate, baseline in COMPARISONS:
            delta = (np.abs(group[f"{candidate}_prediction"] - group.goal_difference)
                     - np.abs(group[f"{baseline}_prediction"] - group.goal_difference))
            match_delta = pd.DataFrame({"match_id": group.match_id, "delta": delta}).groupby(
                "match_id", sort=False).delta.mean()
            by_season.append({
                "season": season, "candidate": candidate, "baseline": baseline,
                "test_matches": int(group.match_id.nunique()),
                "mae_delta_candidate_minus_baseline": float(match_delta.mean()),
                "matches_with_candidate_lower_absolute_error": int((match_delta < 0).sum()),
            })

    league_rows = []
    for (season, league), group in predictions.groupby(["heldout_season", "league"], sort=True):
        for name in MODELS:
            league_rows.append({
                "season": season, "league": league, "model": name,
                "matches": int(group.match_id.nunique()),
                **metric(group.goal_difference.to_numpy(), group[f"{name}_prediction"].to_numpy()),
            })

    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(fold_rows).to_csv(OUT / "fold_metrics.csv", index=False)
    pd.DataFrame(comparisons).to_csv(OUT / "pooled_paired_differences.csv", index=False)
    pd.DataFrame(league_comparisons).to_csv(OUT / "paired_differences_by_league.csv", index=False)
    pd.DataFrame(by_season).to_csv(OUT / "paired_differences_by_season.csv", index=False)
    pd.DataFrame(league_rows).to_csv(OUT / "metrics_by_season_league.csv", index=False)
    predictions.to_csv(OUT / "team_match_predictions_local.csv", index=False)
    summary = {
        **audit,
        "target": "team-perspective final goal difference after 90 minutes",
        "heldout_seasons": list(source.TARGET_SEASONS),
        "heldout_match_count": int(predictions.match_id.nunique()),
        "split": "same within-season chronological 60/15/25 splits as the expected-points action-lineup audit",
        "tuning": "each model selects Ridge alpha on earlier dates only; tie prefers stronger regularization",
        "uncertainty": "paired 5,000-replicate match-cluster bootstrap for pooled and within-league MAE differences; intervals condition on fitted models and do not capture season-fold dependence or refit uncertainty",
        "formula_or_credit_selected": False,
        "player_coefficients_exported": False,
        "causal_player_value_estimated": False,
        "interpretation": "exploratory predictive-utility check on the owner's secondary scale; not player validation or WAR",
        "outputs_local_ignored": True,
        "pooled_comparisons": comparisons,
        "league_comparisons": league_comparisons,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
