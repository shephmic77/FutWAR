# Expected-points primary and goal-difference check — 2026-11-03

## Question and owner direction

The owner selected expected league points as the primary outcome scale for the first fitted comparison and final match goal difference as a check. The owner also asked to compare a fitted method with a transparent hand-set action-value method. This report evaluates match-state outcome prediction only; it does not yet compare player-credit methods or hand-set values.

## Method

The event-state pipeline was extended to retain each target team's final goal difference alongside its final league points. The same score-reconciled Wyscout 2017–18 archive, state sampling rule, and five leave-one-league-out folds were used for both outcomes. Each held-out match contributes up to 40 sampled post-event states per team. One fixture with an event-derived score mismatch remains excluded.

For expected points, the compared models are the existing score/time/context multinomial logistic model and event-context histogram gradient boosting classifier. For goal difference, the corresponding models predict the final team goal margin with histogram gradient boosting regression: one uses score/time/context, the other adds the event-history/action features. A training-mean baseline is included. All rows in a match remain together for uncertainty resampling; 1,000 paired match-cluster bootstrap samples were used per held-out league. Intervals condition on the already fitted models.

This is a same-season transfer check, not future-season validation. The March–May 2018 period has already informed prior development. State rows are sampled observations from matches, not independent cases. The target is final observed goal difference conditional on an event state. It is **not xG**, and prediction of the final margin does not itself value an action or assign player credit.

## Results

The score/time/context model had lower expected-points RMSE, multiclass Brier score, and log loss than the event-context model in all five held-out leagues, consistent with the earlier transfer analysis.

For the goal-difference check, negative `event-context minus score-time-context` means event context has lower error:

| Held-out league | Matches | Score/time RMSE | Event-context RMSE | RMSE difference (95% paired match interval) | MAE difference |
|---|---:|---:|---:|---:|---:|
| Premier League | 379 | 1.2964 | 1.2961 | -0.0003 [-0.0059, 0.0059] | +0.0022 |
| La Liga | 380 | 1.2629 | 1.2645 | +0.0017 [-0.0036, 0.0071] | +0.0025 |
| Serie A | 380 | 1.1992 | 1.1934 | -0.0058 [-0.0121, 0.0003] | +0.0017 |
| Bundesliga | 306 | 1.3193 | 1.3158 | -0.0035 [-0.0111, 0.0038] | -0.0005 |
| Ligue 1 | 380 | 1.3022 | 1.3037 | +0.0015 [-0.0060, 0.0091] | +0.0018 |

The state-weighted RMSE intervals all include zero. Match-weighted RMSE intervals also include zero in all five leagues. The direction is mixed and the differences are small relative to the uncertainty. This check therefore does not establish that event history improves final-goal-difference prediction beyond the simpler model. Both model families substantially outperform the training-mean baseline on this sample, but that is not evidence of player-level validity.

## Interpretation and next model gates

1. Keep expected points primary and goal difference as a secondary diagnostic for now, as requested. These results do not settle the final scale.
2. Do not add event-history features solely because they make a richer football story; their incremental predictive value was not established in this check.
3. The transparent hand-set action-value comparison still needs owner input on what actions and value rules to include. I have not inserted arbitrary coefficients.
4. Adjusted lineup impact and teammate uplift remain candidate components. The current fit does not estimate either. They require an incremental held-out comparison against action-only value, plus a clear definition of teammate uplift and identity/exposure checks.
5. Do not publish player scores yet. There is only one event season, player identities are not fully verified against the player-season panel, specific played positions are unvalidated, and there is no future-season holdout or feasible team-replacement pool.

## Reproduction

From the project root in Windows PowerShell:

```powershell
py scripts\run_expected_points_state_pilot.py --cross-league-transfer
```

The run writes aggregate tables to `reports/expected_points_pilot/cross_league_transfer/`:

- `goal_difference_metrics.csv`
- `goal_difference_match_cluster_intervals.csv`
- existing `metrics.csv` and `match_cluster_bootstrap_intervals.csv` for expected points

Raw source rows are not modified. These local report files remain subject to the repository's existing generated-output ignore rules.
