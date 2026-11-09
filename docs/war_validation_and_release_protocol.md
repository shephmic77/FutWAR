# FutWAR validation and release protocol

**Status:** research protocol for the owner's review. This documents how to test future candidate methods; it does not select a formula, weights, player-credit rule, position conversion, or replacement pool.

## Current evidence snapshot — 2026-11-05

The event foundation is no longer limited to one season. The pinned OpenPlay v0.1.0 release covers all 40 Big Five league-season cells from 2017–18 through 2024–25, with event files for 14,334 of 14,360 listed fixtures. Twenty-six fixtures have no event file, ten matches have source issues, and the release audit found additional actor, identity, lineup, and event-key exceptions. The OpenPlay release labels its data CC BY 4.0 and requests attribution; see the [release audit](openplay_release_audit_2026-11-04.md) for the source and local integrity checks. This records the publisher's license declaration, not an independent legal opinion.

A chronological expected-points state benchmark and event-context comparison have now been evaluated across seven later-season folds. Event context improves mean Brier score only slightly and inconsistently, while its predicted transition magnitude is much larger and feature-sensitive. The result is a team-state forecast diagnostic, not validated action value. The 2024–25 fold has been used during method development and is not an untouched final test. See [the OpenPlay walk-forward report](openplay_action_value_walkforward_2026-11-05.md).

A paired match bootstrap confirms the sensitivity: on 12,504 shared fixtures, removing coarse location, event type, or outcome lowers the event-context transition scale in all five leagues, but even the location-free residual remains about 13 times the state-only residual. This does not identify a preferred feature set or validate an action-value scale; the comparison is conditional on fitted models.

A separate seven-fold lineup-presence walk-forward tests match-level player identity features. On 14,328 valid matches, adding either the starting XI or realized player-minute exposure increased expected-points log loss in every held-out season at the fixed exploratory shrinkage setting. Earlier-season-only shrinkage selection moved the average lineup difference close to zero, with mixed fold directions and only a small number of intervals favoring lineup information. This is evidence that the simple lineup signal has no reliable incremental value at present; it is not the required action-plus-lineup comparison because the current action signal is not a validated continuous player-match input. See [lineup-presence walk-forward](openplay_lineup_presence_walkforward_2026-11-05.md).

Player WAR is still not ready for publication. After the 2026-11-06 club-alias update, the strict exact-key plus equal-appearance candidate screen covers 90.2% of player-season rows (20,227 / 22,417); 2,190 remain flagged and the expanded candidate set has not been independently precision-validated. Historical minutes in the owner's specific positions are incomplete; goalkeeper interval assignments have coverage but no representative independent accuracy check or common-scale model; and the season-specific team-accessible replacement pool is not available. This protocol now governs the multi-season OpenPlay foundation and identifies which remaining gates block a player score.

## 1. Keep the research quantities separate

Report these as distinct quantities during development:

1. **Match-state forecast:** probability of win/draw/loss and expected points (0/1/3) from a clearly defined match state.
2. **Team-event transition:** change in both teams' expected-points outlook across a recorded event. This remains a team-level value until actor attribution is validated.
3. **Player action contribution:** only the portion assigned under an explicitly compared credit method, with match-cluster uncertainty and exposure shown.
4. **Adjusted lineup signal:** the incremental held-out information in player presence after the action model, not a second copy of value already explained by actions.
5. **Teammate uplift:** a separate estimate of whether the same teammates' goal-difference or expected-points contribution differs with the focal player present; exploratory until confounding and overlap are addressed.
6. **Above-baseline comparison:** the player's contribution compared with one of the six owner-requested season-specific references. A same-position average is an above-average benchmark, not a literal replacement level.

Expected points is the primary target currently requested for the next prototype. Expected goal difference remains a separately reported check. Neither is a finalized FutWAR unit or player score.

## 2. Chronological evaluation protocol

### Data split

- Group all observations from a fixture together, including both team perspectives and every event in the match. Never split rows from one match across train and evaluation sets.
- Use earlier seasons for training, the next season for model and feature decisions, and the latest untouched season for the final report. With sufficient seasons, rotate the development/validation boundary as a sensitivity analysis, but keep a final season untouched until the method is frozen.
- Any transformation, imputation, scaling, feature selection, shrinkage choice, calibration, and hyperparameter selection must be fitted using training data only. Pre-match opponent strength and form may use only results available before kickoff.
- Do not use a same-season held-out league result as a substitute for future-season validation. Report it as cross-league transfer evidence only.

### Forecast candidates and scorecard

Compare on the same fixtures and target construction:

