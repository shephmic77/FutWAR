# Expected-points action-state pilot

Run date: 2026-10-11  
Source: the locally staged, hash-verified Wyscout 2017–18 match and event archives listed in `data/wyscout_research_manifest.json`.

## Question

Can a model estimate a team's final league points from the match state around an event, and does event context improve that estimate beyond score, time, venue and recent team form? This is an early test of the project's desired points scale. It does not estimate player WAR.

For each event team, the target is its final match points: 0 for a loss, 1 for a draw and 3 for a win. Expected points are `P(draw) + 3 × P(win)`. The state-only model uses league, match time/period, score, venue and pre-match form. The event-context model adds the event type, sub-type, location, accuracy and recent event sequence. A constant-outcome model uses only the training sample's outcome frequencies.

Training used 80,000 sampled event pairs from fixtures before 2018-01-01, with both pre-action and post-action rows included (160,000 state rows). January–February fixtures were held for validation; March–May fixtures were held out for testing. Evaluation samples every third raw event and scores only fixtures whose event-derived goal total matches the published match score.

## Held-out results

| Model | Expected-points RMSE | Three-class Brier | Log loss |
| --- | ---: | ---: | ---: |
| Constant outcome | 1.3246 | 0.6542 | 1.0789 |
| Score/time/form | 0.9951 | 0.4541 | 0.7794 |
| Smooth score-state benchmark | 0.9700 | 0.4361 | 0.7506 |
| Event context | 0.9907 | 0.4507 | 0.7731 |

The smooth benchmark is an exploratory multinomial logistic model with learned relationships for score difference, remaining time, their interaction, total goals, venue and recent form. It performed better on this test window than the event-context tree model. Since it was introduced after the original test result was inspected, this is model development, not an unbiased comparison on a fresh holdout. Do not use the test window again to tune a final model. See `prediction_metrics.csv` for the full league-by-league values.

The decile calibration plot compares predicted and observed final points for 306,752 held-out post-event states. The points track the ideal line reasonably closely at this aggregate level. These are repeated states from the same fixtures, not 306,752 independent matches; the chart is a descriptive calibration check, not an uncertainty interval.

## What the action-state differences show

The exploratory action-state delta is the event-context model's expected points after an action minus its estimate before that action. Across 306,752 held-out sampled pairs, the mean was −0.0017 points, the median was 0, and the 10th–90th percentile range was −0.0209 to +0.0127. After correcting and testing event-label alignment, sampled goal-tagged shots have a mean +0.6037-point change and 94.9% are positive. This is a useful basic sanity check, but the event-context model still loses to the smooth score-state benchmark in pooled held-out predictive metrics. The full corrected event-family comparison is in [the action-type diagnostic](action_type_diagnostics.md).

Do not sum these deltas by player. They are conditional prediction changes, not causal effects. Events overlap within a match, some events are credited to a team rather than a player, off-ball work is not observed, the dataset covers only one season, and role/keeper evidence is not yet sufficient. A goal or save may also change the state far more than ordinary actions; this prototype has not validated those tail cases as player credit.

## Coverage and reproducibility

- 1,826 fixtures were audited; 1,825 were included and one Premier League match was excluded because the event goal tags did not reconcile to the published score.
- 2,047,644 pre/post state rows were constructed; 306,752 held-out action pairs were evaluated.
- The `playerId` field is populated on all 306,752 held-out sampled event rows, but 23,094 contain the source sentinel `0`, not a player. The remaining rows contain 2,164 distinct nonzero Wyscout player IDs. Neither the field nor profile existence establishes a verified crosswalk to FutWAR player-season records. See the [event-type diagnostic](action_type_diagnostics.md).
- Three out-of-pitch coordinate pairs were flagged and represented as missing only in derived model features. Source archives were not edited.
- Run in Windows PowerShell from the project root with `py scripts/run_expected_points_state_pilot.py`.

Generated files: `prediction_metrics.csv`, `fixture_audit.csv`, `heldout_event_state_changes.csv`, `heldout_state_changes_by_event_type.csv`, `paired_state_model_sanity.csv`, `heldout_match_state_metrics.png`, `heldout_expected_points_calibration.png`, and `heldout_state_changes_by_event_type.png`. The follow-up [event-type diagnostic](action_type_diagnostics.md) adds sentinel-aware actor coverage, corrected action-family distributions and a goal-event sanity check.

## Interpretation and next research step

This supports continuing with expected match points as a candidate outcome scale. It does not yet support an action-to-player credit rule, a replacement formula, or a WAR number. Before calculating player totals, expand chronological evaluation across seasons, check calibration by league and match state, test the event contribution differences against goals and shots, and decide how to handle shared build-up, team events, goalkeepers and substitutions. Those decisions change the meaning of the measure and should be discussed before implementation.
