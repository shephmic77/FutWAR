# FutWAR — Instructions for Codex

## Mission
Build FutWAR (Football Wins Above Replacement), a transparent and validated soccer analytics research project across Europe's Big Five leagues, initially for 2017–18 through 2024–25.

## Goals
1. Estimate players' *observed seasonal contribution* above an appropriate replacement baseline, with a per-90 and total-season value. Aim eventually to express this in expected league points above replacement, but do not label arbitrary composites 'WAR'.
2. Compare **absolute strength and depth** of Premier League, La Liga, Serie A, Bundesliga, and Ligue 1: elite, middle and bottom teams; players actually fielded; over time.
3. Examine positional and tactical context, including formation and role changes; e.g., a LWB in 3-5-2 vs a LB in 4-3-3. Separate overall value from suitability to a particular tactical system.

## Current phase
The foundational source inventory, player-season audit, PostgreSQL staging, match-results and standings checks, and exploratory notebooks are in place. Current authorized work is methodological research for a player-contribution model and its comparison views. No FutWAR WAR formula, feature weights, player-credit policy, cross-position conversion, or replacement pool has been finalized.

The owner asked to investigate three season-specific references—same-position average across all five leagues, same-position league average, and a team-accessible replacement candidate—each with a position-locked and an any-evidenced-position view. This yields six comparison views, not six approved WAR formulas. Average references remain above-average comparisons; only a defensible feasible-replacement pool could support a WAR interpretation. Keep the distinctions explicit in analysis and labels.

The first model direction eventually to test is expected match points before and after observed actions. Current pilots are limited and exploratory. The owner has asked to drop StatsBomb and focus on free alternatives. Current work is data-foundation readiness; do not begin new WAR formula experiments until the documented data gates are reviewed. A possible Impect Bundesliga 2023–24 sample requires source-terms review and a coverage/quality audit before use. The current scope remains 2017–18 through 2024–25, retaining COVID-era seasons pending analysis.

## Technology
Python (primary, not R), pandas and statistical libraries, PostgreSQL and SQL, Tableau for later dashboards; Git/GitHub; Jupyter for exploratory work. Docker optional once useful. Avoid adding tools just to increase the stack.

## Engineering rules
- Inspect the repository and README before changing files; preserve existing user work.
- Plan small, reviewable changes. Prefer plain, readable code and minimal dependencies.
- Never fabricate rows, statistics, tactical roles, links, model performance, or source completeness.
- Keep raw source data immutable; preserve original filenames, source URLs, retrieval dates, licenses/terms, and transformation provenance.
- Keep raw source archives, credentials and local database files out of Git; use `.gitignore`. Do not infer redistribution rights from public access alone.
- Treat this GitHub repository as public. On 2026-10-31 the owner explicitly directed public deployment of the existing explorer and stated that its Kaggle stats, Transfermarkt-derived values/identity records, images/marks, and anonymized injury research material are acceptable for this personal/student project. The generated `site/` deployment bundle is authorized; raw archives and unrelated row-level research outputs remain excluded. Preserve source links, attribution and limitations, and do not describe owner approval as an upstream license or independent legal certification.
- When merging providers, validate club/player identity matching and stat definitions; mark uncertain matches.
- Check missing coverage for every league × season × statistic, not just presence of files.
- Current user-approved scope is 2017–18 through 2024–25. Retain COVID-era seasons for inspection; exclusion or contextual treatment remains undecided.
- Respect websites' terms and rate limits. Prefer permitted public downloads/APIs to brittle scraping.
- Avoid data leakage. Evaluate models on future/held-out seasons and compare to meaningful baselines; report uncertainty.
- Keep league-relative WAR, absolute league strength, and tactical fit as distinct outputs. A stronger league must not be inferred from a higher internally normalized WAR.
- State assumptions and limits explicitly. Do not pretend nominal starting formation reveals exact in-game role.
- Document how to execute scripts and tests on Windows PowerShell (the user's development environment).

## Workflow and communication
For each task: explain the intended file changes, implement, run available checks, and summarize what actually worked and what remains unresolved. Ask before making large restructuring changes or introducing new external services.

## Read first
- `README.md`
- `docs/project_plan.md`
- `docs/data_sources.md`
