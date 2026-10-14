# FutWAR contribution model: current design proposal

This is a research design, not a fitted score. It records the owner's instruction to focus development on WAR and its comparison graphs before returning to the website. The owner confirmed the three baseline choices crossed with a separate position-scope switch, giving six comparisons.

## What is being compared

One player contribution estimate must be on a shared outcome scale before players at different positions can be compared. The graph will offer three reference settings and two eligibility settings:

| Reference setting | Position locked | Any evidenced position |
|---|---|---|
| All-five-league average | same specific position and season | any eligible position in that season |
| Selected-league average | same specific position, league and season | any eligible position in that league-season |
| Team-accessible replacement | club, season-start resources and availability; same specific position | club, season-start resources and availability; any eligible position |

The first two are **above-average benchmarks**. Subtracting an average does not, by itself, produce baseball-style WAR. The team-accessible option is the candidate replacement-level WAR comparison, if we can document a feasible historical pool. The graph can compare all three against one contribution estimate, but labels and units must preserve this distinction. This is a statistical distinction, not a change to the requested three graph options.

For a given player-season and reference scenario:

`per-90 difference = estimated contribution per 90 − reference contribution per 90`

`season total = per-90 difference × the player's observed minutes / 90`

For a multi-season selection, estimate each year against its own baseline and then add totals. Never apply today's budget or a different year's average retroactively. Team affordability/availability is frozen at season start; January recruitment is a separate scenario. Estimating the player's impact *during* a season can use that season's observed output. Forecasting what a team could have recruited at the start must predict replacement performance using only information known then, not the recruit's future actual season.

## Position eligibility

**Locked:** the replacement candidate must share the player's verified main position for that player-season. The owner's exact position vocabulary is GK, RB, RWB, CB, LB, LWB, CM, CDM, CAM, LM, RM, ST, LW and RW. Similar-sounding roles are not interchangeable without a separately defined flexible view.

**Flexible:** a candidate may qualify through any verified position. A meaningful secondary role must have at least five appearances and be at least 10% of total appearances. Candidate exposure still needs reliability checks; these position-label cutoffs do not define playing-time reliability or replacement eligibility. Goalkeepers need a separate contribution estimator, but must reach the same expected-goal/points outcome scale before entering the all-position comparison. Until that common scale exists, a cross-position WAR graph is a design target, not a valid numerical ranking.

Main position is selected by greatest evidenced minutes over the player-season. Ties, incomplete match coverage and unresolved role spells remain unknown. Current profile labels and broad CSV labels MF/DF/FW cannot replace this evidence.

## Contribution estimate: test actions before adding bonuses

The preferred first rich-data estimator is a bottom-up, context-aware action-value model. For each action, estimate the change in the acting team's probability of scoring and conceding over one consistent horizon:

`action value = (P(score after) − P(score before)) − (P(concede after) − P(concede before))`

