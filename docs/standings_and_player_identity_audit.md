# Standings and player identity audit

This Phase 1 addition compares independently transcribed primary references with `team_results_baseline`. Reference data and administrative rulings remain separate from match scores and player statistics. No player IDs, replacement levels, WAR weights or COVID exclusions were introduced.

## Initial 2024-25 comparison

| League | Club references | Metrics available | Evidence limitations |
| --- | ---: | --- | --- |
| Bundesliga | 18 | Played, W/D/L, GF/GA, points | League table explicitly identifies season; includes awarded result |
| Premier League | 3 | Played, W/D/L, GF/GA, points | Liverpool, Arsenal, Southampton from indexed official table rows; direct page returned navigation |
| Serie A | 20 | Points only | Indexed official communication 247, 26 May 2025; direct PDF retrieval failed |
| La Liga | 1 | Played, W/D/L, GF/GA, points | Barcelona annual report; played derived from the reported W/D/L sum |
| Ligue 1 | 18 | Played, W/D/L, GF/GA, points | Official PSG club table has 2024-25 URL but a 2026-27 selector heading; all rows provisional |

There are **300 compared metric cells, with zero differences**. Of those, 174 cells in 42 club references have reviewed primary evidence; 126 cells in 18 French references remain provisional. Matching values do not resolve the French source's season-heading conflict.

Across all eight research seasons, the coverage report lists all 780 club-seasons: 60 have reference data, including the 18 provisional rows; 720 have no reviewed reference yet. Within 2024-25, 38 of 98 clubs have no reference in this pass. Each row explicitly lists checked and unchecked metrics. These counts are not a certification of all seasons or statistics. Official rankings, head-to-head tie-breaks, deductions and historical COVID standings policies remain unimplemented.

Primary references:

- [Bundesliga 2024-25 table](https://www.bundesliga.com/en/bundesliga/table/2024-2025).
- [Premier League final matchweek table](https://www.premierleague.com/en/tables/premier-league/2024-25/matchweek-38).
- [Serie A final points communication](https://img.legaseriea.it/vimages/68347c5e/247%20-%20classifica%20Serie%20A%20Enilive%202024-2025.pdf).
- [Barcelona 2024-25 annual report, page 10](https://www.fcbarcelona.com/fcbarcelona/document/2025/11/19/7b34fa91-c770-4ca9-8b07-0c8f24d52cb2/MEM_2024_25_ENG.pdf).
- [PSG club-published table, provisional season metadata](https://www.psg.fr/football-masculin/classements/season/2024-25).

The private factual transcription is `data/raw/standings_references/2024-25_primary_transcription.json`. Its SHA-256 is recorded in the audit output and SQL records. This file archives our transcription and evidence notes, not the original HTML/PDF. No open redistribution license is claimed for those reference pages. Subsequent corrections should be separately versioned evidence files rather than overwriting this input.

## Administrative result discovered

Union Berlin–Bochum, 14 December 2024, finished 1-1 on the field but was awarded 0-2 to Bochum. The OpenFootball snapshot already stores 0-2; our standings totals therefore agree with the official table. The [Union Berlin appeal report](https://www.fc-union-berlin.de/de/meldungen/union-gegen-bochum-wird-mit-02-gewertet-UkLA0t) and Bundesliga table footnote corroborate the distinction.

`futwar.administrative_result_evidence` preserves both scores and source links, tied to the existing match ID. It does not overwrite `match_results`. Awarded results can affect official points and goal totals without representing player-produced goals. Later contribution modeling must explicitly decide which outcome concept it needs. One reviewed event is not evidence that no other administrative fixtures exist.

## Player identity and transfer audit

The processed file has 22,418 player-team records, with names, birth years, nationality labels and club/league/season context. It contains no player-ID or profile-URL columns. The audit found:

- 7,185 distinct name-and-birth-year groups. These are candidate groups, not verified unique players.
- 48 name labels associated with multiple known birth years.
- 3 records missing birth year and 10 missing nationality.
- 1,044 same-season candidate groups appearing at multiple clubs.

`possible_transfers.csv` lists the relevant output record numbers and club contexts. It deliberately labels every group `possible_transfer_or_name_collision_unverified`. Same names can identify different people; birth years can also be wrong or insufficient to disambiguate. Club changes alone do not establish transfer dates, loans, fees, squad eligibility or double-counting policy. The report's output record numbers are one-based processed-record ordinals and can be joined to existing lineage/context records; the run records the processed-file SHA-256.

One research example supports the usefulness of this queue: it includes Abdukodir Khusanov at Lens and Manchester City in 2024-25. [City's signing announcement](https://www.mancity.com/news/mens/abdukodir-khusanov-signing-manchester-city-63872982) confirms the move from Lens, and [his official profile](https://www.mancity.com/players/abdukodir-khusanov) gives a 2004-02-29 birth date and January 2025 arrival. This is an illustrative primary-source check, not an imported identity mapping or a claim that all candidate transfers are verified. A profile URL is an evidence link, not a guaranteed stable cross-provider ID.

## Reproduce in PowerShell

From the project root with Docker running:

```powershell
py scripts/audit_standings_and_identity.py
docker compose exec -T postgres psql -U futwar -d futwar -f sql/012_standings_reference_audit.sql
py -m unittest discover -s tests -v
```

If `py` is unavailable, use the interpreter tested on this machine:

```powershell
py scripts/audit_standings_and_identity.py
```

Generated, ignored outputs are in `reports/standings_identity/`: metric comparisons, full club-season reference coverage, possible transfers and `run.json`. Ignored import exports are in `data/processed/postgres/`. `012` follows the normalized core and imports 60 reference rows and one administrative event. Repeating it inserts zero additional records; changed evidence under the same hash is rejected. Reference versions remain separate rows rather than silently superseding previous evidence.

Inspect discrepancies in PowerShell:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -c "SELECT league, season, team, metric, calculated_value, reference_value, difference FROM futwar.standings_reference_comparison WHERE difference <> 0;"
```

An empty discrepancy result means checked values agree. Consult the coverage report to see what was never checked. All 26 Python tests pass; the normalized-core integration checks still pass after the additive evidence import.

## Work remaining

Obtain unambiguous historical standings references for the missing clubs/metrics, resolve the French heading conflict, and extend the same evidence pipeline to 2017-18 through 2023-24. Record deductions and awarded results as separate evidence. For player identity, evaluate a permitted source with durable IDs and richer biographical evidence, then review a sample of transfer/collision candidates before constructing a players table. Until that matching policy is supported by evidence, retain player-team records separately.
