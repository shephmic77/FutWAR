# Replacement-cost source screen — 2026-11-05

## Decision

No free, consistently reusable source located in this screen supports a factual team-accessible replacement pool across all 40 Big Five league-season cells (2017–18 through 2024–25). Keep the team-budget comparison unavailable as a numeric player metric until season-specific access and annualized cost can be evidenced. Do not infer a player's affordability from market value, a transfer fee by itself, or a club's later financial statements.

This is a targeted source screen, not a claim that no such private or unpublished records exist. No new salary or contract data were downloaded, scraped, transcribed, or added to the project.

## Sources reviewed

| Source | What it can support | Limits for FutWAR |
|---|---|---|
| [Footy Cap data feed](https://footycap.com/data-feed/) | Free download; the publisher permits reuse with a visible link to Footy Cap and retention of each underlying source. Its 2026-11-03 build lists 480 clubs and 8,144 cited figures, including club wages where sourced. | Underlying figures retain their own source rights and must be checked. The local audit found wages for 94/96 clubs in the feed's current Big Five club list, but its historical transfer-history matching covered only 144/780 target club-season slots (18.5%) and none in Ligue 1. Neither current wage values nor selectively matched historical transfer spend establish a historical player pool or season-start affordability. See [the local feed audit](reep_footycap_feed_audit_2026-11-04.md). |
| [Capology salary API documentation](https://www.capology.com/documentatie/api/v2/salarissen/) and [support/pricing](https://www.capology.com/pricing/api-plans/) | Historical season and player/club salary endpoints exist; the API documentation lists paid subscription tiers for salary access. | Not a free downloadable open dataset. Site estimates may not include all bonuses or contract costs; the project does not have a public redistribution basis for the data. No data were acquired. |
| [Capology scraper used by a LaLiga squad-efficiency project](https://github.com/aitorcacciola/football-squad-efficiency/blob/main/capology/docs/capology-salary-data-guide.md) | Useful methodological example: player × club × season grain, explicit join review, and separation of source tables from derived matching. The repository is MIT-licensed for its own code. | The guide describes extracting figures from Capology page JavaScript. The repository itself warns that MIT does not grant rights to Capology, Transfermarkt, or other third-party content and that users must check current source terms. Its LaLiga project data do not clear a Big Five panel for FutWAR. Do not import its salary files or reuse its scraper as a public data source. |
| [La Gazzetta dello Sport's 2017/18 salary feature](https://www.gazzetta.it/Calcio/Serie-A/06-09-2017/serie-a-campo-ingaggi-gazzetta-vi-svela-nuova-stagione-220388461265.shtml) and a [peer-reviewed Serie A wage study](https://link.springer.com/article/10.1007/s00181-024-02640-w) | Evidence that season-start salary lists have been reported for Serie A; the study uses a ten-season Italian panel and explains that Gazzetta figures are net, while accounts can report gross wage costs. | This is Italy-only, not an open machine-readable Big Five panel. The article is copyrighted, its article page says reproduction reserved, and no open license for redistributing a compiled player-level table was found. Published salary definitions also differ from gross annual employment cost. No tables were transcribed. |
| [FIGC 2025 economic-data archive](https://www.figc.it/it/full-html?path=/federazione/federazione-trasparente/dati-agenti-sportivi/archivio-2025) | Official archive includes separate 2025 Serie A aggregate economic-data files for players and clubs, plus transactions. | One edition/year, aggregate rather than the complete candidate-level wage and contract panel required here, and one league only. It cannot establish all-in costs or candidates available at each historical season start. No files were downloaded. |
| Community and research salary compilations | Can point to definitions, known data limitations, and source leads. | Search results frequently trace to paid Capology, journalistic reporting, Football Manager community files, or scraped Transfermarkt/Capology pages. A repository's code license or a Kaggle uploader's license statement does not grant upstream data rights. None found in this screen provides a verified, openly reusable, complete Big Five player-cost panel. |
| [withqwerty/availability-data](https://github.com/withqwerty/availability-data) | README describes player-matchday statuses (starting, substitute, bench, injured, suspended, national team, and not selected) for six leagues from 2015/16, with player IDs and listed positions. This is a potentially useful availability research lead. | README says data are from Transfermarkt and provided for research/analysis, but declares no explicit open data license. Its weekly scraping and Transfermarkt-derived records do not meet this repository's explicit-open-license source rule. It does not include wage or annualized acquisition cost. **Not downloaded, not used, and not considered cleared for public redistribution or model development.** |

An academic review reports that European soccer salary data are unusually limited and identifies Gazzetta's Serie A reporting as a rare public player-level source. This is supporting context rather than a current exhaustive inventory; the later Italian study independently demonstrates that salary definitions and financial-statement totals are not interchangeable.

## What remains necessary for the team-accessible view

For a candidate to enter a season-specific feasible pool, the record needs all of the following, with source and as-of timing retained:

1. Evidence the player was available to the club in the relevant window (an actual move or directly documented availability, as previously requested).
2. Evidence the player could fill the allowed position scope, with the required season-specific role evidence.
3. Annualized total cost for the selected scenario: salary commitment plus the relevant transfer/loan, signing, and other included costs. Unknown components stay unknown and exclude the player from the central pool.
4. Sufficient exposure and a comparable, independently validated performance estimate. Acquisition alone does not make a player replacement-level.

The seven existing signing/release cases are still workflow examples, not a representative pool. They have unknown salaries and/or all-in costs and span only five of 40 league-season combinations. They remain excluded from a numeric baseline. Team-accessible replacement is therefore an explicitly unavailable comparison, not zero and not an average-player estimate.

## Reproduction and next gate

The existing aggregate audits can be reproduced with:

```powershell
py scripts\audit_public_context_feeds.py
py scripts\audit_replacement_pilot.py --expanded
```

Their row-level and generated outputs remain local/ignored. Do not fetch or scrape salary pages to fill gaps without a clearly reusable source and an auditable acquisition basis. Revisit this gate if a primary league, club, union, or data publisher releases a genuinely reusable historical panel; otherwise preserve the team-budget view as unavailable while advancing the two average-reference research views.
