# Player identity source audit and reviewed pilot

We acquired six public CSV exports from [dcaribou/transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets): competitions, clubs, players, games, appearances and transfers. The publisher documents these downloads and declares CC0-1.0. This is a publisher license declaration; upstream rights were not independently confirmed. No Transfermarkt scraping occurred, and raw/processed data remain excluded from Git. Download URLs, retrieval timestamps, sizes and SHA-256 hashes are preserved in `data/player_identity_source_manifest.json`.

The published snapshot extends beyond our research period. All historical game and appearance calculations here are restricted to the Big Five domestic competition IDs and season-start years 2017 through 2024. Current club, current market value and later-season performance are not used for historical matching or modeling.

## Measured coverage and quality

| Measure | Result |
| --- | ---: |
| Provider player profiles, all competitions/years | 50,149 |
| Provider club profiles | 796 |
| Scoped league-seasons | 40 |
| Scoped games | 14,359 |
| Scoped appearance records | 422,080 |
| Scoped games without appearance records | 0 |
| Scoped appearances missing minutes, goals or assists | 0 |
| Scoped appearances without a player profile | 0 |
| Scoped appearances whose profile lacks birth date | 113 |
| Scoped minutes outside 0–120 | 0 |
| Exact fixture-date-and-club matches | 14,287 |
| Fixture-date disagreements | 72 |

Every league-season game count agrees with the existing standings benchmark. All 14,359 games also map to the same unique home/away club pair within their league-season, and their scores agree. However, 72 dates differ between providers. `fixture_discrepancies.csv` preserves both dates. The fallback club-pair comparison is a diagnostic, not a silently accepted date correction or imported match-ID mapping. Resolve these dates against primary fixture evidence before joining appearance rows to our match IDs.

Provider player IDs, club IDs and game IDs are unique. Scoped appearance IDs are unique; their competition IDs and historical player-club IDs agree with their game records. None of the source's appearance rows refer to an unknown game ID. Population and structural consistency do not prove that every player appearance or statistic is accurate. Providers can define minutes and assists differently; no numerical player stats were overwritten.

The 40-row `coverage.csv` reports game counts, appearance records and missingness for minutes, goals, assists and cards, plus profile/birth-date availability and transfer counts. These basic appearance fields do not replace the original source's advanced attacking, defensive or progression statistics. Nominal formation/position fields are not verified tactical roles.

## Candidate identity method

Names are case-folded, accents removed and whitespace normalized. Full names must then match exactly; no fuzzy or surname-only assignment occurs. A known birth year must agree with the provider's full birth date. Finally, historical appearances must support the same club, league and season. Current-club fields are ignored.

Club correspondence uses existing explicit Wikipedia aliases plus 103 reviewed provider-name aliases in `data/identity_club_aliases.json`. Mappings must fit every observed club season, and conflicting IDs for a canonical club fail. These are local source correspondences, not independently certified club legal histories.

For the original 22,418 player-team records:

- **20,521** have one candidate supported by exact normalized name, birth year and historical appearance context.
- **1,894** have no supported exact-name candidate.
- **3** lack birth year.

These are record counts, not unique players. Every automated result retains a blank verified-player field. Unmatched names may reflect aliases, different spellings, missing provider appearances or incorrect original records; no identity is guessed. The method's false-match rate has not been estimated from a representative labeled sample. Five positive pilot examples do not establish general matching precision.

## Reviewed five-player pilot

Only five researched identities and eight specific processed records are loaded into PostgreSQL:

