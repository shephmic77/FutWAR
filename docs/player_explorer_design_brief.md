# Player explorer design discussion

This document records owner answers to design questions 1-44. Implementation is paused while the page and analysis layout are discussed. The existing prototype is an example, not the approved final layout.

## Accepted direction

- Prioritize the analytical football fan and project owner; navigation and presentation should also be impressive and understandable to a portfolio reviewer.
- Emphasize player comparisons within a chosen season, with league and position distinctions and interactive graphs.
- Add team-comparison and position-exploration options with selectable leagues/teams/positions. These are intended views, not implemented new analyses.
- Begin with a simple, largely blank search-first landing page, rather than opening a preselected player and full dashboard. Reveal detail after selection.
- Use progressive disclosure: initially simple, increasingly detailed as the visitor chooses a subject or analysis.
- Use a hybrid library-like experience: a concise overview and focused sections/tabs, with a coherent visual identity throughout navigation.
- Keep search visible and a compact player header sticky while scrolling.
- Include portrait, club and league marks, age at selected season, nationality, height, preferred foot, main/secondary positions, appearances, minutes and Transfermarkt market value. Arrange details cleanly, with expandable information where useful.
- Shared chart filters should have useful defaults.
- Provide a season slider for an individual season and a range/group selection. Whether noncontiguous seasons and combined summaries are wanted remains open.
- Combine historical line charts, small multiple charts and a metric heatmap where useful.
- Research and propose role-relevant default metrics, drawing on other projects; this does not authorize arbitrary weights or a finalized formula.

## Data and method boundaries

Main position remains the position with most total evidenced seasonal minutes, with ties/incomplete evidence flagged. Secondary labels retain the five-appearance/10% rule; sustained within-match secondary counting is unresolved. Do not fabricate exact roles to complete filters.

Market value must be labeled as a dated provider estimate, distinct from contribution, transfer fee and replacement cost. Existing current/maximum profile values are not historical season snapshots and cannot be projected backward. Birth/profile information also requires verified identity and appropriate dates. Include unavailable states where history cannot be established.

Charts must come from versioned, reproducible analysis outputs, retaining source/definition/cohort/exposure information. League coloring is a visual encoding, not league-strength adjustment. Team-theme colors and analytical league/position encodings should remain distinct. Final default peer groups, visual encodings and range-aggregation behavior need owner decisions.

## Default metric research: proposals only

