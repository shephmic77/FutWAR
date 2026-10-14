# FutWAR — Project plan and research decisions

## Project identity and initial boundaries
- Name: **FutWAR** — Football Wins Above Replacement (working title).
- Independently developed sports analytics / data science portfolio project.
- Geography: Europe's Big Five domestic men's leagues: England Premier League, Spain La Liga, Italy Serie A, Germany Bundesliga, France Ligue 1.
- Seasons: **2017–18 through 2024–25**, eight seasons. The user expanded the scope after supplying the first dataset. Retain all seasons initially, including COVID-era seasons; inspect their distributions and data quality before deciding whether to exclude them or add contextual adjustments. No exclusion policy is finalized.
- Primary language: **Python**, rather than R (user more comfortable with Python). Database: **PostgreSQL/SQL**. Interactive visualization: **Tableau**. GitHub repository: `shephmic77/FutWAR`; use the repository root as the working directory for commands.
- Goalkeepers are included in the project scope following owner confirmation on 2026-10-10. Outfield and goalkeeper contribution methods are developed separately; cross-position value requires a validated common outcome scale. The existing outfield notebook remains an explicitly bounded analysis.
- Owner data-use decision, 2026-10-10: investigate cited keeper archives for the personal project unless explicitly contrary personal-use terms are identified. Reuse rights remain unconfirmed where policy access or licensing evidence is incomplete; no dataset redistribution is authorized. Row-level keeper staging, correction plans and findings remain local and are excluded from the public repository.
- Desired granularity: ideally match-level with season aggregates; selective event-level tactical studies if complete comparable data are unavailable.

## Three research goals

Owner clarification, 2026-10-10: goalkeeper analysis belongs alongside outfield players in both analysis tracks. The first describes each position separately; the second investigates overall player value using role-relevant evidence on an eventual validated common scale. Shared notebook entry points and unchanged model decisions are documented in `two_analysis_tracks.md`. Broad outfield labels remain provisional until historical specific positions are supported.
### 1. Player contributions and value above replacement
Core question: how much did each player actually contribute to their club in a season compared with a readily available replacement-level player? Distinguish:
- Player value per 90, without replacement subtraction.
- Above-replacement value per 90.
- Cumulative seasonal above-replacement value based on playing time.
- Aspirational final interpretation: **expected league points above replacement**, after calibration and validation.

Owner confirmation, 2026-10-10: follow baseball WAR's replacement-level comparison; the proposed average-player comparison was withdrawn. The soccer replacement pool and its estimation remain undecided. Keep position-only descriptive analysis separate from contribution modeling, and recognize contributions beyond goals and assists without tuning weights to force positional representation in rankings.

Additional owner confirmation, 2026-10-10: core FutWAR uses a shared replacement standard, not a different standard based on each club's budget. Club-specific replacement options form a separate comparison, where resources, attraction, academy alternatives and historical availability may be investigated. Shared means a common comparison principle; it does not yet settle positional baselines, variation by league/season or cross-league calibration. Protect estimates against small-sample rate instability and league/context bias; no stabilization method, exposure threshold or league multiplier is finalized.

Position decision, 2026-10-10: use specific historical positions for player labels and replacement compatibility, rather than DF/MF/FW families. Do not automatically interchange LB, RB, CB, LWB or RWB. A secondary position requires both at least 5 appearances and at least 10% of total appearances within the analyzed season. The primary position is proposed as the most frequently evidenced match position; ties remain flagged. Missing match positions cannot shrink the denominator or establish complete labels. Player-season aggregation across clubs requires verified identities. Current provider position descriptions alone do not establish seasonal position frequencies or exact tactical roles.

