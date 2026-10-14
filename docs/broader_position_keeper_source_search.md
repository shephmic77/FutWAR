# Broader historical position and goalkeeper source search

Reviewed 2026-10-10 following the owner's decision to search for broader data before a StatsBomb pilot. This is a documentation and literature search, not a row-level completeness audit or source adoption. No account, purchase, provider message, new service integration or player-data merge was performed.

## Outcome

No inspected source establishes complete permitted coverage of historical played positions, including LB/RB/LWB/RWB distinctions and substitutes, plus detailed goalkeeper performance across all 40 target league-seasons. This is a finding about this search, not proof that such data do not exist.

| Candidate | Evidence found | Main unresolved issue | Current status |
|---|---|---|---|
| Sportmonks API v3 | Historical season endpoints, detailed lineup positions and keeper-stat types | Published position list has no explicit LWB/RWB; all 40 cells, substitutes' roles and advanced keeper values untested | Commercial candidate; no credentials or sample audit |
| API-Football | Starting-lineup grid, player saves/conceded goals, league-season coverage flags | Grid is nominal starting arrangement; actual roles, historical backfill and keeper detail untested | Account/API candidate; no credentials or sample audit |
| Wyscout public research dataset | Published Big Five 2017-18 event collection with CC BY 4.0 | Only five target cells; position-frequency evidence and keeper fields untested | Free bounded audit candidate, not full-scope solution |
| Münster goalkeeper study archive lead | Authors report match-level PSxG for our exact leagues/seasons | No public replication dataset located; permission, definitions and completeness unresolved | Research/access lead only |
| DFL integrated tracking/events research dataset | Seven matches with synchronized coordinates/events and CC BY 4.0 | Far too small for seasonal labels or eight-season coverage | Later method-validation lead |

## Commercial/API candidates

### Sportmonks

The [lineup guide](https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/lineups-and-formations) describes fixture lineups and detailed positions. However, the inspected [position vocabulary](https://docs.sportmonks.com/v3/definitions/types/lineups-positions-and-formations.md) lists fullbacks, center backs and several midfield/attacking positions without explicit left/right wingbacks. A formation-based inference would need separate approval and validation; it cannot silently replace played-role evidence.

The [player-stat definitions](https://docs.sportmonks.com/v3/definitions/types/statistics/player-statistics.md) include saves, inside-box saves, minutes and goalkeeper goals conceded. No post-shot expected-goals field was identified on that page; this does not establish absence from every product. A glossary mentioning a metric would not prove populated historical data.

[Season access](https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/leagues-and-seasons/seasons) depends on the subscription. Older [season documentation](https://docs.sportmonks.com/v3/endpoints-and-entities/endpoints/seasons) warns of incomplete historical migration; the [API FAQ](https://docs.sportmonks.com/v3/faq/api-3.0) says migration is completed with possible statistical gaps. These differing statements reinforce the need for actual samples. [Provider integrity guidance](https://www.sportmonks.com/integrity-support/) discusses storing data inside products; applicable subscription terms, continued retention and portfolio sharing still need review before acquisition. No plan or price is recommended.

### API-Football

The [provider's grid announcement](https://www.api-football.com/news/post/players-positions-on-the-grid) dates this feature to June 2021. It does not establish backfill into 2017-18. The [current getting-started guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide) describes starter grid coordinates, with availability caveats. They are not observed tactical-role intervals or substitute roles.

The [coverage guide](https://www.api-football.com/news/post/how-to-optimize-api-sports-calls-and-quota-usage) requires checking league-season coverage flags and cautions that enabled coverage is not a per-match guarantee. A [provider match-report example](https://www.api-football.com/news/post/fifa-world-cup-2026-group-stage-recap-and-complete-match-reports-with-api-football) includes individual saves and goals conceded, demonstrating schema capability only. It does not validate keeper statistics for our historical leagues. Exact terms and historical access have not been established; the main documentation endpoint returned no readable content through the research tool.

## Free and academic leads

The authors' [Wyscout data paper](https://www.nature.com/articles/s41597-019-0247-7) describes public 2017-18 Big Five event data under CC BY 4.0. The [author repository](https://github.com/jonpappalord/soccer_logs_exploration) corroborates scope and links the [Figshare collection](https://figshare.com/collections/Soccer_match_event_dataset/4415000/2). This is five of our 40 target cells, based on published scope, not locally audited files. Event coordinates identify where an action occurred; they cannot alone establish the player's LB/LWB role. The legacy public release must not be assumed to have every field in today's commercial Wyscout API. No files acquired in this search.

[Böttger and Vischer's March 2026 discussion paper](https://www.wiwi.uni-muenster.de/io/sites/io/files/forschen/downloads/dp-io_03-2026.pdf) reports match-level goalkeeper PSxG across the Big Five in 2017-18 through 2024-25. The authors describe collecting FBref data before January 2026, and a filtered sample of 932 keeper-seasons. That count is not a full keeper census. No replication download was located in the paper or this targeted search. An author-held archive could be useful only if access and reuse are permitted; no author was contacted. Their eligibility rules or formula are not adopted for FutWAR.

The [DFL research data descriptor](https://www.nature.com/articles/s41597-025-04505-y) describes seven first/second-division matches with synchronized tracking and events under CC BY 4.0. It offers a later way to validate role methods, not broad historical coverage or enough appearances to apply the secondary-position rule. No tracking files acquired.

## Next acquisition gate

Keep the existing raw data and the owner's position rule unchanged. Before merging a candidate:

1. Establish applicable terms, historical access and retention/publication permissions.
2. Check each of the 40 league-season cells separately for matches, appearances, positions and each keeper statistic. Use explicit `not_audited` rather than a completeness claim for inaccessible cells.
3. Compare an early and late season, starters and used substitutes, and documented fullback/wingback role changes. Validate the field's meaning before counting positions.
4. Check keeper minutes, shots faced, saves, goals conceded/own-goal treatment and opportunity denominators. Audit post-shot metrics separately from pre-shot xG.
5. Resolve cross-provider player/club identities and conflicting definitions before joining.

Recommendation pending the owner's cost/access preference: a free Wyscout metadata/schema audit is a concrete next step, but it cannot complete the eight-season data. Provider sampling or contacting the study authors requires a separate owner decision. Do not relax positions, infer missing values or finalize a contribution formula to bridge the gap.

Owner follow-up: free sources only for now. The subsequent [local Wyscout audit](wyscout_research_audit.md) supersedes the unsampled status above: all five 2017-18 domestic cells have matches/events, but specific played positions and post-shot xG remain unavailable in the inspected fields. No paid provider was adopted.
