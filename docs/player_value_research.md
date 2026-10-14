# Player value: research options for FutWAR

## Owner direction added 2026-10-10

The owner requested three graph reference options—overall average, league average, and the selected team's feasible replacement—and confirmed both a position-locked and any-position scope for every option (six views total). In the any-position view, replacement candidates may qualify through multiple roles when each role has at least five appearances and at least 10% of appearances. The scope switch changes replacement eligibility; player value must already be calibrated to a common outcome scale. See [the detailed architecture and decision record](war_model_architecture.md) and its [six-view diagram](../reports/war_research/war_comparison_matrix.svg).

Method note: all-five-league and league averages are useful benchmarks, but subtracting an average yields above-average contribution, not baseball WAR. The team-feasible replacement is the only one of these three that could support a literal above-replacement label, after historical availability, affordability and contribution estimates are validated. Show the three comparisons as requested while keeping labels methodologically accurate.

The owner does not want goals/assists to swamp the score. Do not force this by hand-downweighting goals. Test a single action-value/expected-outcome model that includes scoring and prevention, avoid adding overlapping goal/assist/xG/creation terms as independent bonuses, and test whether defensive, progression and goalkeeper features add out-of-sample information. No weights are adopted.

Research reviewed on 2026-10-10. The owner subsequently confirmed replacement-level comparison, following baseball WAR. Methods below remain proposals for discussion; no model or formula is finalized.

## The owner's question

How valuable was this player to the team, and how much would the team suffer if a readily available replacement-level player took the same minutes? Value should include useful contributions beyond goals and assists, without tuning rankings to force equal representation of positions. Keep the descriptive position analysis separate from contribution estimation.