Candidate performance domains (final inputs/weights NOT decided):
- Attack: non-penalty goals, npxG, xA, shooting, shot/goal-creating actions, finishing residuals.
- Chance creation: key passes, progression, progressive passes/carries, take-ons.
- Possession: completion conditional on pass difficulty, dispossessions, miscontrols, turnovers.
- Defense: tackles, interceptions, blocks, recoveries, aerial duels; adjust for opportunities/possession, not just raw counts.
- Discipline: cards, fouls and penalties conceded.
- Context: position, minutes, team strength, opposition strength, league, game state, formation and observed role where defensible.
- Goalkeeper extension: post-shot xG vs conceded, claims/crosses, sweeping, distribution, etc.

Warning: related features are correlated; don't sum arbitrary weighted z-scores and call them WAR. Study replacement definition (percentile vs realistic available reserves), calibration from on-field impact to goals/points, positional comparability, shrinkage for small samples, and uncertainty intervals.

### 2. Relative league and team strength
Questions: Which league has strongest top 3–5, middle, and bottom 3–5 teams? Which has greater depth and competitive spread? How do comparisons change across the eight seasons? How strong are the **players actually fielded** (minutes-weighted, starts, rotation), not merely squad rosters?

Compare on a **common cross-league scale** using club results/ratings, ideally including continental competitions as links between leagues; assess calibration and structural biases (European fixtures over-represent top clubs). External ratings like ClubElo may be benchmarks if accessible under their terms. UEFA coefficients reflect European participants, not the complete league.

Do not infer absolute league quality directly from within-league above-replacement measures. Distinguish value relative to a local replacement pool and cross-league transferable talent.

### 3. Formation, position and tactical roles
Key user question: *How do you evaluate a LWB in a system with wingbacks versus a team that doesn't field wingbacks?*

Separate:
- Position family (wide defender, center-back, central midfielder, attacker, etc.).
- Tactical role (attacking wingback, conventional or inverted fullback, etc.).
- Observed actions/opportunities and locations.
- Overall contribution vs fit to a nominated system (future projection, not equivalent to actual seasonal WAR).

Nominal 3-5-2/4-3-3 lineups do not determine true in/out-of-possession shape. Only infer specific roles from sufficient event/positional evidence. Consider additional layer using a smaller rich-data sample; allow 'unknown role' rather than inventing labels.

## Research / modeling sequence

The owner requested three season-specific comparison views: same-position average across all five leagues, same-position league averages with selectable leagues, and team-accessible replacement under multiple budget scenarios. Average performance is retrospective for the selected season; historical team availability/resources are assessed at season start, with January separate. Combined periods use each year's own reference. See [draft formula, inputs and validation limits](three_baseline_formula_proposal.md). Recorded-metric website previews are implemented; a calibrated contribution model and numeric team-budget baseline remain unresolved.

The first Wyscout event-danger pilot and a one-season expected-match-points state pilot are complete. Corrected goal-event checks now pass directionally, but the event-context model underperforms an exploratory smooth score-state benchmark on the reused 2017–18 test window. New chronological holdouts are needed before selecting a model or using action deltas for player totals. The first same-sequence comparison evaluates direct action credit against an equal participant split for complete-actor shot-ending sequence proxies. It shows that allocation changes player rankings while conserving the same sequence total; it does not identify the more accurate player-credit method. The equal split is not Shapley, and this attacking pilot does not cover the all-position goal. See the [action-credit comparison](action_credit_comparison.md), [pilot results](../reports/action_credit_pilot/results.md), and [expected-points pilot report](../reports/expected_points_pilot/results.md). UEFA's public finance reports and Capology were screened as historical-budget leads; neither currently supplies a free, openly reusable, complete club-by-club Big Five panel for this project.

