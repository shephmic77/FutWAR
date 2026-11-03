# FIFA / EA Sports FC roster-position panel

**Status:** two source archives acquired; edition/position audit and conservative player-season links generated on 2026-11-02. The panel remains separate from match-based position evidence. It is visible in the explorer when a candidate link meets the stated identity policy.

## Purpose and interpretation

Build a separate edition-by-edition position panel from FIFA / EA Sports FC squad databases. The owner confirmed that these databases include secondary positions and asked to use the roster associated with the start of each season. Keep the original game position string, primary position, and each listed secondary position as distinct fields. Compare this roster view with match-lineup labels and any future verified played-position evidence; do not treat the game label as proof of minutes played in that role.

The roster panel is season-start context. It does not replace the approved match-based secondary-position rule (at least five appearances and at least 10% of appearances in a position), and it cannot be used to count real match appearances or positional minutes.

## Edition-to-season mapping

| Game edition | Target season |
|---|---|
| FIFA 18 | 2017–18 |
| FIFA 19 | 2018–19 |
| FIFA 20 | 2019–20 |
| FIFA 21 | 2020–21 |
| FIFA 22 | 2021–22 |
| FIFA 23 | 2022–23 |
| EA Sports FC 24 | 2023–24 |
| EA Sports FC 25 | 2024–25 |
| EA Sports FC 26 | 2025–26, outside the current FutWAR scope |

The selected roster snapshot is the available edition snapshot with its actual source date retained. Game editions are released after some leagues have started; therefore this is a documented edition-based season proxy, not a claim that the roster was captured on each league's opening day. Never substitute a later winter/spring update without retaining its version and date as a separate observation. The FC25 file does not include a snapshot date; its Kaggle card's last-updated date (2024-09-26) is recorded only as a proxy and flagged unverified.

## Position handling

FutWAR's allowed canonical labels remain `GK`, `RWB`, `RB`, `CB`, `LWB`, `LB`, `CDM`, `CM`, `CAM`, `LM`, `RM`, `RW`, `LW`, and `ST`.

1. Preserve the dataset's raw position field and raw player identifier.
2. Split multi-position values only according to the audited source delimiter; do not discard the source order.
3. Retain a primary/secondary distinction only if the source schema explicitly provides one. If the source lists an unordered set, call it `listed_positions`, not primary and secondary.
4. Map a source code only when its meaning is a direct equivalent of an allowed FutWAR label. Keep unmatched codes (for example CF or side-specific CB variants) in the raw field and mark the canonical mapping unresolved until reviewed.
5. Do not infer a player's actual match role, main position by minutes, or secondary-position appearance threshold from this roster panel.

## Identity, coverage and quality checks

Audit each edition before joining: source file/version/hash and stated license; snapshot date; unique player IDs; repeated IDs; number of positions per player; allowed and unmapped codes; Big Five club/league coverage; free-agent and retired players; duplicate edition snapshots; missing names, dates of birth and club IDs; and join rates to the 22,417-row corrected analytical player-season panel. Candidate joins require a stable source ID or corroborating name, birth date and club/season evidence. Name-only fuzzy matches remain review candidates.

Store this panel separately from the canonical player-season and match-position tables. A comparison output can show agreement, disagreement, and missingness by game edition, league, season, team and player. It must display the source and snapshot date and must not silently replace a match-based position.

## Acquired files and first-pass audit

The raw ZIP files are stored locally and are excluded from Git by the existing `data/raw/*` ignore rule. They are not modified. The extraction script writes the season-specific CSVs and a JSON audit under ignored `data/processed/ea_fc_position_rosters/`.