Sum credited action values over each player's minutes, then calibrate the aggregate to observed goals or match points. This follows the rationale of [VAEP](https://arxiv.org/abs/1802.07127): assess actions in their context rather than treating goals, assists or counts as the whole contribution. [American Soccer Analysis's goals-added work](https://www.americansocceranalysis.com/home/2020/5/4/goals-added-deep-dive-methodology) offers a related possession-value approach. Neither set of coefficients is imported.

Goals matter because they change the scoreboard and win probability. They should not be given a hand-written downweight to make the leaderboard look balanced. Instead, avoid counting the same attacking sequence several times by summing goals + assists + xG + xA + xAG + chance-creation totals as separate full-value bonuses. A shot's expected chance, its realized goal, and the earlier actions that created it need an explicit shared-credit policy. The outcome-calibration stage should measure whether a component adds information after the preceding components.

Candidate action domains are chance creation/finishing, progression/retention, recoveries/interceptions/duels/blocks, and goalkeeper shot-stopping/distribution/sweeping. A tackle, recovery or progressive pass is not automatically a positive bonus: its location, success, possession change and later danger matter. Missing off-ball defending must be disclosed as a blind spot. A goalkeeper method should separate shot difficulty, shot outcome and distribution so the same saved danger is not credited twice; [ASA's keeper goals-added work](https://www.americansocceranalysis.com/home/2021/6/20/valuing-goalkeepers-with-goals-added) is a design reference.

The proposed common endpoint is expected league points. For each match, predict goal distributions and calculate `3 × P(win) + P(draw)` under the player's estimated contribution and under the specific reference. The difference across matches is the points-above-reference candidate. The effect of a goal or action depends on match state, opponent and score; there is no justified universal goals-to-points multiplier. [The eLPAR study](https://arxiv.org/abs/1807.07536) shows a points-based positional approach, but used FIFA player ratings and broad lines; we will not copy its inputs, positional weights or replacement percentile.

### Candidate equation to test, not an approved formula

The most direct outcome-scale prototype is **expected points added (EPA)** at each event state:

`EP_c(s) = 3 × P(c wins | state s) + P(match draws | state s)`

`EPA(p, a) = EP_p-team(state after action a) − EP_p-team(state before action a)`

`observed contribution(p, season) = sum of EPA(p, a) across that player's recorded actions`

This makes goals valuable through the change in the modeled match outcome, without hand-tuning a goal coefficient or adding goals, assists, xG and xA as separate bonuses. Defensive actions and goalkeeper actions can also gain value when the state transition changes their team's expected result. Negative actions can lower it. This is a value-of-the-observed-action estimate, not automatically a causal estimate of what would happen if that player were removed; action sequence, score state, substitutions, off-ball work and opponent response remain important.

For reference `r`, the season comparison would then be:

`difference_r = observed contribution(p, season) − expected contribution(r, same exposure)`

The six views change only reference eligibility: three user-selected reference settings crossed with specific-position locked or evidenced any-position pools. For the flexible pool, a secondary position must still meet the user's five-appearance/10% rule. The overall and league averages are above-average comparisons; the club's preseason affordable/available pool is the only proposed replacement-level baseline. A season-total graph can plot the differences in expected league points; a per-90 view can plot the corresponding rate. Empty/unknown bars must remain unknown where inputs or pool coverage fail.

Turning this candidate into player value needs a match-state model validated by match and season, with score, remaining time, home advantage and pre-match team strength. The one-season pilot below is a preliminary test, not that validation. It also needs a rule for which player receives an action's credit and how multi-action build-up sequences share credit. The earlier 2017–18 danger model is a prerequisite diagnostic only: its ten-event score/concede probabilities are not the win/draw probabilities required by this equation. Both crediting routes remain open for discussion.

## Two estimation tracks and overlap control

1. **Action track:** score event states before/after actions, with offensive and defensive danger on one goal-probability scale. Tests whether contributions beyond goals/assists are measured.
2. **Lineup/team-outcome track:** estimate how goal difference or expected points change with player presence while accounting for teammates, opponents, venue, score and role. This needs verified playing intervals and substantial regularization because players share the pitch and are selected non-randomly.

These tracks are alternative evidence about related impact. Do not add their full estimates together. Compare rankings, predictions and uncertainty; combine only if an out-of-sample model demonstrates distinct information without double-counting. A 2026 restricted-Shapley paper offers a way to allocate shared shot-action credit and bootstrap uncertainty, but its available analysis covers one Italian season, excludes keepers, and explicitly warns that raw values vary with participation/support. It is a pilot candidate, not a universal solution: [Cefis, Metulini and Carpita](https://arxiv.org/abs/2603.11016).

## Stabilization, league context, validation

Per-90 rates from one-minute/small-exposure stints can be extreme. Do not solve this by labeling every low-minute player a replacement or by hiding them. Estimate reliability using exposure and historical repeatability; fit any shrinkage/partial-pooling parameters on training seasons and show sensitivity. The existing 900-minute display setting remains exploratory, not a model cutoff.

Cross-league comparisons need a common outcome scale, competition/opponent context and validation on transitions between leagues. Do not apply an arbitrary league multiplier or equate a league's internally normalized leaderboard with absolute strength. Keep league strength, player contribution and tactical fit distinct.

Use chronological holdouts: train on earlier seasons, predict a later season, then rotate the held-out year. Test match probabilities/calibration, contribution stability, incremental value beyond goals/assists, role-specific error, out-of-league transfer prediction, keeper-versus-outfield scale agreement and sensitivity to all six comparison settings. Report intervals and coverage alongside ranks. COVID seasons stay in scope, with context decisions open.

## Team budget and availability scenario

For each selected historical club-season, define cost scenarios rather than one vague percentage of club budget: academy/free-agent access, low-cost loans/transfers, and a broader affordable shortlist. Candidate pool membership requires evidence the player was available to that club as of season start, position eligibility, a reliable pre-season performance prediction, and an evidenced annual cost. A possible accounting comparison is annual wages plus amortized fee plus annual agent/signing/loan costs, but it is not cash affordability and needs consistent currencies, gross/net definitions and loan contributions. A free transfer is not free labor. Market value is an estimate, not a fee or a wage. Club-wide employee expenses do not equal the first-team budget.

Average, league and team comparisons answer different questions: general benchmark, competition benchmark, and a club's constrained feasible alternative. Team affordability should not silently change a shared/base WAR rating. Until cost, contract, and availability history is assembled, the team mode should report coverage and uncertainty and leave the numeric baseline unestimated.

## Current data readiness

- Player-season summaries: 22,418 club-season records over all 40 Big Five league-season cells; original source positions are broad and do not establish the specific position minutes required by the locked/flexible scopes.
- Team results/archived tables: 780 club-seasons. These support outcome context, not isolated player causality.
- Match context: 14,359 historical fixtures across 40 league-season cells; one Bundesliga 2024–25 fixture lacks shots/corners/fouls/cards.
- Rich events: 3,071,395 derivative Wyscout events across the five leagues in 2017–18 only. The remaining 35 league-season cells are absent, event IDs are not reconciled to the player-season file, and event tags are not a validated xG/PSxG feed. A one-season final-match-points state prototype is fitted; it is not a player-value model.
- Match-position records have broad coverage in an archived provider export, but played-position meaning is explicitly not verified. The project's independent six-match pilot does not establish all-season role coverage.
- Historical player wages, team recruitment budgets, contract/availability candidate histories and academy/free-agent pools are not assembled. The third baseline is not yet computable.
- GK is a separate performance-estimation domain. Comparable historical shot-level post-shot xG and distribution evidence is insufficient for eight-season coverage.

## First event-danger model check (2026-10-11)

The licensed Wyscout 2017–18 event archive passed a bounded chronological prediction pilot: 1,825 fixtures were score-reconciled and included, one of 1,826 was excluded for a goal mismatch, and 1,011,664 complete sampled event states were available. The model using event history/context reduced held-out March–May error against a constant-rate forecast for both score and concede events in the next ten raw events in all five leagues. Pooled Brier error fell 2.57% for scoring and 2.04% for conceding; log loss fell 10.48% and 12.68%. The gain is predictive evidence, not causal player impact. States overlap inside fixtures, labels are rare, and this is one season. Exact tables, calibration and exclusions are in `reports/event_value_pilot/results.md`.

The diagnostic found three out-of-range coordinate points; derived coordinate features are set missing, while the licensed raw source stays unchanged. One match with a goal-tag/score discrepancy is excluded and documented. The feature-history model outperforms the constant-rate model in the pooled held-out sample, but that alone does not select a feature set, action horizon, player-credit policy or WAR formula.

## Expected-points action-state pilot (2026-10-11)

The first expected-points model estimates final match points for each event team from pre/post event states. On the March–May 2018 chronological holdout, the event-context tree slightly improved pooled prediction over the simpler score/time/form tree, but an exploratory smooth score-state model performed best (RMSE 0.9700, three-class Brier 0.4361, log loss 0.7506). The smooth model was added after the original holdout had been inspected, so this is model development on a reused test window, not a fair final comparison. See the full [pilot report](../reports/expected_points_pilot/results.md).

The exploratory pre/post prediction difference has median zero and mean −0.0017 points across 306,752 sampled held-out action pairs. After correcting a sample-ID alignment bug in the event-label export, 414 sampled goal shots average +0.604 points and 94.9% are positive. The event-context model nonetheless underperforms an exploratory smooth score-state benchmark on this test window; because that benchmark was added after inspecting the test result, a new holdout is needed for a fair comparison. The `playerId` field is populated but 23,094 rows use sentinel 0 and are not attributable to a player. These state changes are not causal effects and must not be summed as player value: events overlap, off-ball work is missing, and no replacement player is modeled. See the [event-type diagnostic](../reports/expected_points_pilot/action_type_diagnostics.md) and the [direct/shared shot-sequence comparison](../reports/action_credit_pilot/results.md). Event-level attribution and replacement remain open research decisions. The pilot is one season and is not calibrated across seasons, roles, keepers or league transitions.

Next: audit actual match/event availability in the later, selected StatsBomb seasons, then decide whether the sample can support a limited cross-provider stress test of the score-state benchmark. StatsBomb's catalog is not a continuous Big Five panel, so it cannot by itself provide representative chronological validation. If coverage is adequate, measure calibration and error by season and competition before comparing event-context features. Then discuss action allocation before producing player totals. No coefficients, credit allocation, or WAR formula are approved. Details are in [the external-validation source review](expected_points_external_validation.md).

## Direct versus shared action credit

The [action-credit comparison](action_credit_comparison.md) summarizes direct actor credit, shared shot/possession allocation and a complementary possession plus-minus validation route. The same-sequence pilot in [`reports/action_credit_pilot/results.md`](../reports/action_credit_pilot/results.md) compares direct credit with a transparent equal-participant benchmark on 11,693 complete-actor shot-ending sequence proxies. The two methods conserve the same aggregate but have materially different player rankings. Equal split is not Shapley, the sequence rules are unvalidated, and source IDs are not linked to multi-season player-seasons. This one-season attacking result does not choose the all-position method or establish WAR.

## Historical team-budget source leads

UEFA's public finance reports provide selected club comparisons (including top-25 financial lists and selected cross-year comparisons); UEFA also describes a curated finance database of more than 700 clubs over 15 years, including player and non-player wages. The public report is not equivalent to open, complete club-by-club data for all 40 league-season cells. No download or transcription was made for this work. [UEFA report](https://ecfil.uefa.com/2024), [UEFA database description](https://intellcentrecatalogue.uefa.com/club-costs-and-financial-performance/).

Capology may help identify salary ranges but warns all salary amounts are estimates, offers bulk historical API data only through a paid subscription, and says API data cannot be published without a publishing license. Its terms restrict use to private, non-commercial purposes unless separately approved. Therefore it is not being used for bulk collection or public website data. [Capology data-quality/support page](https://capology.com/support/), [API plans](https://www.capology.com/pricing/api-plans/), [terms](https://www.capology.com/terms-and-conditions).

## Graphs prepared

`reports/war_research/war_comparison_matrix.svg` maps the six requested views. `data_readiness_by_season.svg` shows why the team-budget and flexible-position comparisons remain research designs rather than scores. Local-only event-pilot figures visualize the bounded held-out prediction check and predicted-versus-observed event rates; row-level model outputs and generated plots are not committed. None contains player WAR values.

## Decisions already recorded / still open

Recorded: the three requested baselines; average and league values use the selected season; team resources and availability are assessed at season start with January separate; each season is compared against its own reference before multi-year totals; locked and flexible position scopes cross all three baselines; meaningful secondary roles meet five appearances and 10%; the all-position outcome scale must be common; no WAR coefficients are final.

Still for discussion after the pilot makes tradeoffs concrete: how to credit a finished shot versus its build-up, how to combine or compare event and lineup estimates, how to calibrate goals into match points, what evidence defines a historically feasible team shortlist, and the exact uncertainty/shrinkage presentation. Do not finalize these by convention.
