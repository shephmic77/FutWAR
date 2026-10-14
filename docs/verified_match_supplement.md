# Verified final-round match supplement

The 20 unscored fixtures in the pinned OpenFootball snapshot have been supplemented with full-time scores from official league and club sources. La Liga and Serie A 2024-25 each now have 380 scored results in the effective view. All 780 club-season player-start totals match eleven starters per played fixture. These checks establish structural exposure agreement, not universal player-stat accuracy.

The original OpenFootball files and player CSV are unchanged. The original result staging table still holds 14,339 results; the separate `futwar.match_result_supplements` table holds 20 sourced results. `futwar.match_results_effective` combines them into 14,359 results, identifying each row's origin and source URL. Ligue 1 2019-20 remains at 279 played matches; no cancelled fixtures were filled.

## Evidence

Spanish results were checked against [La Liga's official 2024-25 matchday 38 page](https://www.laliga.com/laliga-easports/resultados/2024-25/jornada-38). Italian results were checked against official Lega Serie A reports, except Como-Inter, checked against [Inter's official match centre](https://www.inter.it/en/match_center/5285). Individual Italian report URLs are stored alongside each record in the ignored raw supplement and SQL evidence table.

| League | Date | Home (player-source label) | Away | Score |
|---|---|---|---|---|
| La Liga | 2025-05-23 | Betis | Valencia | 1-1 |
| La Liga | 2025-05-24 | Real Madrid | Real Sociedad | 2-0 |
| La Liga | 2025-05-24 | Leganés | Valladolid | 3-0 |
| La Liga | 2025-05-24 | Espanyol | Las Palmas | 2-0 |
| La Liga | 2025-05-24 | Alavés | Osasuna | 1-1 |
| La Liga | 2025-05-24 | Getafe | Celta Vigo | 1-2 |
| La Liga | 2025-05-24 | Rayo Vallecano | Mallorca | 0-0 |
| La Liga | 2025-05-25 | Girona | Atlético Madrid | 0-4 |
| La Liga | 2025-05-25 | Villarreal | Sevilla | 4-2 |
| La Liga | 2025-05-25 | Athletic Club | Barcelona | 0-3 |
| Serie A | 2025-05-23 | Como | Inter | 0-2 |
| Serie A | 2025-05-23 | Napoli | Cagliari | 2-0 |
| Serie A | 2025-05-24 | Bologna | Genoa | 1-3 |
| Serie A | 2025-05-24 | Milan | Monza | 2-0 |
| Serie A | 2025-05-25 | Atalanta | Parma | 2-3 |
| Serie A | 2025-05-25 | Empoli | Hellas Verona | 1-2 |
| Serie A | 2025-05-25 | Lazio | Lecce | 0-1 |
| Serie A | 2025-05-25 | Torino | Roma | 0-2 |
| Serie A | 2025-05-25 | Udinese | Fiorentina | 2-3 |
| Serie A | 2025-05-25 | Venezia | Juventus | 2-3 |

Only match date, club pair and full-time score have been supplemented. Half-time scores, lineups, roles and advanced measures have not been invented. No open license for the official reference pages or reports has been established; raw supplement records remain ignored by Git. The official sources were read through web tools; local PDF archiving/rendering failed because local DNS could not resolve the report host. URLs and the manually reviewed factual transcription remain recorded. This is not a bulk official-site acquisition pipeline.

## Reproduction and validation

The factual transcription is preserved in ignored `data/raw/match_supplements/2024-25_final_round_verified.json`, with sources and verification date 2026-10-10. Its SHA-256 and the two original file hashes are recorded in `data/match_supplement_manifest.json`. The initial transcription candidate suffered a default-codec decoding error in accented source names and was rejected by exact fixture matching before import. That rejected candidate remains untouched for the audit trail; the verified version explicitly decodes original JSON as UTF-8.

```powershell
py scripts/prepare_match_supplement.py
docker compose exec -T postgres psql -U futwar -d futwar -f sql/008_verified_match_supplements.sql
py -m unittest discover -s tests -v
```

If the `py` launcher is unavailable but the existing Python 3.13 installation is present, use:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" scripts/prepare_match_supplement.py
```

The validator requires exactly the 20 pinned missing fixture keys, matching dates and home/away labels, nonnegative integer scores and source evidence. It rejects additional fixtures, incomplete supplementation, duplicate records and invalid goals. The SQL transaction rejects replacement of existing scored snapshot results and conflicts with previously loaded supplements. Repeating the import was tested: zero additional rows were inserted. All 22 regression tests passed, including a regression for corrupted accented club names. Original source hashes were independently rechecked.

Updated reports: `reports/match_audit/supplemented_season_coverage.csv` and `supplemented_team_coverage.csv`. Earlier baseline audit files continue to describe the unmodified source snapshot.

The historical `007_match_results_audit.sql` re-creates baseline coverage views. When rebuilding from scratch, always run `008_verified_match_supplements.sql` afterwards to restore effective supplemented coverage.

Try this directly in PowerShell:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -c "SELECT league, season, completed_matches, clubs_with_start_discrepancy FROM futwar.match_season_coverage WHERE season = '2024-25' ORDER BY league;"
```

Remaining limitations: O'Neill's conflicting exposure evidence, stable cross-provider player IDs, feature definitions and tactical evidence are unresolved. Club/competition/season normalization and chronological analysis come next; no WAR formula or COVID exclusion has been selected.
