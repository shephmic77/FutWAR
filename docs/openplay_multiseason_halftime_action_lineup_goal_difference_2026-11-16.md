# Multi-season action and lineup check on goal difference — 2026-11-16

## Purpose

This is a companion to the multi-season expected-points check. The owner chose expected match points as the first outcome scale and expected goal difference as a secondary check. This analysis asks whether candidate action features and starting-player identities help forecast a team's final goal margin beyond halftime match context. It does **not** estimate individual player impact or WAR.

## Design

- Source: the locally acquired OpenPlay v0.1.0 event, match, and lineup data. No row-level records or player IDs are published in this report.
- Outcome: final 90-minute goal difference from each team's perspective (home margin for the home team, its negative for the away team). This is not expected goals (xG).
- Folds: six within-season chronological holdouts, 2019–20 through 2024–25. Each season uses the same chronological 60/15/25 split as the expected-points action/lineup audit.
- Models: halftime score/time context; context plus starting-XI identities; context plus sampled player action candidates; and context plus both actions and starting-XI identities. Full transitions and clock-adjusted action features are both included as sensitivity variants.
- Tuning: each Ridge model chooses its regularization on earlier dates in that fold; the held-out dates are used only for evaluation.
- Uncertainty: 5,000 paired match-cluster bootstrap resamples for pooled MAE differences. The interval conditions on the fitted fold models and does not account for dependence between season folds, model refitting, feature selection, or unresolved player identity errors.

Four score-unreconciled matches were excluded. The analysis includes 2,632 held-out matches across the six folds. Of 14,334 matches with source match rows, 14,330 had usable halftime state. The final action-plus-lineup design had 12,503 matches with valid starting XIs; one invalid XI was excluded. Sixteen action rows without positive player exposure were removed. Player identities remain candidate links, not validated links.

## Results

MAE differences are candidate minus baseline, so positive values mean the added feature set made predictions less accurate.

| Held-out comparison | MAE change | Paired match-bootstrap 95% interval | Interpretation |
|---|---:|---:|---|
| Add starting-XI identities on top of full action candidates | +0.01449 goals | +0.00720 to +0.02182 | Worse pooled; worse in 5 of 6 season folds |
| Add starting-XI identities on top of clock-adjusted action candidates | +0.01446 goals | +0.00712 to +0.02170 | Worse pooled; worse in 5 of 6 season folds |
| Add starting-XI identities to context alone | +0.01959 goals | +0.01156 to +0.02783 | Worse pooled |
| Add full action candidates to context alone | +0.00528 goals | +0.00221 to +0.00833 | Worse pooled |
| Add clock-adjusted action candidates to context alone | +0.00532 goals | +0.00227 to +0.00852 | Worse pooled |

### League breakdown: add lineup identities on top of action candidates

| League | Held-out matches | MAE change | Paired match-bootstrap 95% interval |
|---|---:|---:|---:|
| Bundesliga | 407 | +0.01727 | −0.00408 to +0.03944 |
| La Liga | 623 | +0.01210 | −0.00215 to +0.02680 |
| Ligue 1 | 422 | +0.02157 | +0.00660 to +0.03618 |
| Premier League | 568 | +0.00772 | −0.00828 to +0.02361 |
| Serie A | 612 | +0.01648 | +0.00124 to +0.03203 |

The point estimate is worse in all five leagues, but the league-specific interval excludes zero only for Ligue 1 and Serie A. For adding action candidates to context alone, the point estimate is worse in four leagues and slightly better in the Premier League; only Ligue 1's interval excludes zero. These league intervals are descriptive sensitivity checks, not five independent confirmations, and still condition on the fitted models.

For the action-plus-lineup comparison, the exception is 2024–25: adding the XI signal slightly lowered MAE in that fold. That exception makes the result mixed by season, although the pooled comparison is clearly worse and five folds are worse. The per-season table is retained in the local ignored report outputs.

## What this means

On this target and with these candidate features, the model does not show that lineup identities add useful predictive information beyond the action candidate. The action candidate also fails to improve goal-margin forecasts over halftime context alone. This is a warning about current feature construction and data quality, not proof that players or their actions have no value. Team-level forecast usefulness is not the same as assigning value to a player.

This result does not choose an action-value policy, a lineup-impact adjustment, or a teammate-uplift method. It does not establish causality, the value of a role, goalkeeper value, cross-league comparability, any of the six replacement comparisons, or an individual score. No player coefficients or player scores were exported.

## Reproduction

From the repository root in PowerShell:

```powershell
& 'C:\Users\mikey\AppData\Local\Programs\Python\Python313\python.exe' scripts\audit_openplay_multiseason_halftime_action_lineup_goal_difference.py
```

The script writes ignored local outputs under `reports/openplay_multiseason_halftime_action_lineup_goal_difference/` and leaves source data unchanged. The analysis script passed Python compilation before the run; the complete run finished and wrote the summary and comparison tables.

## Files

- Script: `scripts/audit_openplay_multiseason_halftime_action_lineup_goal_difference.py`
- Local summary: `reports/openplay_multiseason_halftime_action_lineup_goal_difference/summary.json`
- Expected-points companion: `docs/openplay_multiseason_halftime_action_lineup_2026-11-13.md`
- League-level paired intervals: `reports/openplay_multiseason_halftime_action_lineup_goal_difference/paired_differences_by_league.csv`
