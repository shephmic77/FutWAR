# Event-type diagnostic for expected-points state changes

This follow-up checks whether the current model distinguishes action families, including shots, saves, duels and goalkeeper-coded events. It reuses the held-out March–May 2018 event sample and verifies goal events against the hash-verified Wyscout archive. These remain model-prediction differences, not measured player contributions.

## Data-alignment correction

The first export paired predictions sorted by sample ID with event labels in fixture order. That mislabeled event types in the initial diagnostic summary. I corrected the export to align metadata by sample ID, added a regression test, reran the same models and rebuilt the tables and chart below. Match-level model metrics were unaffected by the export-order bug. The separate direct-versus-shared sequence comparison reconstructs prediction pairs per event and is unaffected.

## Corrected findings

Across 306,752 sampled event pairs, the overall median change is zero and the mean is −0.00171. About 37.6% of deltas are within ±0.005 points. Correctly aligned action families now show different distributions: for example, sampled goal shots have a positive mean change, while saves and interruptions have negative means. These associations still should not be read as individual player value; the model estimates the outcome for the event's team, source event-team conventions vary, and actions are highly selected by match state.

| Event type | Sampled events | Mean change | Median | 10th–90th percentile | `playerId=0` rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pass | 156,690 | +0.00356 | +0.00545 | −0.00759 to +0.01616 | 2 |
| Duel | 82,448 | −0.00895 | −0.00638 | −0.02303 to 0 | 8,892 |
| Others on the ball | 24,911 | −0.00741 | −0.00644 | −0.02344 to +0.00723 | 27 |
| Free Kick | 18,072 | −0.00476 | −0.00502 | −0.02126 to +0.00695 | 1,080 |
| Interruption | 13,059 | −0.02070 | −0.01984 | −0.04064 to +0.00011 | 13,059 |
| Foul | 4,585 | −0.00072 | 0 | 0 to 0 | 34 |
| Shot | 3,995 | +0.05869 | −0.00130 | −0.01400 to +0.06242 | 0 |
| Save attempt | 1,635 | −0.02162 | −0.01907 | −0.04388 to −0.00112 | 0 |
| Offside | 742 | +0.00238 | +0.00174 | −0.00534 to +0.01471 | 0 |
| Goalkeeper leaving line | 615 | −0.00279 | −0.00089 | −0.00931 to +0.00523 | 0 |

The 414 sampled goal-tagged shots have a mean change of +0.60368; 94.9% move the event team's predicted expected points upward. The score/time/form tree baseline has +0.61006 mean change and is positive for 95.4%; a smooth score-state logistic benchmark has +0.56725 and is positive for all 414. The goal sanity check now passes directionally. By contrast, the event-context model's pooled held-out prediction error is worse than the smooth score-state benchmark: expected-points RMSE 0.99066 vs 0.96998, Brier 0.45073 vs 0.43609, and log loss 0.77307 vs 0.75058.

The smooth benchmark uses league as a category and learned logistic relationships for score difference, remaining minutes, their interaction, total goals, venue and prior form. These features were introduced after inspecting the first held-out result, so this is an exploratory comparison on a reused test window, not a fresh unbiased validation. It is a benchmark candidate, not a chosen FutWAR model.

The `playerId=0` value is a source sentinel, not a player. It appears in 23,094 rows (7.5%); all 13,059 Interruption rows use it. Other zero-ID rows, particularly Duels and Free Kicks, also cannot be assigned to a player from this event row. A populated ID field does not mean every event identifies a player. Exclude or separately classify sentinel IDs in future player-credit analyses.

![Median state change by event type with 10th–90th percentiles](action_state_by_event_type.png)

## What this means for the next model step

The current model reacts to goal events in the expected direction, but its event-context version adds no held-out predictive improvement over the smooth score-state benchmark. The action-state design therefore remains unready for player totals. We should first improve out-of-sample prediction with a new chronological season/window and evaluate calibration by league, score state, and event family. Only then should we test actor allocation and the three replacement baselines. The model must not be tuned to make positions look balanced; defense and goalkeeper coverage needs separate evidence and the common points scale must be validated.

Run from the repository root in PowerShell:

```powershell
python scripts/run_expected_points_state_pilot.py
python scripts/summarize_action_state_diagnostics.py
```

The first command verifies sources, rebuilds models and splits, and writes paired predictions. The second verifies source hashes and writes `action_state_by_event_type.csv`, `goal_event_sanity_check.csv` and `action_state_by_event_type.png`. Neither script changes raw source data or calculates player value.
