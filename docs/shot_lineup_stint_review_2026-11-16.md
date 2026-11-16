# Shot actor versus lineup-stint follow-up — 2026-11-16

**Purpose:** interpret the five events flagged by the cross-provider shot/lineup presence audit. This is a targeted case review, not a representative sample, identity-precision estimate, or validation of player-value attribution.

## Finding

All five flagged player names have an exact-name match in the OpenPlay lineup, but the recorded OpenPlay entry minute is later than an independent match timeline's substitution time. In each case, the Wyscout shot time falls after the independently reported substitution and before the later OpenPlay lineup-on time. The cases therefore demonstrate that lineup stint timing can create false appearance-conflict flags. They do **not** establish that the shot actor assignment is correct; they also do not support labeling these five as actor misattributions.

| League / match | Player | Wyscout shot time (approx.) | OpenPlay listed on | Independently reported on | Gap between reported and OpenPlay entry | Source |
|---|---|---:|---:|---:|---:|---|
| Premier League, Crystal Palace–Man City, 2017-12-31 | Jason Puncheon | 76.9 | 82 | 75 | 7 min | [11v11 match record](https://www.11v11.com/matches/crystal-palace-v-manchester-city-31-december-2017-356095/); [RSSSF match details](https://www.rsssf.org/tablese/eng2018det.html) |
| Premier League, Southampton–Stoke, 2018-03-03 | Sofiane Boufal | 76.1 | 81 | by 75 | at least 6 min | [Statto/Statbunker live commentary](https://statbunker.com/competitions/LiveFootballCommentary?comp_id=586&date=03-Mar-2018&match_id=94454); [Sky Sports report](https://www.skysports.com/football/news/11274633/southampton-0-0-stoke-stalemate-keeps-pressure-on-relegation-rivals) |
| Serie A, Lazio–Torino, 2017-12-11 | Afriyie Acquah | 85.5 | 90 | 85 | 5 min | [Corriere dello Sport match sheet](https://www.corrieredellosport.it/news/calcio/serie-a/2017/12/11-35420398/serie_a_torino-lazio_1-3_il_tabellino) |
| Bundesliga, Mönchengladbach–Bayern, 2017-11-25 | Josip Drmić | 91.4 | 96 | 87 | 9 min | [FC Bayern official live ticker](https://fcbayern.com/en/matches/profis/bundesliga/2017-2018/borussia-moenchengladbach-fc-bayern-muenchen-24-11-2017/liveticker); [DFB match record](https://datencenter.dfb.de/datencenter/bundesliga/2017-2018/13-spieltag/borussia-moenchengladbach-bayern-muenchen-2247798) |
| Ligue 1, Troyes–Amiens, 2017-12-16 | Benjamin Nivet | 68.6 | 77 | 67 | 10 min | [Gazette Sports match report](https://gazettesports.fr/2017/12/16/football-lamiens-sc-etait-coup/); [iSport live match record](https://isport.blesk.cz/fotbal/ligue-1-2017-2018/troyes-amiens/online-prenos?match=263558) |

## Scope and data handling

- The five cases were selected because the audit flagged them; the observed 5/5 rate must not be generalized to the full archive.
- Match-report substitution times are rounded to match minutes and may differ by a minute across providers. The Wyscout event clock is also approximate. These are sufficient to show a timing conflict, not to build exact corrected stint intervals.
- The report does not establish why OpenPlay's intervals differ, nor whether every shot row has the correct actor. Actor identity requires its own independent evidence.
- No raw event, lineup, identity, or exposure data were changed. No correction was applied. Keep all five as timing-review cases; do not count them as confirmed actor errors.
- The audit's broader rate remains a **lineup-presence plausibility screen**, not an actor-identity precision score. Use conservative language in any public summary.

## Reproduction and next use

The aggregate screen and its local row-level review candidates are produced by `scripts/audit_cross_provider_shot_lineup_presence.py`; the row-level CSV is ignored by Git. Re-run the script before reusing its aggregate counts. Future manual reviews should be sampled from both flagged and unflagged shots, with match reports and source actor evidence recorded separately, before estimating any actor-link precision or recall.
