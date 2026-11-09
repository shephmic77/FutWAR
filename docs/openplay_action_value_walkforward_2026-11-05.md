# OpenPlay action-context expected-points walk-forward — 2026-11-05

## Status

Exploratory team-state/action-context experiment only. It fits expected final league points from earlier seasons and tests on the next season. It produces no player value, player credit, WAR, replacement comparison, or website output. Event context gives a small average improvement in final-outcome prediction, but fold-level evidence is mixed; its much larger predicted transitions are not evidence that its action values are more accurate.

## Data and scope

- Pinned local OpenPlay `data-v0.1.0` files across the five Big Five leagues and 2017–18 through 2024–25.
- All 14,330 matches retained by the score-reconciled sample had event-derived scores equal to supplied 90-minute results. No reconstruction mismatches were found in this run.
- Excluded source-flagged `score_differs_from_events` and `few_events` matches, plus non-regulation periods.
- Constructed 44,683,476 team-perspective event states (two team views per event).
- Fitting sample: every twentieth source event for each team perspective. Held-out prediction and transition sample: every fifth event; each sampled transition was calculated against the immediately preceding event, so no intervening event is bundled into the measured step.
- Train/holdout split is chronological by full season: each fold trains only on earlier seasons and tests on the next. The final 2024–25 fold is still exploratory and has now been used for method development; it is not an untouched final test.

## Models compared

Both models predict the target team's final points (0, 1, or 3) from the current match state: league, minutes remaining, score difference and its square, total goals, score-by-time interaction, red-card difference, home/away, and prior within-season team points-per-match and goal-difference-per-match differences. Those team-form features are computed only from earlier results in the same league-season. They are a basic opponent-strength proxy, not a full strength rating.

1. **State-only:** match state and league.
2. **Event-context:** the same state plus event period, event type, outcome, coarse start-location zone, and whether the event team is the target or opponent.

Player IDs are not features and no player attribution is made. Events with missing actor IDs remain part of team context only.

## Out-of-time outcome prediction

| Held-out season | Matches | State-only Brier | Event-context Brier | Difference (event minus state) | Match-bootstrap 95% CI for difference |
|---|---:|---:|---:|---:|---:|
| 2018–19 | 1,826 | 0.44721 | 0.44732 | +0.00011 | [+0.00003, +0.00020] |
| 2019–20 | 1,724 | 0.45268 | 0.45266 | -0.00003 | [-0.00011, +0.00005] |
| 2020–21 | 1,825 | 0.44376 | 0.44367 | -0.00009 | [-0.00015, -0.00001] |
| 2021–22 | 1,810 | 0.45344 | 0.45332 | -0.00012 | [-0.00019, -0.00005] |
| 2022–23 | 1,818 | 0.43385 | 0.43379 | -0.00006 | [-0.00014, +0.00002] |
| 2023–24 | 1,751 | 0.44032 | 0.44023 | -0.00008 | [-0.00016, -0.00001] |
| 2024–25 | 1,750 | 0.44423 | 0.44416 | -0.00007 | [-0.00014, -0.000003] |

The event-context model has lower Brier in six of seven seasons, though the differences in 2019–20 and 2022–23 are uncertain. Four match-bootstrap intervals favor event context, one favors the state-only model, and two cross zero. The mean season-fold Brier difference is **-0.0000479** (event-context minus state-only; weighted by held-out matches: **-0.0000476**). This is a small predictive improvement, not evidence that the transition magnitudes represent accurate action values.

## Consecutive transition decomposition

For the sampled every-fifth event, the **full transition** is predicted expected points after the event minus predicted expected points after the immediately prior event. The **clock-only counterfactual** carries the prior match state and event descriptors forward to the current event time. The **clock-adjusted residual** is the current event-state prediction minus that counterfactual. Full transition equals clock-only plus residual to machine precision (maximum absolute closure error `2.3e-16`).

Across the seven test seasons, mean absolute event-context full transitions range from 0.01456 to 0.01845 expected points per sampled transition. The mean absolute clock-only component is 0.00016–0.00018; the clock-adjusted residual is 0.01451–0.01841. Weighted across all 7,770,624 sampled transitions, event-context means are 0.016001 full transition and 0.015956 residual. Match-cluster bootstrap 95% intervals are [0.015911, 0.016090] and [0.015868, 0.016055], respectively. The state-only model's corresponding weighted means are 0.001246 full transition [0.001218, 0.001275] and 0.001075 residual [0.001046, 0.001104]. Event-context residuals are positive on 46.9%–48.9% of sampled team-perspective transitions (47.7% weighted overall); the state-only share is 23.0% weighted overall. Event-context residual 95th percentiles range from 0.0587 to 0.0643 expected points.

