# Three season-specific comparisons — research proposal

Status: draft mathematical components and recorded-metric preview, not a fitted or validated FutWAR formula. The owner requested three views. No weights, league-strength adjustment or goal-to-point conversion have been finalized.

## Historical timing decision

All references belong to the season being viewed. The overall and league averages describe that season's observed performance retrospectively. Team-accessible replacement uses resources and availability evidenced at **season start**; January is a separate scenario. A full-season average budget could incorporate later sales, investment or contract changes unavailable at the original decision date. The owner asked whether seasonal averaging was preferable and authorized season start if not.

A combined period first subtracts each season/club stint's own reference, then adds the differences. Missing historical references remain missing; today's budget or player pool never fills an earlier year. Retrospective season performance may evaluate a historically feasible replacement, but must not be used to select that replacement with hindsight. A forecasting version needs performance predictions trained only on information available then.

## Proposed contribution measurement

For an action, from the same acting team's perspective and prediction horizon:

`action contribution = change in P(scoring) − change in P(conceding)`

This follows [VAEP's action-value framework](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/vaep.html). Fitting the probabilities requires reconciled event sequences, possession changes, terminal goals and period boundaries. The arithmetic helper is not a full VAEP implementation. [American Soccer Analysis goals added](https://www.americansocceranalysis.com/home/2020/5/4/goals-added-deep-dive-methodology) provides a complementary possession-value reference; its coefficients and credit rules are not being imported.

Let `v(i,s)` be a player's estimated contribution per 90 on a common, validated scale. The simplest proposed comparison is:

`difference per 90 = v(i,s) − reference(position, season, comparison)`

`season difference = difference per 90 × observed minutes / 90`

Goals, assists, expected goals and expected assists must not be added as independent bonuses on top of already valued actions. Tackles, recoveries, interceptions, progression, errors and aerial outcomes are candidate explanatory inputs, with action location and opportunity where available. More features do not automatically imply better measurement. Team shots and corners offer context, not the player's exact opportunities or possession denominator.

Keeper shot prevention and distribution need a common scale and separate credit accounting. [ASA's keeper methodology](https://www.americansocceranalysis.com/home/2021/6/20/valuing-goalkeepers-with-goals-added) informs this design. We cannot sum raw saves, PSxG prevention and distribution counts into a defensible overall value.

A future expected-points target is the sum across matches of:

`3 × (P(win with player) − P(win with replacement)) + (P(draw with player) − P(draw with replacement))`

This requires match calibration and a defensible replacement counterfactual, with uncertainty. [eLPAR](https://arxiv.org/abs/1807.07536) motivates examining points rather than an arbitrary score; its FIFA ratings and replacement cutoff are not adopted. No universal goals-to-points multiplier is assumed.

## Three references

1. **Overall average:** same specific position and season across all five leagues. The current preview pools recorded metric rates by provisional player identity and uses an equal-player mean. A final value model must account for league/opponent context; raw pooled rates do not establish absolute player strength.
2. **League average:** same specific position, selected league and season. The graph can show any subset of the five leagues. An average is not a baseball-style replacement baseline, so this view is labeled above average rather than WAR.
3. **Team-accessible replacement:** a historically evidenced, role-compatible shortlist under several cost scenarios: academy/free agents, loans/low-cost options, and a wider affordable shortlist. Availability, acceptance likelihood, reliability and financial evidence must be reviewed. Do not pick the best subsequent performer with hindsight.

For budget scenarios, an accounting approximation is `transfer fee / contract years + annual gross wages + annualized agent/signing costs + annual loan costs`. Every component must be known, including evidenced zeros. This is not cash-flow affordability. Currency, gross/net wage scope and loan contributions need alignment. Market value is neither an actual fee nor wages. Total club employee costs are not automatically first-team wages or available recruitment funds.

Unknown costs and availability are excluded and counted. No team-accessible numeric reference is currently estimated. The UI exposes the scenarios and this limitation instead of inventing numbers.

Low-minute reliability and cross-league translation require held-out calibration. Any shrinkage strength must be estimated and sensitivity tested; no low-minute inflation or hand-set league multipliers are approved. Detailed historic main positions remain incomplete; website profile positions are explicitly provisional proxies.

## Inputs prepared, and gaps

- Football-Data: 14,359 fixtures in all 40 league-season cells, with goals plus shots, shots on target, corners, fouls and cards. One Bundesliga 2024–25 fixture lacks the twelve non-goal context fields. These are separate source inputs; club identity/definition joins are not yet validated. [Source](https://www.football-data.co.uk/data.php), [definitions](https://www.football-data.co.uk/notes.txt).
- Wyscout: 3,071,395 derivative event records, preserving source coordinates and tags. Only 2017–18 is covered; the other 35 league-season cells are absent. A bounded pilot now fits scoring/conceding event-danger probabilities on an early-season training split and evaluates a later-month holdout; this predicts rare events, not player value or model-generated xG. Its tables and limits are in `reports/event_value_pilot/results.md`. [Dataset and attribution](https://figshare.com/collections/Soccer_match_event_dataset/4415000).
- Existing player and keeper audits support seasonal exploration; ten additional recorded outfield metrics are now available to the website reference graph.
- Historical candidate wages, recruitment capacity, contract availability, comparable event coverage and historical position minutes remain insufficient for a complete three-baseline value estimate.
- SkillCorner's current public sample is Australian A-League data, not a fill for Big Five historical tracking. [Repository](https://github.com/SkillCorner/opendata).

Forum discussions were discovery leads, not sources of formula weights: [off-ball coverage discussion](https://www.reddit.com/r/MLS/comments/ge03dv), [action opportunity discussion](https://www.reddit.com/r/soccer/comments/pbvg32). Research judgments still require empirical tests.

## Implemented preview and validation

Owner UI clarification: FutWAR is now the default comparison metric. It displays **not yet estimated** until a fitted, validated contribution output exists. Individual recorded metrics remain selectable exploratory previews; they are not relabeled as WAR. The team-performance tables also show recorded final league positions for all 780 club-seasons, with archived Wikipedia citations; rankings are not reconstructed by sorting earned match points.

The Value & replacement tab compares recorded metrics against season-specific references. It is not a contribution estimate. Reference players need metric-specific observed exposure (default 900 minutes); transfer stints are pooled by provisional identity. The selected player is excluded from their own reference. Unknown positions, inadequate exposure and unavailable metrics are not filled. Keeper/outfield domains remain separate. Team scenarios show an explicit unestimated state.

PowerShell, from the project directory:

```powershell
py -m unittest discover -s tests -p 'test_value_comparison_methods.py'
node tests/test_value_comparisons.js
py scripts/package_explorer.py
```

Next methodological review: approve a small action-value pilot, its credit accounting and chronological validation design before fitting. Eight-season coverage and team-budget estimates remain separate data tasks; neither is resolved by the pilot.
