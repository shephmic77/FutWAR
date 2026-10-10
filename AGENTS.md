# FutWAR — Instructions for Codex

## Mission
Build FutWAR (Football Wins Above Replacement), a transparent and validated soccer analytics research project across Europe's Big Five leagues, initially for 2022–23 through 2025–26.

## Goals
1. Estimate players' *observed seasonal contribution* above an appropriate replacement baseline, with a per-90 and total-season value. Aim eventually to express this in expected league points above replacement, but do not label arbitrary composites 'WAR'.
2. Compare **absolute strength and depth** of Premier League, La Liga, Serie A, Bundesliga, and Ligue 1: elite, middle and bottom teams; players actually fielded; over time.
3. Examine positional and tactical context, including formation and role changes; e.g., a LWB in 3-5-2 vs a LB in 4-3-3. Separate overall value from suitability to a particular tactical system.

## Current phase
Phase 1: find/audit real data, establish coverage and provenance, build reproducible ingestion and PostgreSQL schema. No FutWAR model has been finalized. The first technical task is to audit original CSVs placed in `data/raw/`, report columns, missing values, duplicates, and league/season coverage. Do not claim an untested dataset is complete.

## Technology
Python (primary, not R), pandas and statistical libraries, PostgreSQL and SQL, Tableau for later dashboards; Git/GitHub; Jupyter for exploratory work. Docker optional once useful. Avoid adding tools just to increase the stack.

## Engineering rules
- Inspect the repository and README before changing files; preserve existing user work.
- Plan small, reviewable changes. Prefer plain, readable code and minimal dependencies.
- Never fabricate rows, statistics, tactical roles, links, model performance, or source completeness.
- Keep raw source data immutable; preserve original filenames, source URLs, retrieval dates, licenses/terms, and transformation provenance.
- Keep raw/processed datasets and credentials out of Git; use `.gitignore`. Do not assume data may be redistributed.
- When merging providers, validate club/player identity matching and stat definitions; mark uncertain matches.
- Check missing coverage for every league × season × statistic, not just presence of files.
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
