# Public-data alternatives for the explorer and WAR foundation

**Reviewed:** 2026-10-31
**Decision standard:** use material with a stated public-domain dedication or an explicit open license, and verify that the license covers the underlying data needed for public redistribution. A public download, research use, uploader-selected license, or provider API is not by itself enough.

## Owner's current publication direction

On 2026-10-31, the owner stated that the Kaggle player-stat dataset, Transfermarkt-derived valuation and identity material, player photos and club marks, and the anonymized injury data are acceptable for public use in this personal/student project, and asked to publish the explorer. This supersedes the earlier project decision to keep the explorer offline while reviewing reuse terms. The owner direction is the project's release decision; it does not amend any upstream license or convert a third-party source declaration into an independent legal certification. The deployed app should preserve source attribution and honest coverage/identity limitations.

The earlier source screen below records why these materials were held pending clarification and which narrower alternatives were found. It remains useful provenance history, not a current instruction to block the owner's requested deployment. No replacement was found that simultaneously improves on the current local explorer's 2017–18 to 2024–25 Big Five scope, player statistics, specific played-position evidence, and goalkeeper metrics.

## Source and provenance notes retained from the prior review

| Component | What the local explorer uses | Earlier review note |
|---|---|---|
| Player-season statistics | User-supplied Kaggle file, 22,418 original player-club-season rows | The first audit did not establish upstream provider and row-level provenance. The owner now approves public use for this project; preserve the dataset citation and original Kaggle license metadata. |
| Market values, transfers, player IDs and some profile fields | Transfermarkt-derived exports published by `dcaribou/transfermarkt-datasets` under its own CC0 declaration | The publisher declares CC0; upstream source provenance was not independently confirmed in the first audit. Retain the source link and CC0 attribution, and do not imply Transfermarkt issued that license. |
| Player photographs and club/league marks | Transfermarkt URLs, official club/league marks, and a community crest archive | Keep item-level source credits; marks/photos remain third-party material and the project should not suggest endorsement. |
| Injury context | A separate anonymized Kaggle research dataset | CC BY-NC-SA 4.0, filtered cohort, anonymized identities; keep its attribution/share-alike and non-commercial conditions, and do not join to named player profiles. |

These are distinct issues: replacing the player-stat table does not automatically clear portraits, crests, market values, transfer fees, or injury histories.

## Alternatives that pass a useful, limited reuse screen

