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

The project has audited an initial player-season source, built a local PostgreSQL/SQL workflow, assembled match and standings references, explored metric coverage by position, and run bounded event-state experiments. Event context gives a small average forecasting improvement across chronological folds, but its much larger, feature-sensitive transition estimates do not establish action-to-player credit or player value. Sources have differing definitions and coverage, and the data are not complete or fully harmonized. Current repository, publication, and owner data-use status is summarized in [project status](docs/project_status.md).

The owner has dropped StatsBomb from consideration. OpenPlay v0.1.0 has now been acquired and audited across all 40 target league-season cells (2017–18 through 2024–25), with events listed for 14,334 of 14,360 fixtures. This establishes broad event-file coverage, not complete event data, player attribution, all source-use permissions for derived player outputs, or a complete WAR foundation. Its chronological expected-points and goal-difference experiments remain team-state forecasting checks; no player scores are produced. A reviewed club-name alias update raised unique exact-key player-season candidates to 20,889 / 22,417 and equal-appearance candidates to 20,227 / 22,417; these remain candidates rather than approved links. The 61 larger appearance mismatches cluster in six club-seasons with known event-file gaps. See the [OpenPlay audit](docs/openplay_release_audit_2026-11-04.md), [club-alias follow-up](docs/openplay_team_alias_followup_2026-11-06.md), [identity discrepancy follow-up](docs/openplay_identity_exposure_conflicts_2026-11-06.md), the [current project status](docs/project_status.md), and the [event-context walk-forward report](docs/openplay_action_value_walkforward_2026-11-05.md). The earlier [source-gate closeout](docs/event_data_source_gate_closeout_2026-11-03.md) records the search before OpenPlay was acquired.

A multi-season adjusted-lineup feasibility check found that simple starting-XI and realized-minute identity features did not improve held-out expected-points forecasts beyond pre-match context at the fixed shrinkage setting. An earlier-season-only shrinkage sensitivity produced only tiny, inconsistent changes. This is not a causal player-impact estimate or the requested action-plus-lineup residual test. See the [lineup-presence walk-forward](docs/openplay_lineup_presence_walkforward_2026-11-05.md). A targeted replacement-cost source review found no complete, reusable historical Big Five wage-and-availability panel; the team-accessible comparison remains unavailable as a numeric baseline. See the [replacement-cost source screen](docs/replacement_cost_source_screen_2026-11-05.md). A full-scope teammate-overlap audit finds repeated exposure in all 780 club-seasons, but it measures no teammate uplift or player value; see the [eight-season overlap report](docs/openplay_teammate_uplift_overlap_2026-11-05.md).

OpenPlay formation slots now have an expanding-season position-label audit, but the formation durations still differ from lineup exposure by more than five minutes in 6.51% of held-out player-match rows. Applying a conservative mapping and five-minute reconciliation screen retains candidate source-position minutes for 90.39% of held-out lineup minutes, but does not validate FutWAR roles. See the [position-slot audit](docs/openplay_position_slot_audit_2026-11-05.md). Player WAR remains unavailable in the site until its data and validation gates pass.

An aggregate formation-slot goalkeeper audit assigns one mapped keeper to 95.39% of later-season on-target shots. Direct lineup intervals raise candidate coverage to 98.91% in those same 35 cells. A strict same-minute formation-plus-lineup cross-check for substitute keepers raises candidate coverage to 99.30%. An eight-per-league external review sample confirmed the incoming keeper pair in 40/40 candidates, but only 7/32 comparable numeric times matched exactly; 25 differed by 1–4 minutes, six reports described a half-time change, and two did not provide a precise minute. This supports the sampled player-pair links, not all shot-to-keeper interval assignments or shot-stopping value. See the [direct lineup audit](docs/openplay_keeper_direct_lineup_audit_2026-11-05.md), [substitute linkage audit](docs/openplay_keeper_substitute_linkage_2026-11-06.md), and [formation-slot comparison](docs/openplay_keeper_shot_linkage_2026-11-05.md).

A separate seven-fold goalkeeper shot-outcome pilot tests whether shot-target coordinates improve goal prediction over pre-shot context. The Brier/log-loss/AUC changes are small and mixed across 103,203 held-out on-target non-penalty shots, and no goalkeeper identities or player scores are used. It is not keeper skill or a WAR component; see the [pilot report](docs/openplay_keeper_shot_outcome_pilot_2026-11-05.md).