| Kaggle dataset | Editions used | Kaggle-card license | Downloaded archive SHA-256 |
|---|---|---|---|
| [EA Sports FC 24 complete player dataset](https://www.kaggle.com/datasets/stefanoleone992/ea-sports-fc-24-complete-player-dataset) | FIFA 18 through FIFA 23 and EA Sports FC 24 | CC0: Public Domain | `b7a0438fb2c5bda6c9107637b4c57f840e38b25246d3785080054dac5b441c9a` |
| [EA SPORTS FC 25 Database, Ratings and Stats](https://www.kaggle.com/datasets/nyagami/ea-sports-fc-25-database-ratings-and-stats) | EA Sports FC 25 | Apache 2.0 | `f159e2f85062aa4d408893e823bfacd2eb7c331260832677df482c03d868d0e4` |

The FC24 source card describes the archive as FIFA 15–FC24 and says its data were scraped from SoFIFA; the FC25 card says it was scraped from EA's FC25 ratings site. The listed Kaggle licenses are recorded as source metadata, not independent certification of upstream rights. Source page, retrieval timestamp, byte counts and hashes are in `data/raw/ea_fc_positions/download_manifest.json`.

The extraction produced 16 files (male and female source tables kept separate), 151,716 player-edition rows across the eight target seasons. The FC24 archive contains one `fifa_update=2.0` snapshot per edition, with `update_as_of` dates from 2017-09-18 through 2023-09-22. The FC25 archive supplies 16,161 male rows and 1,576 female rows; the file has no explicit roster date, so 2024-09-26 is only the Kaggle card's last-updated date. The first audit found no blank source-position fields or repeated source IDs in the extracted snapshots. FC25 explicitly separates `Position` and `Alternative positions`; the earlier editions use `player_positions`, whose original ordered string is preserved without upgrading it to a primary/secondary claim.

The requested canonical position list is applied as a coverage check and UI display filter. FIFA/FC rows also contain `CF`, which is outside the list and is retained in the raw field and flagged; this pipeline does not guess a conversion to `ST` or `CAM`. The source rosters cover the game's broader player universe, not only Big Five league players.

Rebuild the local derivatives from PowerShell at the project root:

```powershell
py scripts\extract_ea_fc_position_rosters.py
```

The generated audit is `data/processed/ea_fc_position_rosters/roster_position_audit.json`. The source-position CSVs remain local ignored derivatives. Only the approved displayed position context and source attribution are packaged into the explorer bundle.

## Player-season link and explorer display (2026-11-02)

`scripts/build_ea_fc_roster_enrichment.py` links source rows to explorer player-season records conservatively. FIFA18–FC24 require an exact normalized player name (or the first two tokens of a longer source name), matching birth year, and a unique source roster identity within that edition. Initial-plus-surname aliases additionally require a same-club season record. Club disagreement is retained as context because the game roster snapshot and full-season statistics can fall on opposite sides of a transfer. FC25 has no birth date, so it requires an exact unique name and matching nationality; its club agreement is recorded where available. No fuzzy name join is used. The latest run linked 18,807 of 22,418 explorer records (83.892%); season-level counts are in `reports/explorer/ea_fc_roster_enrichment.json` (local generated report). Unmatched records remain explicitly unavailable.

The player header shows the explicit EA Sports FC 25 primary position when one is available; earlier editions keep the existing profile role as the main label because their ordered lists do not establish primary/secondary semantics. An adjacent badge shows distinct additional game-listed positions. The edition name and roster snapshot date are not repeated in the header; the Context tab retains season-by-season edition, source roles and dates. Only the user's approved codes are rendered: `GK`, `RWB`, `RB`, `CB`, `LWB`, `LB`, `CDM`, `CM`, `CAM`, `LM`, `RM`, `RW`, `LW`, `ST`. Unsupported source labels remain in the evidence JSON and are not remapped or shown as approved codes. Tooltips retain the distinction between source-listed roles and match-played positions.

### Main/additional display duplicate audit — 2026-11-02

The explorer now uses the explicit EA Sports FC 25 primary position for the selected player-season header. Its adjacent additional-position badge filters that primary and the displayed main position from a de-duplicated set of approved alternatives. For FIFA 18–EA Sports FC 24, the game source does not identify primary versus alternative roles; the existing profile role remains the header main role, and repeated codes are removed from the adjacent listed-role badge. This is a display rule only and does not alter raw source strings or the game-roster enrichment.

Before the display change, a full join of the 22,418 explorer records to the position enrichment found 298 records where the profile-derived header role repeated among FC 25 alternatives. The source's explicit primary itself did not repeat in the parsed alternative field, and no duplicate canonical position codes were found within the linked allowed-position lists. The 298 apparent repeats were role disagreements: 973 linked FC 25 records had a game primary different from the older profile role. For example, Dybala's FC 25 roster lists CAM as primary and ST as alternative, while the separate profile role maps SS to ST. The hero now presents CAM / ST for that FC 25 season rather than repeating ST.

The expanded repeat audit on 2026-11-02 checked every explorer player-season page record and all 145,698 acquired men's roster rows across the eight FIFA/EA FC editions. Results: 22,418 page records checked; 18,807 linked to a game roster and 3,611 left unlinked; zero source primary codes repeated in source alternatives; zero displayed main positions repeated in the adjacent additional-position badge; zero duplicate additional codes; and zero repeats in the season-by-season Context position list. Search-result, season-summary, and team-roster position labels use the same selected-season primary-position rule as the player header. The underlying male roster scan found no duplicate position codes in the older ordered lists or within FC 25 alternative lists. Unlinked records remain unlinked and show no game-roster alternatives; their profile position is not independently validated by this audit. `scripts/audit_position_display.py` reproduces the linked-display and full-roster checks and writes a local report; source position strings remain preserved.

Player-facing nationality abbreviations are replaced by FlagCDN flag images with accessible country names in the label/tooltip; if an image request fails, an emoji flag is shown as a fallback. Source nationality codes remain available in the underlying records and CSV exports. Flag images are linked from [FlagCDN](https://flagcdn.com/), whose provider describes the service as free and based on Wikimedia Commons vector artwork.

`data/explorer_nationality_corrections.json` is a separate, reviewed nine-record layer for originally blank nationality values. The original source fields are preserved. The layer cites Premier League, Leicester City FC, L'Équipe, Le Puy Foot, DFB and UEFA pages; Plamedi Nsingi is explicitly provisional because one provider lists France while the interview and another profile support DR Congo. Generic game-source `Congo` labels are deliberately not mapped automatically because the label does not distinguish the two countries. Unambiguous source spelling variants (for example `Congo DR`, `Korea DPR`, and `Cape Verde Islands`) are mapped to their flag codes in the interface.

Rebuild from PowerShell at the project root:

```powershell
py scripts\build_ea_fc_roster_enrichment.py
py scripts\package_explorer.py
```

This enrichment affects generated explorer data only. It does not write to raw Kaggle archives, canonical analytical source rows, SQL tables, or match-played-position fields.

## Additional candidates (not acquired)

Other potentially overlapping FIFA/SoFIFA datasets were not downloaded because the acquired FC24 archive already supplies the needed FIFA18–FC24 editions. Do not assume one dataset's license applies to another edition or upstream source, and do not scrape SoFIFA directly as a substitute for an audited downloadable file.

Candidate references not used here: [FIFA 18 Complete Player Dataset](https://www.kaggle.com/datasets/thec03u5/fifa-18-demo-player-dataset), [FIFA 22 Complete Player Dataset](https://www.kaggle.com/datasets/cashncarry/fifa-22-complete-player-dataset), [FIFA 23 Complete Player Dataset](https://www.kaggle.com/datasets/stefanoleone992/fifa-23-complete-player-dataset), [FC 25 SoFIFA snapshot from June 2025](https://www.kaggle.com/datasets/aniss7/fifa-player-data-from-sofifa-2025-06-03), and [EAFC26 Player Database](https://www.kaggle.com/datasets/flynn28/eafc26-player-database). EAFC26 is outside the current eight-season scope.

## Remaining validation before use

1. Review coverage gaps and season-end club differences before using game roles as explanatory context.
2. Compare game-listed roles against match-based labels only as context. Do not use game positions as played positions, positional minutes or proof of the five-appearance/10% secondary-role rule.
3. Review any proposed identity-link expansion before applying it; do not loosen linkage silently.