| Source | Reuse terms and verified scope | What it can replace | What it cannot replace |
|---|---|---|---|
| [OpenFootball match results](https://github.com/openfootball/football.json) | CC0. The project already audits a pinned snapshot across the 40 Big Five league-season cells from 2017–18 to 2024–25. Current open baseline: 14,339 scored fixtures; 20 played 2024–25 fixtures lack scores in the open files. | Public match results and related team-level descriptive work, with those 20 missing scores plainly flagged. | Player-season performance, player identities, positions, salaries, transfers, or market values. Do not merge the separately researched, non-open 20-score supplement into the public package. |
| [Pappalardo et al. / Wyscout soccer event data](https://figshare.com/collections/Soccer_match_event_dataset/4415000) | CC BY 4.0 is recorded in the project’s prior file-level Figshare audit. Published scope is the complete 2017–18 first divisions of England, Spain, Italy, Germany and France (plus Euro 2016 and the 2018 World Cup). Figshare describes the collection as match events with time, location, outcome, player and event characteristics. | A public, event-based 2017–18 player-action pilot; selected player-season totals and action features can be derived with attribution and provenance. | The other seven seasons, current-specific position minutes, market values, or complete goalkeeper shot-stopping outcomes. This is a one-season slice, not a full-scope replacement. |
| [OpenFootball players](https://github.com/openfootball/players) | Repository declares CC0 1.0. Its published records give names, birth information, height and only broad G/D/M/F position groups. | A basic, reusable identity/bio seed where the player is present and the record can be matched confidently. | Complete Big Five season rosters, player-season stats, the project's 14 specific position labels, or evidence of positions actually played. |
| [Reep football identity register](https://www.reep.football/data/) | Its 2026-10-25 downloadable release says the register is CC0 and redistributable. It provides entity IDs, aliases, provider-ID bridges, match entities and relationship edges, not performance statistics. The publisher also cautions that CC0 only waives rights Reep holds and does not grant rights in third-party source material. | Potential identity crosswalk and search/index support after we verify the release manifest, relevant provider bridges, and source provenance. | Player performance, appearances/minutes, or proof of historical role. Do not treat an ID bridge as a license for the underlying provider's records. |
| [Wikidata structured data](https://www.wikidata.org/wiki/Wikidata:Licensing) | Structured data are released under CC0. Wikidata's own policy warns that this does not settle rights in third-party datasets that users may have integrated. | Optional discovery/corroboration of biographical facts and aliases with source links. | A complete audited season panel or specific played-position evidence. Each fact still needs quality and provenance checks. |
| [Wikimedia Commons media](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia) | Many files have free licenses or public-domain status, but each file has its own source, license and attribution requirements; Commons tells reusers to verify each item. | A curated subset of individual player photos or simple marks only after per-file license, attribution and relevant non-copyright restrictions are recorded. | Guaranteed coverage for all players, historical-season photographs, or a blanket license for all logos. The safe default is a project-made initials avatar and text/monogram team badge. |

The CC BY 4.0 Wyscout collection's stated coverage is also corroborated by the [data descriptor](https://www.nature.com/articles/s41597-019-0247-7) and its [Figshare collection page](https://figshare.com/collections/Soccer_match_event_dataset/4415000). The prior local source audit checked the relevant Figshare file metadata rather than inferring a license from the collection title.

## Screened but rejected as full-scope public substitutes

- **Global Football Data Lake (`v-eatpizzanot/soccer-dataset`):** the maintainer labels the compiled output CC BY 4.0 and says it is sourced from API-Football and Football-Data.co.uk. API-Football's current [terms](https://www.api-football.com/terms) state that it does not provide a license for users to publish its data and that publication authorization must be obtained from competent rights holders. The derived dataset therefore does not meet the project's no-permission upstream standard. It is also primarily match/team data; league history is uneven.
- **Cornerflick match JSON/CSV:** its [data page](https://cornerflick.com/data) says its compilation is CC BY 4.0, but also says underlying match facts come from providers with their own terms and asks users redistributing at scale to check with the providers and Cornerflick. That is not a verified no-permission source for republishing a full Big Five archive. Its historical eight-season coverage and player-minute/position semantics also remain unaudited.
- **Zenodo “Big 5 League stats” (2022–23):** the [record](https://zenodo.org/records/10120708) describes a scraped, trimmed one-season dataset. The record's displayed rights section does not identify a license, and its linked collection method does not provide clear upstream reuse rights. Not cleared.
- **Recent GitHub top-five player-season merges:** the inspected [2024–25/2025–26 repository](https://github.com/m-mahadi/top5-football-dataset) combines FBref, Understat, SofaScore and SoFIFA sources. It misses seven of FutWAR's eight seasons and does not establish that the upstream data may be republished as one dataset. Not a substitute.
- **Reddit/community dumps and Kaggle mirrors:** posts may describe useful coverage, but the reviewed leads provide no verified source-level grant for the upstream player data. “Free,” “public,” or an uploader's CC0/CC BY selection is not enough for the requested public mirror.
- **FBref, Understat, FotMob/SofaScore and EA FC/SoFIFA:** none in this audit provided a verified, complete Big Five 2017–18 to 2024–25 player-performance bundle with redistribution terms that meet the requested standard. A manual export or public webpage does not become an open dataset license.

## Practical replacement route

1. The owner has chosen to publish the existing explorer; preserve original files and provenance and keep local raw archives out of Git.
2. Keep public app text precise: describe this as an exploratory player library, not a complete or certified data release, and do not present the provisional contribution preview as finalized WAR.
3. Retain the narrower CC0/CC BY sources as documented alternatives for future corroboration, while preserving their exact source scope and attribution.
4. Continue auditing upstream provenance, position semantics, missingness and correction evidence as research-quality work; publication does not make the data complete or settle the WAR methodology.

## Next audit gate

Any newly found source must pass, before download or merge: (a) license applies to the data, not only code/website compilation; (b) upstream collection rights and redistribution are not conditioned on contacting a provider; (c) actual league × season × field coverage; (d) data definitions and missingness; (e) player/team identity quality; (f) position semantics; and (g) a reproducible source/version/hash manifest. No WAR formula, coefficient, position policy, or project season scope is changed by this audit.