| Player | Provider ID | Reviewed records | Primary biographical evidence |
| --- | --- | ---: | --- |
| Aaron Lennon | 14221 | 2: Everton/Burnley 2017-18 | [Premier League profile](https://www.premierleague.com/en/players/17349/aaron-lennon/stats), birth 16 April 1987 |
| Abde Ezzalzouli | 724520 | 2: Barcelona/Betis 2023-24 | [Betis announcement/profile evidence](https://www.realbetisbalompie.es/noticias/primer-equipo/abde-nuevo-jugador-del-real-betis-29389), birth 17 December 2001 |
| Abdukodir Khusanov | 763079 | 2: Lens/Manchester City 2024-25 | [City profile](https://www.mancity.com/players/abdukodir-khusanov), birth 29 February 2004 |
| Jude Bellingham | 581678 | 1: Dortmund 2022-23 | [Real Madrid profile/history](https://www.realmadrid.com/en-US/football/squad/jude-bellingham), birth 29 June 2003 |
| Alessandro Bastoni | 315853 | 1: Inter 2024-25 | [Inter profile](https://www.inter.it/it/squadra/prima-squadra/giocatore/alessandro-bastoni), birth 13 April 1999 |

Official links corroborate biographical and club-history evidence; provider IDs come from the archived publisher profiles, not from official clubs. Reviewed aliases such as Abde/Abdessamad Ezzalzouli are supported by the primary references. The source review JSON is `data/raw/identity_reviews/pilot_2026-10-10.json`. It pins the processed input hash, identifies only these eight output ordinals, and preserves the evidence URLs and review date. The exporter rejects changed birth dates or unsupported candidates.

The three sample club changes are also corroborated by [Burnley's Lennon announcement](https://burnleyfootballclub.com/content/clarets-complete-lennon-deal), [Barcelona's Abde transfer announcement](https://www.fcbarcelona.com/en/football/first-team/news/3664527/agreement-with-betis-for-the-transfer-of-ez-abde) and [City's Khusanov announcement](https://www.mancity.com/news/mens/abdukodir-khusanov-signing-manchester-city-63872982). The publisher records the Abde move on 1 September 2023 and Khusanov move on 20 January 2025. It contains **no transfer rows for Lennon**, demonstrating a gap even for an independently confirmed move. Announcements and transfer registration dates are not assumed interchangeable in general.

The pilot's `players` table has five opaque local IDs and status `reviewed_pilot_identity`. `player_source_ids` maps publisher IDs and stores biography evidence. `reviewed_player_record_links` links eight original processed records through foreign keys to the existing context bridge. `reviewed_player_seasons` is a read-only joined view retaining original player labels and minutes. Other records are neither merged nor silently linked. Full birth dates are new evidence on the player entity, not edits to the raw birth-year column.

## Transfer limitations

The transfer file contains 175,165 rows across all competitions and years. Of those, 475 are dated after retrieval; they are excluded from historical transfer coverage and not treated as completed moves. They may reflect scheduled loan returns or other prospective records, but no individual explanation has been verified.

Among scoped provider player-seasons with appearances at multiple clubs, **214** lack a transfer row for the corresponding declared transfer season. The gap report includes provider ID, season and club contexts. This is a coverage warning, not proof of 214 missing real transfers: source season conventions, loans, promotions or data errors can affect the comparison. Transfer-count coverage is reported separately for every league-season. Some retiree histories are absent, as the Lennon example shows. Do not treat the published transfer table as a complete ledger or treat fees/market values as contribution measures.

Minute differences also remain explicit. For example, Lennon's Burnley record has 1,118 original minutes versus 1,124 provider appearance minutes; Khusanov at City has 503 versus 504. These differences do not invalidate identity by themselves and do not justify overwriting the original exposure. Exact minute agreement is not a matching criterion.

## Reproduce on Windows PowerShell

Run from the project root with Docker running:

```powershell
py scripts/acquire_player_identity_source.py
py scripts/audit_player_identity_source.py
py scripts/prepare_identity_pilot.py
docker compose exec -T postgres psql -U futwar -d futwar -f sql/014_player_identity_pilot.sql
py -m unittest discover -s tests -v
```

Use the explicit Python interpreter from the earlier guides if `py` fails. These scripts use the standard library. The audit also requires the earlier standings coverage reports and normalized match-results view. Files already acquired are hash-verified and reused. Refreshes require a separately versioned snapshot; original raw files are not overwritten.

Generated outputs are in ignored `reports/player_identity/`: `coverage.csv`, `identity_candidates.csv`, `fixture_discrepancies.csv`, `transfer_coverage_gaps.csv`, sample transfer rows and `run.json`. The automatic audit summary reports zero verified IDs assigned because it creates candidates only; the separate pilot exporter reports five researched identities/eight links. Import exports are ignored in `data/processed/postgres/`.

The SQL import is transactional. Repeat imports preserved five players/eight links and inserted zero duplicate links. All 36 regression tests passed; the normalized-core validation still passes. Raw player data retain their original fingerprint. Example SQL:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -c "SELECT display_name, league, season, team_name, minutes FROM futwar.reviewed_player_seasons ORDER BY display_name, season, team_name;"
```

## Next work

Review a broader, stratified identity sample including common-name collisions, missing birth years and unmatched aliases. Investigate the 72 fixture dates before importing match appearances into the core. Resolve selected transfer-history gaps individually using primary evidence. Expand reviewed identities only after recording support and measuring matching errors. Player-value and replacement modeling remain undecided.