The league-level match-cluster intervals show this scale gap in every league, not just one: mean absolute event-context residuals range from 0.01554 in the Bundesliga to 0.01677 in La Liga, while state-only residuals range from 0.00104 to 0.00111. League-level intervals and all 35 league-season estimates are in the local `transition_uncertainty.csv`. The event-context residual is roughly 14–16 times the state-only residual in each league, despite little improvement in outcome prediction. This points to event-feature/model sensitivity as a central unresolved issue, rather than a league-specific effect.

These transition magnitudes are descriptive model outputs, not empirically observed points, causal action effects, or player credits. Adding event labels changes predicted swings far more than it changes proper scoring metrics, and the action model does not consistently improve held-out forecasts. That gap is a warning against interpreting its larger transitions as accurate contribution values. Rare event categories can be highly noisy; inspect counts and coverage before interpreting any family-level rows. The counterfactual holds the last event descriptor, including which team's event it was, fixed while advancing time and is a modeling convention, not an observed no-action state.

## Interpretation and remaining checks

- The event-context model has a small mean predictive gain in the chronological folds, but its transition scale remains poorly supported. Keep the state-only model as a benchmark and compare the individual feature ablations before considering action values.
- Event-type, outcome, and location ablations are now complete below. The event-outcome and location labels are not selected as action weights; they are model inputs whose removal was tested for sensitivity.
- Home/away and a simple prior-form strength proxy are included. Nominal player role and tactical role are not, because player-specific actual role minutes are not validated.
- The match-cluster intervals are narrow for the sampled-data means, but quantify only sampling uncertainty conditional on fitted fold models. They do not include model-refitting uncertainty, model misspecification, or establish causal action values. The local output includes intervals at overall, league, season, and league-season levels.
- A separate, same-fold expected-goal-difference check is now complete. It predicts final 90-minute goal difference in goals, not xG. Results and transition-scale sensitivity are below; expected points remains the primary target the owner selected.
- The full event-context model represents goals through both score and event-type features. Removing event type reduced the transition scale only about 5%, so this alone does not explain the mismatch; event-outcome and location ablations remain to be checked.
- Identity, actual role minutes, goalkeeper calibration, feasible replacement pools, and source-use provenance remain unresolved. This work does not clear those gates.

## Expected-goal-difference cross-check

A separate regression pipeline used the same score-reconciled matches, chronological folds, state/event feature definitions, sampling design, and match-cluster bootstrap. Its target is each team's final 90-minute goal difference in goals. This is an outcome prediction check on the expected-goal-difference scale, not expected goals, an isolated event's causal effect, or player credit. There are 12,504 match clusters and 7,770,624 sampled team states pooled across the seven held-out seasons.

| Scope | Matches | State RMSE | Event RMSE | RMSE difference (event minus state), 95% match-bootstrap CI | MAE difference, 95% CI |
|---|---:|---:|---:|---:|---:|
| All leagues | 12,504 | 1.25474 | 1.25358 | -0.001161 [-0.001655, -0.000661] | -0.000371 [-0.000786, +0.000058] |
| Bundesliga | 2,138 | 1.37420 | 1.37386 | -0.000343 [-0.001625, +0.001070] | +0.000906 [-0.000188, +0.002062] |
| La Liga | 2,659 | 1.15612 | 1.15521 | -0.000918 [-0.001903, +0.000098] | -0.000056 [-0.000917, +0.000779] |
| Ligue 1 | 2,404 | 1.24508 | 1.24445 | -0.000633 [-0.001650, +0.000365] | -0.000356 [-0.001268, +0.000514] |
| Premier League | 2,654 | 1.30027 | 1.29859 | -0.001682 [-0.002816, -0.000604] | -0.000794 [-0.001655, +0.000045] |
| Serie A | 2,649 | 1.20413 | 1.20202 | -0.002118 [-0.003057, -0.001146] | -0.001335 [-0.002164, -0.000458] |