The owner explicitly chose replacement level and withdrew the average-player comparison on 2026-10-10. [FanGraphs explains](https://library.fangraphs.com/the-beginners-guide-to-replacement-level/) replacement as a readily available alternative. FutWAR will follow that comparison principle; the soccer replacement pool and its estimated performance still require research and discussion. No percentile, minutes threshold or automatic classification of reserves has been chosen.

## Methods worth learning from

| Research | Useful idea for FutWAR | Required evidence / main limitation |
|---|---|---|
| [Baseball WAR](https://library.fangraphs.com/misc/war/) | Put distinct contributions on an outcome scale, subtract a defined baseline and account for playing time | Baseball coefficients and positional adjustments cannot simply be imported into soccer |
| [Sill's basketball adjusted plus-minus research](https://www.sloansportsconference.com/research-papers/improved-nba-adjusted-using-regularization-and-out-of-sample-testing) | Regularize player estimates and select modeling details through predictions on games outside training | Need who played together and against whom; correlated teammates make attribution difficult |
| [Schuckers et al., design-weighted adjusted plus-minus](https://myslu.stlawu.edu/~msch/DWRAPMFeb2019.pdf) | Research across basketball, hockey and American football distinguishes presence from involvement; contextual weights require validation | Weighting involvement can change coefficient scales and overfit; not a license to assign favored positions extra credit |
| [VAEP: Decroos et al.](https://arxiv.org/abs/1802.07127) | Value on-ball actions through changes in scoring and conceding probabilities, allowing offensive and defensive contributions | Needs ordered, located events; unrecorded off-ball prevention remains difficult |
| [American Soccer Analysis goals added](https://www.americansocceranalysis.com/home/2020/5/4/goals-added-deep-dive-methodology) | Value possession changes, including receiving and interrupting play; examine allocation of shared credit | Receiving credit and finishing/penalty treatment involve methodological choices; do not copy them without discussing their fit to observed seasonal contribution |
| [Soccer plus-minus: Kharrat, López Peña and McHale](https://arxiv.org/abs/1706.04943) | Study goal-difference and expected-points variants in soccer | Need verified lineup intervals and context; model associations do not by themselves prove the effect of an actual substitution |
| [Soccer eLPAR / Skellam regression](https://arxiv.org/abs/1807.07536) | Connect positional team inputs to goal outcomes and expected league points relative to a replacement scenario | Uses FIFA video-game ratings and positional line averages; its input ratings do not measure our players' observed seasonal contributions |

Sill's conference abstract supports regularization and future-game validation. This first review does not reproduce the studies or establish that any method works on FutWAR's data. Event action values and plus-minus estimates answer related but different questions; neither automatically equals above-replacement value.

## A possible research structure, subject to discussion

1. Define the replacement pool and the scenario: position/role, competition, minutes, teammates, opponents and whether the tactical system stays fixed. A comparator must be able to perform the position being replaced.
2. Estimate contributions to scoring and preventing concessions. Event-based methods explain recorded actions; lineup-based methods offer a complementary view of team outcomes. Test these separately before considering a combined method. Do not simply add their overlapping estimates.
3. Estimate outcomes under the stated comparison scenario. A conceptual target is expected team points with the player minus expected team points with the comparator. This describes the question, not an implemented formula or a claim of causal identification.
4. Calibrate goal distributions to match outcomes. Expected points are `3 * P(win) + P(draw)`; the value of a change in expected goals depends on the starting match context. A single universal goals-to-points multiplier is a hypothesis to test, not a settled rule.
5. Report seasonal value, per-90 value and uncertainty. Test future seasons and simpler baselines; check sensitivity to comparator definitions, position assumptions and playing time.

## How to recognize smaller contributions

Examples to investigate include a pass that improves a possession, receiving in a useful location, an interception that reduces conceding danger, a recovery that creates a counterattack, and the cost of losing possession. These are hypotheses about value, not additional fixed bonuses. Location, difficulty, pressure, possession opportunities and subsequent state matter when available.

A defender who prevents a pass from being attempted may have no recorded event. Tracking data or outcome-based evidence may help, but we must retain the uncertainty rather than fabricate defensive credit. More tackles or passes do not necessarily mean more value.

Avoid counting the same attacking sequence repeatedly by stacking goals, assists, xG, xA, xAG and creation statistics at full value. Correlated measurements can inform a model, but credit allocation must be explicit. Do not suppress genuine goals merely to balance the leaderboard. Finishing skill, realized finishing outcomes and repeatability are separate issues to discuss for a retrospective seasonal measure.

## What our current data support

The audited player-team-season CSV supports position-specific descriptions and candidate-feature research. Match scores and standings checks support team-outcome analysis. The appearance-source audit and five-player identity pilot are useful groundwork; they do not establish complete, verified lineup intervals, event sequences or tracking coverage.

Season totals cannot reconstruct the before-and-after state of a pass or the complete players on the pitch at every goal. A season-level statistical prototype would therefore have narrower attribution claims than a rich event/lineup model. A smaller, explicitly bounded event-data pilot is an option, alongside the full eight-season descriptive analysis; its source, access terms and actual coverage must be audited before choosing it.

## Decisions to discuss before modeling

- Which observable pool represents readily available replacement-level players, and how should its performance be estimated across positions, competitions and seasons?
- Keep teammates/system fixed in the comparison, or model adaptation? The latter requires substantially stronger evidence.
- Compare event-based and lineup-based approaches in a limited rich-data sample, or first build a constrained prototype from broad season totals?
- How should realized finishing be credited for the retrospective objective, distinct from forecasting future ability?

No weights, position buckets, replacement thresholds, COVID exclusions or additional source acquisitions are approved by this note.

The [replacement-baseline evidence review](replacement_baseline_research.md) compares candidate pools, documents current data limitations and identifies the next choice for the owner. No candidate pool has been adopted.

The owner approved a small documented-acquisition pilot and subsequently raised club resources, academy/free-agent alternatives, small-sample rates and league context. The [four-case evidence review](replacement_candidate_pilot.md) records these concerns and open modeling choices; no club-budget baseline, shrinkage estimator or league adjustment has been selected.

The owner subsequently approved a shared replacement standard for core FutWAR and a separate club-specific replacement comparison. Budget-dependent comparators must not silently change core FutWAR values. The numerical common standard and any position/league/season structure remain open.

Further owner decisions include goalkeepers through a separate contribution method, and specific historical position labels with secondary positions requiring both five appearances and 10% of appearances. See [the position and keeper requirements](position_evidence_requirements.md) and [expanded candidate evidence](replacement_candidate_expansion.md). These decisions do not establish replacement eligibility, model weights or a common cross-position outcome calibration.