| Candidate | Inputs | Role in comparison |
|---|---|---|
| Context baseline | Score, clock, venue and pre-match strength where available | Minimum forecast benchmark |
| Event-context candidate | Context plus event-state information | Tests whether recorded event context improves forecasts |
| Transparent state-value candidate | Documented context buckets with values derived from training-fold outcome frequencies or a documented owner-approved table | Interpretable benchmark; no values are copied from raw one-season event means |
| Adjusted-lineup candidate | Context plus shrinkage-controlled player-presence features | Aggregate feasibility comparator; not itself player WAR |
| Incremental combined candidate | Out-of-fold action signal plus only the lineup information that improves on action-only forecasts | Tests the owner's “lineup adds what actions miss” principle |

Score expected-points forecasts with multiclass log loss, multiclass Brier score, mean absolute expected-points error, and calibration. Score goal-difference forecasts separately with MAE/RMSE and calibration by predicted range. Show results by league, season, home/away, score state, and red-card state where sample sizes allow. Use paired match-cluster bootstrap intervals; for final uncertainty, refit the complete modeling pipeline within each resample or report that training uncertainty is omitted.

No single metric or favorable fold is sufficient. Report the full held-out scorecard and uncertainty, compare to the context baseline, and retain weaker or mixed results in the report.

## 3. Action accounting and sensitivity

- Reconstruct a complete, ordered event path from the full archive before evaluating action deltas. The every-third-event pilot is not a complete action sequence.
- For team A, define a state transition as `EP_A(after) - EP_A(before)`. For a paired team-level outlook, calculate the change for both teams on the same before/after state and report the pair once. Do not sum two separately counted team benefits as though they were independent.
- Preserve `playerId=0` in state reconstruction but do not assign it to a player. Interruption stays context/state-only, including rare nonzero IDs, per the owner's decision.
- Compare direct actor attribution with alternative shared-credit candidates only on events where identity and participant roles are evidenced. The existing equal-participant split is a sensitivity benchmark, not a validated method or Shapley allocation.
- Compare full state transition with clock-adjusted residual as separate sensitivity views. The latter depends on a hypothetical clock-only forecast and is not automatically more causal.
- Evaluate 3-, 5-, and 10-event horizons on chronological validation matches, with match boundaries and shortened windows explicit. The coverage audit confirms complete windows are available in all 14,330 included fixtures, but does not validate the horizon values. Horizons overlap; endpoint changes cannot be added across actions or read as isolated action effects. See the [full window-availability audit](openplay_action_horizon_coverage_2026-11-05.md).
- The eight-season endpoint sensitivity now reports all three horizons on 12,504 shared future-season fixtures. Mean absolute clock-adjusted residuals rise from 3 to 10 rows for both state-only and event-context forecasts; the event-context scale remains materially larger. These transitions still bundle intervening events from both teams and depend on a hypothetical clock-only comparator. They are diagnostics, not action prices or player credits. The final 2024–25 fold has been used in method development and is not an untouched final test. See [the multi-season horizon sensitivity](openplay_action_horizon_sensitivity_2026-11-05.md).
- Show action-credit results with player-ID coverage, event-family coverage, exposure, and rank/value uncertainty. Keep team-level swings and player-level credited values in separate tables.

The earlier 2017–18 tests do not meet these conditions for a player season score. The newer multi-season OpenPlay forecasts add chronological match holdouts, but they still do not validate player action value, actor credit, or player-season totals. Some transition samples are thinned, and actor identity links remain unresolved for a substantial share of player-season rows.

## 4. Lineup and teammate components

### Incremental lineup information

Use identical fixtures, chronological folds, and outcome definitions for context-only, action-only, lineup-only, and action-plus-lineup comparisons. Generate action forecasts out of fold so a downstream lineup model cannot learn from in-sample action residuals. The candidate lineup term must improve held-out prediction beyond action-only and remain stable across reasonable shrinkage settings and leagues. If it does not, omit it from the candidate combined score. Do not translate raw plus/minus coefficients directly into player points.

The multi-season lineup result now complements the earlier one-season feasibility check. At fixed exploratory shrinkage, starting-XI identity and realized-minute features worsened held-out prediction in all seven seasons. In an earlier-season-only shrinkage sensitivity, the mean changes were near zero and inconsistent; that small, single-inner-season tuning procedure is itself uncertain. This remains a match-level association check, confounded by selection, club strength, tactics, and availability; it is neither an individual causal estimate nor the requested action-plus-lineup residual test. A future candidate must show incremental held-out value beyond out-of-fold action predictions, under nested temporal shrinkage selection, before it can be considered for the combined score. See the [full multi-season report](openplay_lineup_presence_walkforward_2026-11-05.md).

### Teammate uplift

Compare both previously requested approaches: (a) within-teammate with/without exposure, and (b) adjusted player-by-teammate interaction. Use the same teammate outcome tied to expected points or goal difference, adjust for opponent and match state, report support/overlap by player pair, and use match-cluster uncertainty. Treat the estimates as associations unless a credible causal design is established. Keep this component separately visible until evidence shows how it overlaps with action and lineup signals; do not add it mechanically.