Negative differences favor event context. Overall, its RMSE improvement is statistically distinguishable from zero but very small (about 0.0012 goals per sampled state); MAE's interval crosses zero. By league, RMSE intervals clearly favor event context only in the Premier League and Serie A; the other three include zero. Bundesliga MAE point estimate is worse with event context, while its interval is uncertain. This is not strong or uniform evidence that event descriptions add useful goal-difference prediction.

The predicted transition scale again grows sharply when event context is added. Overall mean absolute clock-adjusted residual is **0.02002 goals** [0.01995, 0.02009] with event context versus **0.00271 goals** [0.00267, 0.00276] for state-only, approximately 7.4 times larger. Across leagues, event-context residuals range 0.01956–0.02120 goals, while state-only residuals range 0.00234–0.00309. This reproduces the scale-sensitivity warning seen on expected points: small changes in outcome prediction accompany much larger modeled transition swings. The transitions are not calibrated action prices.

### Calibration of final-goal-difference forecasts

Using only the held-out predictions, I computed state-weighted forecast bias and the linear calibration line `observed final goal difference = intercept + slope × forecast`. Match-cluster bootstrap intervals resample complete fixtures. Pooled calibration is close to unbiased with a slope near one for both models:

| Model | Forecast bias (95% match-cluster CI) | Calibration slope (95% CI) | Intercept (95% CI) |
|---|---:|---:|---:|
| State-only | +0.00008 [-0.00046, +0.00062] | 1.0021 [0.9903, 1.0140] | -0.00008 [-0.00062, +0.00046] |
| Event-context | +0.00013 [-0.00037, +0.00061] | 1.0025 [0.9909, 1.0146] | -0.00013 [-0.00061, +0.00037] |

The pooled slope intervals include one, but league breakdowns show mild variation: both models are under-dispersed in the Bundesliga (slopes 1.031–1.033, intervals above one); the other four league intervals include one. Mean forecast bias is small in every league. These calibration summaries weight each sampled event state and use match-cluster intervals conditional on the fitted models; they do not include refitting uncertainty. Good calibration of final-score forecasts is necessary for an outcome-value model, but it does not establish that a single action produced the change between two predictions. The event-context transition scale remains unvalidated.

All seven fold RMSE point estimates favor event context, but only three fold-level match-bootstrap intervals exclude zero in its favor. Maximum full-transition decomposition closure error is `2.22e-16`; all 14,330 retained matches reconcile event-derived and supplied scores. This numerical closure validates the accounting identity only, not the model's causal or player-level interpretation. The 2024–25 fold has been used during method development and is not an untouched final test.

Reproduce in Windows PowerShell (outputs stay local and ignored):

```powershell
py scripts\run_openplay_goal_difference_walkforward.py
py scripts\summarize_openplay_goal_difference_walkforward.py
```

The outputs are `goal_difference_walkforward_by_season.csv`, `goal_difference_walkforward_match_errors.csv` (match-aggregate sufficient statistics only), `goal_difference_walkforward_forecast_summary.csv`, `goal_difference_walkforward_calibration_summary.csv`, `goal_difference_walkforward_transition_uncertainty.csv`, and the run JSON under `reports/openplay_action_value_walkforward/`. No event-level predictions are written.

## Event feature ablations

A set of models was fitted on the same seven chronological folds, each removing one current-event field while retaining the other event context and match state. The event-type-free model's mean Brier difference from state-only was **-0.000076** (lower is better), with lower Brier in six of seven holdouts. Relative to the full event-context model, its mean Brier was lower by **0.000028**, a very small change; that paired comparison does not have its own bootstrap interval.

| Held-out season | State-only Brier | Full event-context Brier | No-event-type Brier | No-type minus state Brier | Match-bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| 2018–19 | 0.44721 | 0.44732 | 0.44732 | +0.00011 | [+0.00004, +0.00020] |
| 2019–20 | 0.45268 | 0.45266 | 0.45259 | -0.00009 | [-0.00017, -0.00002] |
| 2020–21 | 0.44376 | 0.44367 | 0.44363 | -0.00014 | [-0.00022, -0.00005] |
| 2021–22 | 0.45344 | 0.45332 | 0.45333 | -0.00011 | [-0.00017, -0.00004] |
| 2022–23 | 0.43385 | 0.43379 | 0.43375 | -0.00011 | [-0.00019, -0.00003] |
| 2023–24 | 0.44032 | 0.44023 | 0.44022 | -0.00010 | [-0.00018, -0.00002] |
| 2024–25 | 0.44423 | 0.44415 | 0.44412 | -0.00011 | [-0.00019, -0.00003] |