See [the project plan](docs/project_plan.md), [data-source register](docs/data_sources.md), and [WAR model architecture](docs/war_model_architecture.md) for decisions and limitations. These documents preserve research context; prior proposals remain proposals unless marked as an owner decision.
The current pre-WAR input review documents the selected-metric coverage screen, results-only pre-match team-context candidate, and remaining readiness gates in [pre-WAR input readiness](docs/pre_war_input_readiness.md).
Full-path availability and multi-season endpoint sensitivity for the owner-selected 3-, 5-, and 10-event horizons have been reviewed across the OpenPlay sample. The endpoint sensitivity remains a team-state diagnostic, not action value. See the [window-coverage audit](docs/openplay_action_horizon_coverage_2026-11-05.md) and [seven-fold transition sensitivity](docs/openplay_action_horizon_sensitivity_2026-11-05.md). The latest results-only expected-points benchmark compares lagged team form against historical league outcome rates using seven expanding-window season folds. It is a match-level forecast reference, not player WAR; see the [walk-forward results and chart](docs/prematch_expected_points_walkforward_2026-11-03.md) and the separate [2024–25 calibration and bootstrap review](docs/prematch_expected_points_baseline_2026-11-03.md).
The [COVID training sensitivity](docs/covid_training_sensitivity_2026-11-03.md) compares retaining or excluding those seasons from this narrow match-results benchmark; it does not settle the separate player-level COVID decision.
The next-stage evaluation plan specifies how to compare expected-points and transparent state-value candidates, incremental lineup effects, teammate uplift, action attribution, six comparison views, uncertainty, and website release gates without approving a formula. See [WAR validation and release protocol](docs/war_validation_and_release_protocol.md).
Tableau is the planned interactive analysis and presentation layer; see the [FutWAR Tableau workflow](docs/tableau_workflow.md) for the proposed order and practices. A local Tableau audit workbook has a separate polished copy for data-foundation review; this is not certification of the full data foundation. See the [data-gate review](docs/data_foundation_gate_review.md).

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

Original/raw source archives, credentials, and local database files are excluded from Git. The owner has directed publication of the current explorer bundle for this personal/student project. The tracked `site/` directory includes the explorer and its derived player/search data. The owner's project-use decision does not change upstream license statements or imply independent legal certification. See [project status](docs/project_status.md) and the [source register](docs/data_sources.md) for the boundary between that decision and source-specific provenance. The public app is a research prototype, not a finalized WAR product.

## Public site deployment

The configured production domain is [futwar.vercel.app](https://futwar.vercel.app/). Vercel is set to serve the player explorer from the tracked `site/` directory. Live availability could not be verified during the latest project-status review; see [project status](docs/project_status.md). Rebuild the deployable bundle from the prepared local explorer with:

```powershell
py scripts/package_explorer.py
.\scripts\prepare_vercel_site.ps1
```

This refreshes the local build under ignored `reports/explorer/`, copies the player library into `site/index.html` with its required assets, and verifies the deployable artifact. See [Vercel setup](docs/vercel_setup.md).

## Local setup

Use Windows PowerShell from the project root. Python is the primary language. Some scripts use the standard library; install the project requirements for notebooks and source-specific analyses:

```powershell
py -m pip install -r requirements.txt
py -m unittest discover -s tests -v
```

PostgreSQL is optional for many audits. When needed, create a local `.env` from `.env.example`, set a unique local password, and start the database with Docker Compose. See [Docker setup](docs/docker_setup.md). Never commit `.env` or any database dump.

The root `.gitignore` keeps raw and processed records and generated detailed outputs local. To run the source inventory after placing permitted CSVs in `data/raw/`, use `py scripts/audit_data.py`. Its `coverage.csv` counts mapped raw rows before processing; duplicates and overlapping mapped files may remain. For corrected player-season metric coverage and the source register used in Tableau, run `py scripts\build_tableau_foundation.py`. That export uses the corrected derivative, so its counts can differ from the raw inventory. For the aggregate-only pre-WAR input screen and leakage-conscious lagged team-context candidate, run `py scripts\build_pre_war_foundation_review.py` and `py scripts\build_prematch_team_context.py`. The arithmetic consistency screen for totals, rates and residuals is `py scripts\audit_player_metric_consistency.py`; it writes an ignored review queue under `reports/player_metric_consistency/` and never edits inputs. See [its interpretation and current results](docs/player_metric_consistency_review_2026-11-04.md). These scripts leave source data unchanged. Inspect the local `reports/` outputs before interpreting or sharing them; neither row presence nor a successful file read proves statistical completeness.
