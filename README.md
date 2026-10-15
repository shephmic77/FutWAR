# FutWAR

> **UNDER CONSTRUCTION — active research and development.**
>
> FutWAR is a research prototype. The player explorer and current experiments are incomplete. No final WAR formula, coefficients, replacement pool, or conversion to expected league points has been approved.

FutWAR (Football Wins Above Replacement) is a transparent soccer analytics project focused on men's domestic football in Europe's Big Five leagues from **2017–18 through 2024–25**. The goal is to estimate a player's observed contribution relative to a defensible replacement, while keeping league strength and tactical fit as distinct questions.

## Research goals

- Estimate seasonal player contribution, first per 90 and then across observed playing time; seek an expected-points interpretation only after validation.
- Compare league/team strength on a common scale, including squad depth and the players actually fielded.
- Study specific positions, tactics, and role changes without inferring played roles from broad labels or formation alone.
- Include goalkeepers, with role-appropriate measurement and a separate validation path.

The owner wants three replacement comparisons (a same-position average across the five leagues, a selected league average, and a team-accessible option informed by historical resources/budgets), each available in position-locked and flexible-position views. These are **six comparison views**, not six selected formulas. Team-budget feasibility, league adjustment, cross-position comparability, player credit, and uncertainty remain research questions. The owner's secondary-position threshold is at least five appearances and at least 10% of appearances in that specific position. No position rule or WAR weights are inferred where evidence is missing.

COVID-era seasons remain in the 2017–18 to 2024–25 scope for inspection. Whether to omit them or add context is undecided. Do not adjust or exclude them without discussion.

## Current status

The project has audited an initial player-season source, built a local PostgreSQL/SQL workflow, assembled match and standings references, explored metric coverage by position, and run bounded event-state experiments. Those experiments suggest that event context can improve outcome prediction in limited samples; they do not establish action-to-player credit or player value. Sources have differing definitions, coverage, and reuse terms. The data are not complete or fully harmonized.

The owner has dropped StatsBomb from consideration. Free-source screening identified Impect Open Data (Bundesliga 2023–24) as a possible later-season event sample, subject to review of its separate terms and a coverage/quality audit. Data readiness remains incomplete; see the [data foundation readiness gates](docs/data_foundation_readiness.md). Formula experiments remain paused until the foundation is reviewed.

See [the project plan](docs/project_plan.md), [data-source register](docs/data_sources.md), and [WAR model architecture](docs/war_model_architecture.md) for decisions and limitations. These documents preserve research context; prior proposals remain proposals unless marked as an owner decision.

## Repository layout

```text
AGENTS.md       project-specific development and research constraints
data/           source manifests, aliases, and reviewed metadata
notebooks/      exploratory and methodological notebooks
docs/           research plan, provenance, decisions, and methods
profile/        player-explorer prototype source
reports/        reviewed narrative findings and selected methodology figures
scripts/        reproducible audits, preparation, and research experiments
sql/            PostgreSQL schema and analysis queries
tests/          automated checks for research and data-handling code
```

Original/raw and processed datasets, credentials, local database files, and provider-restricted files are excluded from Git. The public browser application is published from `site/`; its compressed player data, quick-search index and images are separate files so the interface can start before the full library finishes loading. The owner has reviewed the included sources for personal/student project use. Source documentation and attribution remain part of the repository.

## Public site deployment

The live FutWAR explorer is available at [futwar.vercel.app](https://futwar.vercel.app/). The repository is configured for Vercel through `vercel.json`, which serves the `site/` output directory. After updating the explorer locally, rebuild the public site artifact:

```powershell
py scripts/package_explorer.py
.\scripts\prepare_vercel_site.ps1
```

Commit and push the complete updated `site/` folder with the related application changes. Vercel can then deploy automatically from the connected GitHub repository. See [Vercel setup](docs/vercel_setup.md).

## Local setup

Use Windows PowerShell from the project root. Python is the primary language. Some scripts use the standard library; install the project requirements for notebooks and source-specific analyses:

```powershell
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
```

PostgreSQL is optional for many audits. When needed, create a local `.env` from `.env.example`, set a unique local password, and start the database with Docker Compose. See [Docker setup](docs/docker_setup.md). Never commit `.env` or any database dump.

The root `.gitignore` keeps raw and processed records and generated detailed outputs local. To run the first inventory after placing permitted CSVs in `data/raw/`, use `py scripts/audit_data.py`; inspect the local `reports/` outputs before interpreting or sharing them.
