# Historical standings coverage completed

The standings comparison now covers **all 40 league-seasons and 780 club-seasons**, from 2017-18 through 2024-25. Eight fields are compared per club: played, wins, draws, losses, goals for, goals against, goal difference and table points. This closes the earlier reference-coverage gaps using archived secondary tables, with targeted primary evidence for discrepancies. It does not certify every match or player statistic independently.

## Source decision

The [Kenzo911 dataset](https://github.com/Kenzo911/european-football-standings) advertises the required span, but its README says the tables are generated from match results; it would largely repeat our existing calculation, and its root lists no license file. The [Fjelstul English Football Database](https://github.com/jfjelstul/englishfootball) has separately collected standings and a documented CC BY-SA 4.0 license, but covers England only through 2023-24.

We therefore used the permitted [MediaWiki public parsing API](https://www.mediawiki.org/wiki/API:Parsing_wikitext) to archive Wikipedia season articles across all five leagues. Forty requests were made sequentially with one-second spacing and a research User-Agent. Each unmodified API response has a SHA-256, retrieval timestamp, article title, revision ID and permanent source URL in `data/wikipedia_standings_manifest.json`. Subsequent runs reuse and verify the archives. A later refresh should use a new versioned snapshot folder.

Attribution: **English Wikipedia contributors**, individually attributed by article revision links in the manifest and exports. Article content is subject to [Wikimedia's terms](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) and CC BY-SA 4.0. Archived response bytes are unchanged; extracting tables, stripping footnote/status markers and mapping club labels are our transformations. Data and archives remain excluded from Git. Primary reference notes have no claimed open redistribution license.

These are secondary compiled standings, not official league certification. Shared upstream sources may exist; agreement does not establish fully independent collection. The revision identifies the article, while archived bytes and hashes preserve the actual rendered response, including transcluded templates at retrieval. Our 35 explicit nonidentical club-label aliases were reviewed and checked for one-to-one matching in every season. No fuzzy matches or invented provider club IDs were used.

## Findings and resolutions

All 780 rows agree on played, W/D/L, GF/GA and goal difference. Raw table points agree for 771 rows. Nine point differences were reviewed separately:

| League | Season | Club | Match points | Archived table points | Reviewed table points | Explanation |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Serie A | 2017-18 | Lazio | 72 | 71 | 72 | Incorrect secondary points cell |
| Serie A | 2018-19 | Lazio | 59 | 57 | 59 | Incorrect secondary points cell |
| Serie A | 2018-19 | Chievo | 20 | 17 | 17 | Three-point deduction |
| Ligue 1 | 2021-22 | Nice | 67 | 66 | 66 | One effective point deducted |
| Ligue 1 | 2021-22 | Lyon | 62 | 61 | 61 | One-point deduction |
| Serie A | 2022-23 | Juventus | 72 | 62 | 62 | Final ten-point deduction |
| Premier League | 2023-24 | Everton | 48 | 40 | 40 | Six points plus two deducted |
| Premier League | 2023-24 | Nott'ham Forest | 36 | 32 | 32 | Four-point deduction |
| Ligue 1 | 2023-24 | Montpellier | 42 | 41 | 41 | One effective point deducted |

Primary evidence:

- Lazio 2017-18: [Inter's pre-match report](https://www.inter.it/it/notizie/2018-05-19-lazio-inter-tutte-le-informazioni-sul-match) gives 72 points before the final game; [Inter's final-game report](https://www.inter.it/en/news/2018-05-20-inter-are-in-the-champions-league-after-beating-lazio-3-2) establishes Lazio lost it. **Inference from those primary sources:** Lazio therefore finished on 72, not 71.
- Lazio 2018-19: [official Serie A final classification](https://img.legaseriea.it/vimages/16fdc3514751efe9/246_-_classifica_serie_a_tim_2018-2019.pdf) lists 59, available in indexed PDF text.
- Chievo: [FIGC appeal ruling](https://www.figc.it/it/federazione/news/inammissibili-i-ricorsi-di-catania-siena-e-pro-vercelli-respinti-quelli-sul-caso-chievo-cesena-foei3m9o) upholds three points for the current 2018-19 season.
- Nice: [LFP ruling, 8 September 2021](https://www.lfp.fr/article/commission-de-discipline-les-decisions-du-8-septembre) specifies two points, one suspended; one was effective.
- Lyon: [LFP ruling, 8 December 2021](https://www.lfp.fr/article/commission-de-discipline-les-decisions-du-8-decembre-2021) specifies one point.
- Juventus: [FIGC revised ruling](https://figc.it/it/federazione/news/caso-plusvalenze-dieci-punti-di-penalizzazione-per-la-juventus-da-scontare-nella-corrente-stagione-sportiva/) specifies ten points; [subsequent settlement](https://www.figc.it/it/federazione/news/procedimento-juventus-ok-al-patteggiamento-con-ammenda-e-rinuncia-ai-ricorsi-lw0t3nuj) records waiver of appeals. The earlier fifteen-point ruling is not the final adjustment.
- Everton: [Premier League final note](https://www.premierleague.com/en/news/4001861) confirms six plus two points.
- Forest: [Premier League appeal decision](https://www.premierleague.com/en/news/3999776/premier-league-statement) confirms four points remain deducted.
- Montpellier: [LFP ruling, 25 October 2023](https://www.lfp.fr/article/commission-de-discipline-les-decisions-du-25-octobre-2023) specifies two points, one suspended; one was effective.

The review notes are separately preserved in `data/raw/standings_references/historical_points_adjudications_2026-10-10.json`, with their own hash in the run and database. Original Wikipedia cells, match scores and player stats remain unchanged. After applying these evidence-backed distinctions, **zero differences remain unexplained**. The initial French primary table's conflicting season heading remains provisional; the newly archived French secondary tables provide a separate, explicit-season comparison rather than upgrading that earlier evidence.

Ligue 1 2019-20 remains shortened, with 279 completed matches and differing club match counts. Published rank is retained as source information. We do not reconstruct points-per-game rankings, tie-break rules or COVID adjustments, and no research seasons have been excluded.

## Implementation and reproduction

The archive acquisition uses the standard library. HTML extraction uses the already-installed Beautiful Soup package; its optional dependency requirement is in `requirements-reference-audit.txt`. If needed, install it with `py -m pip install -r requirements-reference-audit.txt`.

From Windows PowerShell in the project folder, with Docker running:

```powershell
py scripts/acquire_standings_reference_pages.py
py scripts/audit_historical_standings.py
docker compose exec -T postgres psql -U futwar -d futwar -f sql/013_historical_standings_audit.sql
py -m unittest discover -s tests -v
```

Use the explicit Python interpreter path from the earlier audit guide if `py` is unavailable. SQL `013` follows the normalized core and preserves existing tables. It imports 780 references and nine adjudications with club-season foreign keys, rejects altered exports under an existing source hash, and fails on unmatched, multiplied or unexplained comparisons. Repeating it inserted zero additional records. Views retain source versions; future multiple snapshots or reviews require an explicit version selection policy before aggregating.

Generated reports in `reports/historical_standings/` contain all club comparisons, the nine original discrepancies with their resolutions, and the run summary. The export uses `official_points` for the source-reported cell; SQL deliberately calls it `reported_table_points` because source errors are possible. Reviewed values are separate columns. No field is silently replaced with a calculated number.

Try the resolved differences:

```powershell
docker compose exec -T postgres psql -U futwar -d futwar -c "SELECT league, season, team, earned_match_points, reported_table_points, reviewed_table_points, evidence_classification FROM futwar.historical_standings_comparison WHERE evidence_classification <> 'matches_secondary_reference' ORDER BY season, league, team;"
```

All 31 regression tests passed, including extraction ambiguity, invalid accounting, preserved deduction values and reference-error separation. The normalized-core database checks still pass, and the raw player CSV retains its original SHA-256. This supports progressing to player identity matching; it does not validate a WAR formula.

## Next data gap

Player identities and transfer candidates remain unresolved. The [dcaribou Transfermarkt dataset](https://github.com/dcaribou/transfermarkt-datasets) documents provider IDs and joined player, appearance and transfer tables and a publisher CC0 license. It is a promising next audit candidate, not yet downloaded or proven complete across our scope; source rights, actual historical coverage and identity matching still need checking. Its publisher currently reports updates paused after July 2026, which is outside our historical scope but worth recording. Current-club fields must never be substituted for historical club membership. Market values are not player contribution.
