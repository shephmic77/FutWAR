# Match-results coverage audit

## Source selection and reproducibility

Football-Data.co.uk was checked first. Its [current data page](https://www.football-data.co.uk/data.php) limits use to private individuals and specifically restricts automated bots/scrapers/AI for commercial/data-training products; it also describes league-prediction purposes. It was not downloaded. These are provider statements, not a legal opinion.

Instead, this audit uses the [OpenFootball football.json repository](https://github.com/openfootball/football.json), whose [license](https://github.com/openfootball/football.json/blob/master/LICENSE.md) is CC0-1.0. Its data are community-maintained, not an official league feed. Independent here means acquired from a separate source; statistical independence of upstream providers is not established.

Pinned commit: `e6744429ee395bc86f247348c6184bb08d4eb361`. One 1,659,826-byte archive was retrieved; original bytes, download timestamp and SHA-256 are preserved under ignored `data/raw/openfootball/<commit>/`. Only the 40 scoped files plus license and README were extracted using explicit safe paths. `data/openfootball_manifest.json` records fingerprints and provenance. Existing source files are checked against fingerprints and never overwritten.

PowerShell reproduction from the project root:

```powershell
py scripts/acquire_openfootball.py
py scripts/audit_match_results.py
docker compose exec -T postgres psql -U futwar -d futwar -f sql/007_match_results_audit.sql
py -m unittest discover -s tests -v
```

## Results

All 40 league-season files are present. They contain 14,339 valid scored results. No duplicate directed club-pair fixtures, invalid scored results or invalid dates were found. There are 121 fixtures without full-time scores; these are not converted into 0-0 draws or counted as completed matches.

| League / season | Scored matches | Full double-round-robin benchmark | Interpretation |
|---|---:|---:|---|
| Ligue 1 2019-20 | 279 | 380 | 101 unscored fixtures; shortened-season context requires distinction from data gaps |
| La Liga 2024-25 | 370 | 380 | Final round's ten fixtures have no scores in this snapshot |
| Serie A 2024-25 | 370 | 380 | Final round's ten fixtures have no scores in this snapshot |
| Other 37 league-seasons | Equal to benchmark | 306 or 380 | Structural count check passes, not full statistical accuracy certification |

The benchmark is observed club count times (club count minus one), assuming home-and-away league fixtures. It is a schedule diagnostic, not an imputed count of played matches. It does not certify extra playoffs or every competition convention.

## Club identity and exposure comparison

`data/club_aliases.json` explicitly records name-label correspondences, including FC suffixes, abbreviations, translated names and historical naming variants. No fuzzy matching is applied. After alias matching, all 780 club-season groups align with the player data, and each league-season mapping is one-to-one. The SQL mapping contains 190 distinct league/name-label pairs, including exact labels. These remain source labels, not final stable cross-provider club IDs; the aliases can be reviewed in the JSON and `reports/match_audit/club_comparison.csv`.

For each club, compare summed player starts with eleven starters per scored match. Exactly 40 club-season groups disagree, all in the two incomplete 2024-25 files: each club has 418 recorded player starts versus 407 implied by 37 scored matches. Every other club-season group agrees exactly (740 groups), including the clubs with 27 or 28 recorded Ligue 1 2019-20 matches.

This supports the player-start exposure aggregates and points to the match snapshot's final-round score gaps. It does not resolve individual identity errors, the O'Neill discrepancy, advanced-stat accuracy or match-level player participation. Equal totals can still conceal offsetting errors.

Minutes are also compared with an eleven-players-times-90-minutes benchmark. In Ligue 1 2019-20, each club's recorded minutes falls between 0% and 1.1255% below that benchmark. Red cards, time conventions and source recording can affect this diagnostic; no missing minutes have been invented. A close minutes total is not proof of player-level completeness.

## Files and SQL

Audit reports are in ignored `reports/match_audit/`: league-season coverage, score/date issues, club-label comparison and club-level starts/minutes comparison. Derived results and import files are in ignored `data/processed/match_results/`. Full source and player data remain unchanged.

SQL staging: `futwar.match_results_stage` stores scored candidates, `futwar.club_label_map` keeps explicit source-label mappings, and `futwar.source_files` stores each source file's commit/license/acquisition provenance. The `futwar.match_team_coverage` view joins results to player exposure; `futwar.match_season_coverage` summarizes the comparison. Views select the pinned source snapshot so future versions are not silently counted twice.

The SQL import completed: 40 source files, 14,339 scored results and 190 name-label mappings. It uses a transaction and fixed-source conflict handling; updated snapshots or mappings require deliberate version handling. All 16 regression tests passed, including missing-score handling, noninteger/negative scores, invalid dates and duplicate fixture detection.

Try this single command directly in PowerShell:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -c "SELECT * FROM futwar.match_season_coverage WHERE difference_from_benchmark <> 0 ORDER BY season, league;"
```

## What remains

Recover and independently verify the 20 final-round scores for Spain and Italy 2024-25 using a permitted compatible source, preserving original OpenFootball inputs and documenting any supplements. Keep the cancelled/unfinished Ligue 1 2019-20 fixtures distinguishable from missing scores for matches that actually occurred. No season exclusion, score filling, player-value formula or league-strength estimate has been applied. Domestic match coverage alone cannot establish absolute cross-league strength; European competition links remain a later requirement.

## Follow-up: verified supplementation

The source gaps described above remain in the immutable baseline snapshot. All 20 missing final-round scores have now been verified and loaded separately; see `docs/verified_match_supplement.md`. The effective SQL coverage views include these results and now show agreement across all 780 club-season starts comparisons. Ligue 1 2019-20 remains unchanged.
