# Public Wyscout research-release audit

Audited 2026-10-10 after the owner chose free sources only. This acquisition is limited to the published research release; no commercial API, account or scraper was used. Raw files are unchanged and private. No player labels, replacement baseline, keeper values or database joins were created.

## Provenance and reproducibility

The [Figshare collection](https://figshare.com/collections/Soccer_match_event_dataset/4415000) supplies six inspected articles: Players, Competitions, Matches, Events, and mappings of event/tag identifiers. Each archived article's metadata declares CC BY 4.0. `data/wyscout_research_manifest.json` records article versions, licenses, download URLs, retrieval timestamps, publisher MD5 and local SHA-256. Metadata are also archived and hashed. Attribution: Pappalardo et al. (2019), [A public data set of spatio-temporal match events in soccer competitions](https://www.nature.com/articles/s41597-019-0247-7), DOI 10.1038/s41597-019-0247-7; Pappalardo and Massucco, Figshare collection DOI 10.6084/m9.figshare.c.4415000. The public research license does not confer rights to other Wyscout products.

The archive includes international tournaments, but the audit reads only the five domestic JSON members. ZIPs are read directly without extracting arbitrary member paths. Acquisition verifies publisher size/checksum and pins registered article metadata; reruns verify local hashes instead of replacing existing files.

## Measured domestic coverage

| League, 2017-18 | Clubs | Matches | Event records | Matches without events |
|---|---:|---:|---:|---:|
| Premier League | 20 | 380 | 643,150 | 0 |
| La Liga | 20 | 380 | 628,659 | 0 |
| Serie A | 20 | 380 | 647,372 | 0 |
| Bundesliga | 18 | 306 | 519,407 | 0 |
| Ligue 1 | 20 | 380 | 632,807 | 0 |
| Total | 98 | 1,826 | 3,071,395 | 0 |

All domestic match dates fall within July 2017 through June 2018. Every recorded team has an 11-player starter list. Observed match counts agree with the expected schedules, but individual events have not been certified against video or official match reports. Presence of events does not prove all actions were recorded correctly.

The generated coverage report includes all 40 target cells. The other 35 are explicitly absent from this release. This archive cannot establish eight-season completeness.

## Position evidence

The 3,603 player profiles across the entire archive carry four role categories: GK (426), DF (1,200), MD (1,257), FW (720). These profile counts include the international competitions and are not a Big Five player census.

Domestic starter and bench rows have only player ID, goals, own goals and card fields. There are no specific position fields in those rows. The object named `formation` contains starter/bench/substitution lists, not an observed role history. Player profiles do not establish seasonal position frequencies.

Event `positions` are x/y action coordinates. They cannot directly label LB versus LWB, distinguish a player's substitute role, or establish the owner's 5-appearance/10% secondary-position rule. No specific-position labels have been assigned.

## Goalkeeper evidence and quality flags

Observed events include Save attempt/Reflexes, Save attempt/Save attempt, Goalkeeper leaving line, goal kicks, hand passes, launches and other distribution actions. These support a bounded goalkeeper-method research pilot after definitions and outcomes are validated. A save attempt is not automatically a successful save; leaving the goal line is not automatically a successful sweep or claim.

No xG or post-shot xG fields were identified in the domestic event schemas. Tag definitions include shot outcomes and goal-mouth regions, but those are not supplied calibrated probabilities. Any new expected-goals model would be a separate research decision. No PSxG values or save percentages were manufactured.

Checks found zero duplicate event IDs within each league, zero event links outside that league's match archive, zero unknown nonzero player IDs and no empty coordinate lists. Coordinate accuracy, event timing, outcome-tag logic, keeper exposure and save/goal reconciliation remain unvalidated.

226,038 event records use player ID 0. These are retained and reported; they must not be silently assigned to a player. Unattributed records may reflect event types such as interruptions, so this count is not automatically a missing-player error count.

25 events of goalkeeper-action types lack a GK profile link (3 Premier League, 3 La Liga, 5 Serie A, 4 Bundesliga, 10 Ligue 1): 21 link to non-GK profiles and four use player ID 0. The review queue preserves IDs, names, role metadata, periods and timestamps. Possible explanations include an outfield player acting as keeper, source attribution issues or profile limitations; none has been adjudicated. Profile-based goalkeeper event counts are diagnostics, not final classifications.

## Execution and checks

From the project root in Windows PowerShell:

```powershell
py scripts/acquire_wyscout_research.py
py scripts/audit_wyscout_research.py
```

Ignored outputs under `reports/wyscout_research/` are `coverage.csv`, `summary.json` and `keeper_role_review.json`. The audit validates hashes, competition IDs, match-ID uniqueness, dates and event links before reporting success. It was run successfully across the five leagues; rerun after adding the keeper-role review queue. There is no inference or merge into the existing player-season dataset.

## Implication for FutWAR

Keep this as an auditable 2017-18 event research source. It does not solve historical specific-position labeling or the full-scope goalkeeper data gap. Continue free archive research for the remaining seasons and detailed keeper measurements. A separate decision is needed before constructing a keeper model, inferring roles from action locations, or reducing the project's scope. The owner's position rule remains unchanged.