| Model variant | Mean Brier difference vs state-only | Folds with lower Brier vs state-only | Mean absolute clock-adjusted transition (95% match-cluster CI) |
|---|---:|---:|---:|
| Full event context | -0.000048 | 6 / 7 | 0.015956 [0.015868, 0.016055] |
| Remove event type | -0.000076 | 6 / 7 | 0.015090 [0.015002, 0.015176] |
| Remove event outcome | -0.000052 | 6 / 7 | 0.015863 [0.015769, 0.015957] |
| Remove coarse location | -0.000089 | 6 / 7 | 0.014762 [0.014673, 0.014850] |
| State-only residual | — | — | 0.001075 [0.001046, 0.001104] |

Removing event type reduces the transition residual by about 5%; removing event outcome has almost no effect on its scale. Removing coarse location reduces it by about 7.5%, but the remaining residual is still roughly 13.7 times the state-only residual. It remains larger than the state-only residual in all five leagues. These ablations show that feature choice changes the magnitude, but none produces an action-value scale close to the simpler state benchmark. Event-feature transitions therefore remain model-sensitive and should not be treated as value prices or player credit.

### Paired match-bootstrap for transition-scale sensitivity

The transition-scale comparison now also has a paired match-cluster bootstrap. Each sampled transition is summarized within its fixture, then the same fixture IDs are resampled for both models. This directly tests the change in mean absolute clock-adjusted residual when a feature is removed. It covers the same 12,504 held-out fixtures and 7,770,624 sampled team-perspective transitions for every model pair; rates are weighted by transition counts. The table reports ablation minus full event-context model:

| Ablation | Difference in mean absolute residual (expected points / transition) | Paired match-bootstrap 95% interval | Direction across leagues |
|---|---:|---:|---|
| Remove event type | -0.000867 | [-0.000876, -0.000857] | Lower in all five |
| Remove event outcome | -0.000093 | [-0.000096, -0.000091] | Lower in all five |
| Remove coarse location | -0.001195 | [-0.001208, -0.001182] | Lower in all five |

The within-fixture pairing makes these intervals narrower than unpaired comparisons, but they remain conditional on each already fitted model and do not include model-refit or feature-selection uncertainty. Every ablation reduces this model's transition magnitude, with location having the largest effect; none removes the roughly 13–14-fold gap over state-only transitions. Since outcome prediction changes little while transition scale changes consistently, this is evidence of feature-driven scale sensitivity, not evidence that one ablation supplies the correct action value.

Reproduce the paired sensitivity table in Windows PowerShell after generating the walk-forward and both feature-ablation match summaries:

```powershell
py scripts\compare_openplay_transition_ablation_pairs.py
```

The 336-row result is local and ignored at `reports/openplay_action_value_walkforward/context_ablation_paired_transition_differences.csv`. It contains aggregate scope rows for the pooled sample, each league, each season, and each league-season cell; no event or player-level scores are written.

Reproduce the ablations and their match-cluster intervals in Windows PowerShell:

```powershell
py scripts\run_openplay_event_type_ablation.py
py scripts\summarize_openplay_event_type_ablation.py
py scripts\run_openplay_context_ablation.py
py scripts\summarize_openplay_context_ablation.py
```

The generated fold metrics, match summaries, and interval tables are ignored local outputs under `reports/openplay_action_value_walkforward/`. No paired bootstrap for comparing two ablation models to each other has been generated; the reported fold means and state-model intervals should not be used as that test.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
py scripts\run_openplay_action_value_walkforward.py
```

The run used Python 3.13 directly because the `py` launcher was unavailable in the execution environment. Aggregate outputs and the sampled transition table are written locally under ignored `reports/openplay_action_value_walkforward/`:

- `walkforward_model_comparison.csv`
- `season_transition_summary.csv`
- `league_transition_summary.csv`
- `event_family_transition_summary.csv`
- `sampled_transition_rows.parquet`
- `run.json`

To add match-cluster uncertainty intervals for absolute transition magnitudes without rerunning the model:

```powershell
py scripts\summarize_openplay_transition_uncertainty.py
```

This writes `transition_uncertainty.csv` locally. Bootstrap resampling is by match so the two team perspectives and repeated sampled events within a match stay clustered. The output has 192 rows: four transition summaries across seven seasons, five league aggregates, 35 league-season cells, and the pooled sample.
