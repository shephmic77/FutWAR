# Normalized PostgreSQL core

The audited sources now share database keys for competition, season, club and completed match. This makes joins explicit and lets PostgreSQL reject invalid relationships. The existing staging records and original raw files remain unchanged. This is Phase 1 infrastructure, not a FutWAR model.

## Tables and grain

| Table | One row represents | Current rows |
| --- | --- | ---: |
| `competitions` | One of the five leagues | 5 |
| `seasons` | One season from 2017-18 through 2024-25 | 8 |
| `competition_seasons` | A league-season | 40 |
| `clubs` | A provisional competition-qualified club identity | 149 |
| `club_source_aliases` | One source club label within a competition | 339 |
| `club_seasons` | A club participating in a league-season | 780 |
| `matches` | A scored fixture, identified by league, season, date, home and away club | 14,359 |
| `match_results` | The score for a fixture | 14,359 |
| `match_source_records` | A fixture's source and score provenance | 14,359 |
| `player_season_context` | A processed player-team-season record linked to its context | 22,418 |

A primary key identifies a row. A foreign key requires that its referenced row exists. For example, both match clubs must occur in `club_seasons` for the same league and season. Checks reject negative goals and a club playing itself.

The IDs are opaque local database keys. Existing IDs survive repeated imports, but they are not provider IDs or portable identifiers across fresh databases. Identity sequence gaps are normal. Club keys combine competition code with the player-source club label. Explicit reviewed OpenFootball aliases map to those keys; no fuzzy matching occurs.

Club identity remains `provisional_source_label`. This groups reconciled labels across our current seasons, without claiming that club histories, renamings or cross-league identities have been independently verified. The `user_fbref_archive` namespace reflects the declared origin of the user's CSV, rather than a separately verified FBref download. There is no normalized player identity yet: the context bridge refers to the processed record using its original source SHA-256 and output record number. Transfers and similarly named players still require research before player-level aggregation.

## Results and provenance

`normalized_match_results` provides readable club names, scores and source references. Its current grain is one row per match because every match currently has exactly one provenance record. Adding multiple providers will require a deliberate resolution/view policy before this view is used for aggregation.

Original OpenFootball scores and the 20 verified official supplements remain distinguishable. For supplements, `base_source_sha256` identifies the original fixture file, which lacked the score; `supplement_sha256` identifies the separate score evidence export. The official result URL is preserved. No assertion is made that the original file contained the supplemented result.

`team_results_baseline` calculates played, wins, draws, losses, goals and `earned_match_points` (three per win, one per draw). These are points earned from recorded results, not official standings: deductions, sanctions, tie-break rules and shortened-season ranking policies are not modeled. They also do not measure absolute league strength or contribution above replacement.

Ligue 1 2019-20 retains its 279 completed results. No cancelled games were filled. COVID treatment remains undecided.

## Run in Windows PowerShell

Open Docker Desktop, then run from the project folder:

```powershell
docker compose up -d --wait
docker compose exec -T postgres psql -U futwar -d futwar -f sql/009_normalized_core.sql
docker compose exec -T postgres psql -U futwar -d futwar -f sql/010_validate_normalized_core.sql
docker compose exec -T postgres psql -U futwar -d futwar -f sql/011_example_normalized_queries.sql
```

For a rebuild, first complete the staging, EDA, enrichment and match imports documented in the README and existing guides. Run `007_match_results_audit.sql`, then `008_verified_match_supplements.sql`, before `009_normalized_core.sql`. The normalized import depends on the effective supplemented results, reviewed club map and enriched player-season EDA view.

The import runs in a transaction, rejects score conflicts and changed existing result URLs, and skips existing keys on a repeat run. It is designed for the current audited snapshot. It does not migrate revised aliases, correction policies or providers automatically; such changes need review and explicit versioning.

The validation script checks fixed snapshot counts, mappings, every source score in both directions, player context, supplement hashes and team accounting. It also exercises rejected writes inside rollback blocks. Rerunning the import was checked to insert zero duplicate rows and preserve every existing club and match ID. All 22 existing Python regression tests passed after this change.

Try this small query in PowerShell:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -c "SELECT team, played, wins, draws, losses, earned_match_points FROM futwar.team_results_baseline WHERE league = 'Premier League' AND season = '2024-25' ORDER BY earned_match_points DESC, team;"
```

`SELECT` chooses columns, `FROM` chooses a table or view, `WHERE` filters rows, and `ORDER BY` sorts the output. PowerShell launches `psql`; PostgreSQL interprets the SQL inside the quoted string.

## Next research step

Validate these result-derived team totals against independently sourced official standings and document deductions and ranking rules separately. Then investigate stable player identifiers and transfer records before joining player contributions across clubs. Neither step requires selecting WAR weights or a replacement threshold yet.