The current eight-season OpenPlay audit is support-only: at least one same-team source-ID pair-season meets each tested 90/180/450/900-minute cutoff in all 780 club-seasons. It provides no teammate-performance or uplift estimate, and the source IDs are not independently verified. See the [eight-season overlap report](openplay_teammate_uplift_overlap_2026-11-05.md); keep the earlier one-season Wyscout support audit separate.

## 5. Six comparison views: readiness rules

| Baseline | Position-locked | Any evidenced position |
|---|---|---|
| Same-position average across all five leagues | Requires season-specific role evidence and a comparable contribution signal; label as an average benchmark | Also requires evidenced secondary positions and the owner's five-appearance/10% eligibility rule |
| Same-position average in a selected league | Same requirements, restricted to that league-season | Same requirements plus evidenced secondary roles |
| Team-accessible typical feasible option | Requires season-specific candidate availability and annualized total cost; unknown-cost candidates are excluded from the central pool | Also requires documented accessibility and any-role evidence on a common scale |

Use only information available for the season being evaluated. For the team-accessible view, an actual move or documented availability is required as access evidence; do not infer that a player was affordable from market value alone. Compare candidate-pool summaries (minutes-weighted mean and robust alternatives) before the owner chooses one. Count exclusions at the tested minimum-exposure thresholds; none is approved yet.

These are six comparison views, not six finalized formulas. Do not average them into one player number until the owner reviews whether the baselines share a meaningful scale and whether the average obscures the distinction between above-average and replacement comparisons. Goalkeepers require their own model and a demonstrated bridge to a shared scale before outfield comparison.

## 6. Player attribution and uncertainty gates

Before making a player-level result:

- Verify event actor IDs against match lineups and the player-season identity map; report match-level precision/recall from a reviewed sample rather than assuming provider IDs are correct.
- Reconcile transfers, club-season stints, substitutions, and minutes. Preserve unresolved identities as unresolved and do not aggregate them into career/player totals.
- Keep appearance/event IDs, source player IDs, profile IDs, and canonical player IDs distinct until an evidence-backed crosswalk exists.
- Quantify uncertainty from fixture resampling, model refits, player exposure, attribution alternatives, and replacement-cohort construction. A standard error conditional on one fitted model is not full WAR uncertainty.
- Use player-score or ranking summaries only where the evaluation and identity gates pass; show interval/coverage warnings alongside any eventual score.

## 7. Website release gate

Until the gates above pass, the website may show aggregate pilot diagnostics, data coverage, definitions, uncertainty and limitations. It must not show a player's WAR number, a WAR ranking, or a default mean of six comparisons. A future display should name the selected baseline and scope, show per-90 and season total separately, expose playing time and uncertainty, and link the method and source evidence. Do not call an above-average comparison “replacement WAR.”

### Release checklist

- [ ] At least one suitable later-season event source passes terms, coverage, schema, and identity audit.
- [ ] Chronological held-out evaluation is untouched until candidate choices are frozen.
- [ ] Expected-points and goal-difference results, calibration, league breakdowns, and match-cluster uncertainty are reported.
- [ ] Action-only versus action-plus-lineup incremental comparison is completed on identical fixtures.
- [ ] Teammate-uplift approaches and overlap are compared without causal overclaiming.
- [ ] Actor attribution and player-season identity precision are measured and meet a pre-agreed bar.
- [ ] Six baseline cohorts are season-appropriate and exclusions/cost unknowns are visible.
- [ ] Goalkeeper scale is separately validated before cross-position aggregation.
- [ ] Owner reviews and approves the remaining formula, credit, position, baseline, and display choices.

## Current disposition

Earlier one-season evidence remains in [WAR research execution review](war_research_execution_2026-11-03.md), [action-credit comparison](action_credit_comparison.md), [adjusted-lineup feasibility](adjusted_lineup_feasibility_2026-11-03.md), and [the Wyscout teammate-overlap audit](teammate_uplift_overlap_2026-11-03.md). The current multi-season source audit and player-model gates are summarized in [the OpenPlay release audit](openplay_release_audit_2026-11-04.md), the [eight-season teammate-overlap report](openplay_teammate_uplift_overlap_2026-11-05.md), and [project status](project_status.md).

The next data-dependent work is not finding a second event source merely to fill fixture count. First finish the identity and attribution review, resolve position-minute and goalkeeper validation, establish a season-specific feasible replacement pool or keep that comparison unavailable, and reserve a final untouched season after candidate choices are frozen. A source with a compatible schema but no suitable rights, identity quality, or target coverage does not clear these gates.
