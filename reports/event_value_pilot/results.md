# Event danger prediction pilot — results

**Status:** bounded research diagnostic, not a player contribution score or FutWAR. It tests whether event context helps forecast scoring/conceding events before any action credits are assigned.

## What was tested

The pilot used the licensed Wyscout 2017–18 events for the Big Five. Goal tags were reconciled to the published match score before a fixture entered the sample. One of 1,826 fixtures was excluded because the event reconstruction missed a goal. It kept source-order for events sharing timestamps and defined a positive outcome as the team scoring or conceding within the next ten raw events in the same half; only complete horizons counted. A model using event history and location/time context was trained on pre-2018-01-01 data, checked on January–February, and evaluated on March onward. It was compared with a constant-rate forecast and a location/time-only model. The training sample was a fixed-seed sample of 160,000 eligible states; the held-out test contained 303,119 sampled states in 545 fixtures.

Three coordinate points among 3,071,395 events fell outside the source's expected 0–100 pitch range. The raw events remain unchanged. The diagnostic counts them and sets their derived location coordinates to missing instead of clipping them. The run metadata and fixture reconciliation output retain these checks.

## Held-out results

| Forecast target | Error measure | Constant-rate error | Location/time model reduction | Event-history model reduction |
|---|---|---:|---:|---:|
| Score in next 10 events | Brier | 0.010426 | 1.46% | 2.57% |
| Score in next 10 events | Log loss | 0.058459 | 7.62% | 10.48% |
| Concede in next 10 events | Brier | 0.005522 | 1.05% | 2.04% |
| Concede in next 10 events | Log loss | 0.034379 | 8.14% | 12.68% |

Error reductions are relative to the same constant-rate forecast on held-out event states. Event history improves both errors over the constant forecast in every league; the Brier gain for conceding is smallest in Bundesliga (0.49%). Positive bars in `heldout_error_improvement.png` mean lower prediction error. `heldout_calibration.png` shows reliability by prediction bin. League breakdowns are in `heldout_error_improvement.csv` and the full model metrics in `prediction_metrics.csv`.

## Interpretation and boundary

This is useful evidence that event sequence/context contains predictive information beyond a constant event rate. It is not evidence that a particular action caused a goal, that the model identifies a player's marginal impact, or that a non-scoring action deserves a particular number of points. Ten-event windows overlap, states within a match are dependent, and the test is a later-month holdout from one season—not a held-out future season or cross-season validation. Rare scoring/conceding outcomes also make the absolute probabilities small.

The next contribution step should compare two explicit crediting routes on this one-season sample:

1. **Action change in danger:** value an action by the modelled change in scoring/conceding probability over a defined horizon, following the VAEP family of methods.
2. **Expected match-points change:** estimate win/draw/loss probabilities from match state before and after an action, then value the change as `3 × P(win) + P(draw)`. This would align directly with the project's eventual unit, but needs a separate match-state model and careful handling of score/time transitions.

Neither is selected yet. Any player aggregation needs source player-ID review and a shared-credit rule for build-up, shot and goal events. The archive's IDs are not yet reconciled with the player-seasons. Wyscout covers only five of forty league-season cells; the other 35 are absent. No action values, seasonal player totals, or replacement comparisons were calculated here.

## Reproduction

From the repository root in PowerShell:

```powershell
py scripts/run_event_value_pilot.py
py scripts/summarize_event_value_pilot.py
```

The run is recorded at `run.json`; source hashes point to the separately archived licensed files. The source release is cited in `data/wyscout_research_manifest.json`.