1. Inventory permitted data sources; audit league × season × position × stat × match coverage and provenance.
2. Preserve original data and define a data dictionary, identifiers and missingness policies.
3. Create normalized PostgreSQL schema (players, teams, competitions, seasons, matches, appearances, player stats, team stats, source mappings; tactical events/lineups optional).
4. Perform exploratory analysis of position-specific distributions and exposure opportunities.
5. Create **simple, explainable baseline value**; define and compare replacement definitions.
6. Develop/test more defensible player-value estimates (regularization or hierarchical models if appropriate); translate to goal/expected points only after calibration.
7. Model club strength/league depth on cross-league scale, separate from player WAR.
8. Add context: team, opponent, role, formation as data permit; quantify ranking sensitivity.
9. Validate chronologically (e.g., train earlier seasons and evaluate a later season within the available 2017–18 to 2024–25 span; the exact split remains undecided), avoiding future information leakage, and compare with simple baselines. Quantify uncertainty.
10. Present results in Tableau: WAR rankings and per-90, 2-player comparisons, raw vs context-adjusted, top/mid/bottom league strength distributions, season trends, role profiles.
11. Document assumptions, limitations and reproducible commands.

## Initial deliverables
- Data source audit and report CSVs; `docs/data_dictionary.md`.
- Ingestion/cleaning scripts with source tracking and reproducibility.
- PostgreSQL schema and analytical SQL queries/window functions.
- Methodology notebooks, model code, validation report.
- Tableau dashboards.
- GitHub README and setup guide; no redistribution of restricted data.

## Important unconfirmed decisions

The owner has since requested three graph comparisons (all-five-league average, selected-league average, and team-feasible replacement) crossed with locked/any-position eligibility. The average options must be called above-average benchmarks rather than literal replacement WAR. The [WAR architecture and evidence gaps](war_model_architecture.md) lays out a common expected-points contribution scale and a bounded two-track research plan; weights and a final formula remain unconfirmed.

The owner wants standard analysis to use a single main position and a separate polished interactive player search with additional positions, injuries, transfers, team statistics and broader context. [Requirements and data gaps](player_profile_direction.md) distinguish this direction from implemented features. Main-position calculation, injury-source coverage and profile implementation remain to be reviewed.
- No final WAR formula, conversion to expected league points, position buckets, replacement percentile, feature weights, or tactical-role ontology is finalized.
- No source has been verified to contain *all* eight seasons, all leagues, detailed defense and formations in comparable quality.
- User wants an ambitious model developed incrementally, not a pile of arbitrary technologies. Cross-team future projection/tactical fit is a later extension beyond retrospective WAR.

## Immediate task for Codex
Inspect the actual repository; audit input datasets under `data/raw/` (CSV/possibly ZIP as requested), report rows, columns, null rates, duplicates, season/league coverage and column-level availability. Write output to `reports/`, document usage, keep source data ignored by Git. If Python on local PowerShell is not recognized, try `py --version` and/or guide installation. Cloud Codex may have its own Python environment; do not claim to have changed the user's Windows setup.

## Reinforced requirements from additional user notes

- Python, PostgreSQL/SQL and Tableau form one connected workflow: audited data and identifiers in SQL, statistical estimation and validation in Python, analytical results exported for dashboards. SQL should demonstrate joins, aggregations and window functions, rather than serving only as storage. Jupyter supports exploration; Docker and experiment tracking remain optional until useful.
- Player contribution, absolute club/league strength and tactical fit remain three main project goals with separate outputs. League analysis must cover elite, middle and bottom clubs, depth, spread, and minutes-weighted players actually fielded. Starting-XI and rotation analyses require appearance data.
- Planned Tableau views include player leaderboards, two-player comparisons, raw/context-adjusted comparisons, league/team distributions and tactical profiles. WAR labels require validated replacement and outcome calibration.
- Retrospective observed contribution is the initial player-value objective. Recruitment projections and system suitability remain later extensions.
- Broad player-season coverage can proceed alongside a smaller rich tactical sample if match/event evidence cannot support uniform eight-season coverage. Do not infer wingback/fullback roles from nominal formation alone.
- The supplied notes contain earlier four-season references and illustrative formulas. The explicit 2017-18 through 2024-25 scope supersedes those references; no proposed formula, role grouping or replacement rule is finalized.