[Opta's template explainer](https://theanalyst.com/articles/introducing-opta-radars-compare-players) describes limiting metrics and examining their correlations to avoid redundant slices. [StatsBomb's role templates](https://www.hudl.com/blog/new-statsbomb-radars-2023-update) use position-specific measurements, per-90 exposure and defensive opportunity adjustment. [DataMB's guide](https://datamb.football/guide/) demonstrates selectable scatterplot axes, cohort filters and league-based colors. Their scores, thresholds, position buckets and proprietary metrics are not adopted.

Proposed domains: chance generation/finishing/creation for attackers; creation/progression/retention for midfielders; progression/creation/defensive involvement for fullbacks and wingbacks; aerials/defensive involvement/build-up for centre backs; difficulty-aware shot stopping/cross stopping/sweeping/distribution for keepers. Keep LB/RB/LWB/RWB identities distinct despite related display domains.

Current audited notebook measures can support an initial set. Header inspection also found potential shots, key passes, aerial duel outcomes, challenge success, penalty-area touches, pass completion and possession-loss fields in the original CSV. Header presence is not verification of definitions, coverage or comparable quality. Audit these additional measures before displaying them. No new statistic was processed or published during this discussion.

Detailed season trends require verified player identity across records. Aggregating club stints or selected seasons requires explicit exposure-weighted recomputation and source compatibility; do not average per-90 rates or percentiles. Sparse/incompatible records remain visible as coverage limits.

## Owner answers to questions 13-20

- Show both per-90 and total output for count-based metrics; percentages retain their native units. Exact side-by-side/toggle layout remains a presentation detail.
- Default peers: same supported main position and season across all five leagues, with league colors. These are raw cross-league comparisons until a separate league adjustment is validated.
- Historical reference: peer median plus the middle-50% band (25th-75th percentiles).
- Selecting multiple seasons produces one combined-period summary. Compute pooled rates from compatible counts and exposure, not averages of per-90 values. Combined peer membership, minimum exposure and main-position rules still require decisions.
- Club-stint and combined-season views are both selectable. Combine only verified identities and compatible source definitions; league-switch display remains to be resolved.
- Show low-minute historical observations as hollow markers, with minutes and a warning. This does not automatically admit those observations to the default comparison cohort or select a new eligibility rule.
- Scatterplots offer curated presets plus an Advanced axis selector.
- Offer color-by-league and color-by-position modes, plus league colors combined with position-specific point shapes. Legends and exact-position labels must remain accessible; incomplete position evidence is not fabricated.

Default same-position filters naturally yield one position color/shape; position encodings become useful when users deliberately expand the comparison pool. Multi-period graphs need a pooled-period benchmark rather than an unexplained mixture of annual percentiles. Preserve source and coverage warnings in every aggregate.

## Owner answers to questions 21-28

- Combined-period peers qualify by sufficient total minutes across the selected period; participation in every season is not required. The numeric minimum remains open, and eligibility is distinct from performance aggregation.
- Main position across a selected period uses most total evidenced position minutes, with role changes displayed. Incomplete evidence and ties prevent finalization.
- Include all compatible, identity-verified seasons/stints in the selected player's combined summary, including low-minute seasons with warnings. Do not silently discard those contributions based on peer eligibility.
- Show separate league-specific points with an optional combined point for cross-league records. Do not assign the combined record an unexplained single-league identity.
- Point size selector offers equal size, minutes and a third metric. Its initial setting remains unspecified.
- Clicking another player's point opens a compact preview with View profile and Add to comparison.
- Direct comparisons default to a polished, detailed two-player head-to-head. Larger groups, including more than four records, use a table where appropriate. Maximum count and same-player/different-period behavior remain unspecified.
- Optional graph aids are off by default, with controls to enable them all individually. This includes median guides, persistent selected-player labeling, hover details, interactive legend filtering, zoom/reset, quadrant annotations, full-screen and chart download controls. Basic axis labels, units and a static encoding legend remain essential chart information rather than optional analytical overlays; this distinction should be explained to the owner.

Question 29 resolves the historical benchmark visibility: the median/middle-50% band starts hidden and can be enabled. There is no new FutWAR model eligibility threshold or statistical weighting decision.

## Owner answers to questions 29-36

- Historical median and middle-50% benchmark starts hidden, with an option to enable it.
- Initial comparison exposure filter is 900 total minutes across the entire selected period, adjustable by the visitor. No minimum number of represented seasons is imposed. This is exploratory display eligibility, not a final FutWAR rule.
- Scatterplot points start equal-sized; minutes and a third metric remain available size options.
- Head-to-head comparisons support the same verified player across different seasons, periods or clubs.
- Keepers share outfield navigation and visual layout, with keeper-specific charts and metrics. Keeper-versus-outfielder comparisons focus on overall contribution and replacement-related measures once validated; avoid extensive cross-role raw-stat comparisons. Do not label an arbitrary composite WAR or present an unavailable value as computed.
- Prioritize market-value history, injuries/availability and team performance among supporting history sections. These still require evidence and coverage audits; availability cannot be inferred as injury from absence alone.
- Missing information receives a compact Unavailable explanation.
- Offer light and dark themes. After player selection, use team colors within the selected theme, keeping analytical league/position encodings distinct and text/graphs readable. The default theme and club-color selection for multi-club periods remain open.

## Owner answers to questions 37-44

- Light is the default theme, with a dark-theme toggle.
- For a multi-club selected period, use the club with most player minutes for team accents (the majority-club choice). Do not infer this club if exposure is unresolved; ties need a neutral fallback or later owner decision.
- Comparison pages retain neutral surroundings and team-colored accents for each subject.
- Team comparisons begin with a compact overview combining results and squad information, followed by detailed tabs.
- Allow team comparisons across different leagues and seasons. Display each selected league/season explicitly and preserve context warnings; raw differences do not establish absolute league strength.
- Provide chart-image downloads, comparison-table CSV exports, printable player reports and links preserving player/filter selections. These are requested capabilities, not currently implemented. Export only content permitted by source terms; local share links do not imply public deployment or access to private data.
- Prioritize desktop for now; mobile optimization is deferred.
- Exclude rumors, live scores, fantasy advice and unsupported overall ratings.

## Proposed page structure for review

This structure organizes the approved requirements; it is a proposal pending owner review, not an implemented redesign.

1. Search-first landing: simple search, Players/Teams entry points and theme toggle. No preselected player or dense dashboard.
2. Selected-player header: portrait, club/league marks and concise identity details, plus season/period selection and Add to comparison. A compact header and search remain visible while scrolling.
3. Overview: concise seasonal/period summary, selected role and coverage information, with a small set of analytical charts. Progressive disclosure keeps secondary details out of the initial view.
4. Analysis: season trends, scatter presets and advanced axes, peer filters, per-90/totals controls, league/position encodings and optional chart aids. Analysis outputs supply chart values and provenance.
5. Context: prioritized market-value history, injuries/availability and team performance, with role changes and other verified histories expandable. Missing evidence receives a compact Unavailable explanation.
6. Value and replacement: validated contribution research when available, without placeholder WAR scores. Cross-role comparisons concentrate here rather than mixing incompatible raw statistics.
7. Comparison: detailed two-subject view by default, including the same player across periods; larger groups use a table. Team comparisons use a results/squad overview and detailed tabs.
8. Evidence and export: source/definition/coverage details, chart downloads, CSV, printable report and selection-preserving links, subject to reuse permissions.

No interface changes are made during this discussion. Remaining small details include comparison limits, tied club-color fallback, exact metric presets and export formats. They do not authorize new research formulas, identity merges or inferred historical information.
