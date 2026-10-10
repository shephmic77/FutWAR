# FutWAR — Project plan and research decisions

## Project identity and initial boundaries
- Name: **FutWAR** — Football Wins Above Replacement (working title).
- Independently developed sports analytics / data science portfolio project.
- Geography: Europe's Big Five domestic men's leagues: England Premier League, Spain La Liga, Italy Serie A, Germany Bundesliga, France Ligue 1.
- Seasons: **2022–23, 2023–24, 2024–25, 2025–26**. Intentionally excludes 2021–22 to limit potential COVID-era disruptions. Historical seasons before that can be added later if justified.
- Primary language: **Python**, rather than R (user more comfortable with Python). Database: **PostgreSQL/SQL**. Interactive visualization: **Tableau**. GitHub repository: `shephmic77/FutWAR`; Windows local folder `C:\Users\mikey\Desktop\Data Science projects\FutWar`.
- First version: outfield players; goalkeepers need a separate method.
- Desired granularity: ideally match-level with season aggregates; selective event-level tactical studies if complete comparable data are unavailable.

## Three research goals
### 1. Player contributions and value above replacement
Core question: how much did each player actually contribute to their club in a season compared with a readily available replacement-level player? Distinguish:
- Player value per 90, without replacement subtraction.
- Above-replacement value per 90.
- Cumulative seasonal above-replacement value based on playing time.
- Aspirational final interpretation: **expected league points above replacement**, after calibration and validation.

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
Questions: Which league has strongest top 3–5, middle, and bottom 3–5 teams? Which has greater depth and competitive spread? How do comparisons change across the four seasons? How strong are the **players actually fielded** (minutes-weighted, starts, rotation), not merely squad rosters?

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
1. Inventory permitted data sources; audit league × season × position × stat × match coverage and provenance.
2. Preserve original data and define a data dictionary, identifiers and missingness policies.
3. Create normalized PostgreSQL schema (players, teams, competitions, seasons, matches, appearances, player stats, team stats, source mappings; tactical events/lineups optional).
4. Perform exploratory analysis of position-specific distributions and exposure opportunities.
5. Create **simple, explainable baseline value**; define and compare replacement definitions.
6. Develop/test more defensible player-value estimates (regularization or hierarchical models if appropriate); translate to goal/expected points only after calibration.
7. Model club strength/league depth on cross-league scale, separate from player WAR.
8. Add context: team, opponent, role, formation as data permit; quantify ranking sensitivity.
9. Validate chronologically (e.g., train earlier seasons and evaluate 2025–26), avoiding future information leakage, and compare with simple baselines. Quantify uncertainty.
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
- No final WAR formula, conversion to expected league points, position buckets, replacement percentile, feature weights, or tactical-role ontology is finalized.
- No source has been verified to contain *all* four seasons, all leagues, detailed defense and formations in comparable quality.
- User wants an ambitious model developed incrementally, not a pile of arbitrary technologies. Cross-team future projection/tactical fit is a later extension beyond retrospective WAR.

## Immediate task for Codex
Inspect the actual repository; audit input datasets under `data/raw/` (CSV/possibly ZIP as requested), report rows, columns, null rates, duplicates, season/league coverage and column-level availability. Write output to `reports/`, document usage, keep source data ignored by Git. If Python on local PowerShell is not recognized, try `py --version` and/or guide installation. Cloud Codex may have its own Python environment; do not claim to have changed the user's Windows setup.
