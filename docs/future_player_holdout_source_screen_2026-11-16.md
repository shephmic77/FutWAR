# Future player-level holdout source screen — 2026-11-16

## Decision

No newly reviewed source clears both requirements for FutWAR's final player-value test: Big Five player-level coverage with useful outcomes and documented rights/provenance suitable for a public project. Do not add these data to the public site or use their derived outputs as validation evidence until the source conditions are resolved.

## Candidates reviewed

| Candidate | Potential use | Current limitation | Disposition |
|---|---|---|---|
| [FPL Core Insights](https://github.com/olbauday/FPL-Core-Insights) | Current-season Premier League player-match stats, lineups, and FPL IDs; a possible partial future-season transfer check | The project README says it combines official FPL API data with “Opta-like” manually curated match stats and invites reuse, but the reviewed material does not identify the upstream match-stat source or provide a data-specific license/provenance statement. It is one league and the active season is incomplete. | Do not import into the public panel or use as final validation yet. A season-end sample could be screened if source lineage and reuse scope are clarified. |
| [Top-five football dataset](https://github.com/m-mahadi/top5-football-dataset) | Recent 2024–25 and 2025–26 Big Five player metrics from several providers | Its author explicitly says the data are not theirs to license and each upstream source retains its rights. It is not a clean untouched future-season test for the current prototype. | Do not redistribute or treat its merged rows as a rights-cleared independent gold standard. |
| [Pannadata](https://github.com/peteowen1/pannadata) | Big Five Opta-derived player-match and event data, with lineups, reported from 2013 onward | The repository describes cached Opta records but no data-specific reuse license was found in the reviewed repository page. | Useful as a research lead only; not approved for public ingestion. |
| [Club Football Match Data](https://github.com/xgabora/Club-Football-Match-Data) | Current results and team-match statistics | It contains no player-level features or lineups; its README says the match data come from Football-Data.co.uk and the Elo records from ClubElo. The repository MIT badge applies to the repo/code, not automatically to upstream data. | Could support a separate team-context benchmark, but cannot validate player action value or WAR. |

## Why the available lead does not close the validation gate

FPL Core Insights documents detailed 2026–27 player-match fields, including minutes, xG, assists, passing, defensive actions, and goalkeeper measures, and says the current season is stored separately. That makes it a plausible Premier League-only evaluation candidate. However, its public description is not enough to establish that the underlying match statistics can be republished in FutWAR or that their definitions are independent and consistent with the existing candidate. A download link is evidence of availability, not evidence of public redistribution rights or measurement validity.

The project's own 2025–26 player-form transfer was already inspected during development and performed worse than context on the tested team-outcome forecast. It cannot serve as the final untouched test. Any future player-level holdout needs to be frozen before model decisions, to use its own identity and event/box-score audit, and to be reported separately by league. A Premier League-only test would be evidence for that league only, not validation across all five leagues.

## Reproduction / follow-up

No files were downloaded or joined for this screen. Recheck candidate terms and the current-season coverage at the source before any future use; do not contact a provider or publish derived rows without the project owner explicitly authorizing that step.
