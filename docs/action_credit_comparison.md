# Player-credit approaches for expected-points action values

Status: research comparison only. No action-credit policy or WAR formula is approved.

## The two approaches

| Design question | Direct actor credit | Shared possession/shot-sequence credit |
| --- | --- | --- |
| Unit scored | One action and its before/after state change | A possession or shot-ending sequence as a cooperative unit |
| Initial recipient | The player recorded as performing the action | The players included in the sequence's eligible coalition |
| Main strength | Clear audit trail from event to player; can include passes, duels, recoveries, shots, saves and other coded actions | Represents the fact that a shot's quality can depend on several players' preceding actions; reduces the assumption that only the final actor made the sequence valuable |
| Main weakness | Sees on-ball activity only; a sequence can make several actions look valuable, and off-ball work is unobserved | Requires explicit sequence boundaries, participant rules and a defensible counterfactual value for coalitions; a shot-focused version leaves most defending, goalkeeping and non-shot actions outside its scope |
| Data need | Ordered events, action actor, team, time and state features | Everything in the direct method, plus stable possession/sequence construction and repeated participant coalitions; tracking helps include off-ball players |
| Current FutWAR fit | Possible as a transparent diagnostic after identity linking and model improvement | Possible as a bounded shot-creation sensitivity study; not ready as the universal player-credit layer |

## What the methods literature contributes

VAEP defines an action as a transition between adjacent game states and values it by the change in a modelled state value. This gives an auditable direct-actor starting point and can cover more than shots and goals. Its familiar published target is near-term scoring/conceding danger, however, whereas FutWAR is testing final match points. VAEP's action values should not be treated as a ready-made points model or as proof of causal impact. See [Decroos et al., *Actions Speak Louder Than Goals*](https://arxiv.org/abs/1802.07127) and the [IJCAI explanation of adjacent-state action value](https://www.janvanhaaren.be/assets/papers/ijcai-2020-vaep.pdf).

Expected-possession-value research models possession states over a sequence and decomposes value into action components. It demonstrates how a shared sequence can carry value that is not captured by a shot alone, but the cited rich-data framework uses tracking data and estimates scoring/conceding the next goal, not final match points. Our archived Wyscout events do not include full tracking positions for all 22 players. See [Fernández, Bornn and Cervone (2021)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8570314/).

A recent restricted-Shapley study allocates a modelled shot-action worth across tactically admissible player coalitions. Its empirical analysis uses 8,421 shot actions from Serie A 2022–23, focuses on two clubs in its player-credit examples, and excludes goalkeepers. The authors note that raw restricted-Shapley magnitudes are not directly comparable across players because participation and coalition support differ. This is a useful design reference for shared attacking credit, not a validated all-position FutWAR formula. See [Cefis, Metulini and Carpita (2026)](https://arxiv.org/abs/2603.11016) and its [open-access journal version](https://link.springer.com/article/10.1007/s00180-026-01783-x).

A possession-sequence adjusted plus-minus study offers a complementary top-down check: it estimates strengths from possession outcomes and includes both players directly involved and players on the pitch. That can reflect teammate context and some indirect/off-ball influence, but it does not identify which unrecorded movement caused the outcome. The study uses one season of La Liga 2017–18 and a goal/no-goal possession outcome. See [Bajons and Hornik (2025)](https://academic.oup.com/imaman/article/36/3/593/8115468).

## What the first same-sequence pilot found

The follow-up comparison scores every action inside a held-out shot-ending sequence proxy. Of 12,581 proxies in 545 valid March–May 2018 test fixtures, 11,693 (92.9%) had complete actor IDs matching Wyscout player profiles; 888 incomplete sequences were left out of both methods. The eligible sample has 33,659 actions and 1,970 source player IDs. Detailed counts, league summaries, rank sensitivity, and outputs are in [`reports/action_credit_pilot/results.md`](../reports/action_credit_pilot/results.md).

Direct actor totals and the equal-participant split both sum to 788.768 modelled expected-points-change units by construction. Their player ordering correlates at 0.812 overall and 0.881 among the 286 IDs appearing in at least 25 eligible sequences; median absolute rank movement is 171 and 66.5 places, respectively. This demonstrates a material allocation choice, not which ranking is more accurate. The expected-points model only modestly improves held-out prediction over score/time/form, and these action deltas are not causal effects.

The per-event pre/post predictions are not a telescoping path through a single continuous sequence of match states. Therefore their sum is only the shared allocation total for this experiment; it must not be interpreted as expected points created by a player or team.

The separate state-change audit finds a populated `playerId` field on 306,752 held-out sampled rows, but 23,094 values are sentinel `0`, not a player; there are 2,164 distinct nonzero IDs. Across action types the median change is zero, and 37.6% of rows are within ±0.005 points. After correcting row alignment, 414 sampled goal shots average +0.604 points and 94.9% are positive. However, the event-context model underperforms a smooth score-state benchmark on this test window, and that benchmark was introduced after first inspecting the test result. See the corrected [event-type diagnostic](../reports/expected_points_pilot/action_type_diagnostics.md). The current output remains exploratory and is not a meaningful all-action player-credit signal.

The possession boundaries are transparent proxies over raw events, not validated possession IDs. The equal split makes no coalition counterfactual predictions and is not restricted Shapley. IDs have not been reconciled to multi-season player records. This attacking, one-season sample omits most defensive and goalkeeper value and cannot settle the all-position method.

## A fair comparison plan, before selecting either method

1. Improve and validate the expected-points state model on chronological match holdouts; retain a score/time/form baseline and report calibration by league and match state.
2. Resolve event-player IDs to player-seasons with evidence, and validate sequence boundaries against richer match data where available.
3. The first same-sequence diagnostic is complete. A genuine restricted-Shapley follow-up would first need coalition value estimates and explicit admissibility rules; do not substitute an equal split and call it Shapley. A separate defensive/keeper action comparison is also required for the all-position objective.
4. Compare coverage, uncertainty, player rankings, position distributions, correlation with goals/assists, sensitivity to sequence boundaries, and predictive value on held-out team outcomes. A ranking that looks balanced is not itself validation.
5. Keep goalkeeper/defensive action value in a separate diagnostic and compare it on the same points scale. Shot-sequence Shapley alone cannot satisfy FutWAR's all-position goal.

This experiment would compare the implications of the two credit views. It would not settle the user's three baselines, position-locked versus any-position pools, or the final WAR formula.
