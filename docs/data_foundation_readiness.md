# FutWAR data foundation readiness

**Updated:** 2026-10-16
**Status:** Not ready to call complete; WAR formula experiments remain paused by the owner's request until the foundation passes review.

**Public-site status:** The deployed site at [futwar.vercel.app](https://futwar.vercel.app/) currently serves a data-free holding page. Player data bundles and source-linked assets were removed from the public site tree and rewritten out of reachable Git history on 2026-10-16. The full explorer and underlying local data remain in the owner's local workspace. The owner previously reported that personal/student use and public inclusion were acceptable; that report is retained as the owner's terms review, not independent verification of upstream rights. Public redistribution is paused while source provenance and reuse are reviewed. No commercial-use permission is claimed.

This note separates data that is present from data that is complete, comparable, and usable. “No errors” means the documented validation checks pass for a defined source and purpose; it cannot mean that every real-world record is guaranteed error-free.

## Current audit results

- The processed player-season CSV contains 22,418 player-team-season rows across all 40 Big Five league-season cells from 2017–18 through 2024–25. The latest core CSV audit found zero malformed rows, zero duplicate rows, and zero duplicate configured keys. It found three blank age/birth-year values and ten blank nationality values. Cell presence and row counts do not certify that every eligible player or metric is present.
- The Kaggle page is recorded as the source of the supplied CSV. Its provider, full definitions, acquisition date, and reuse terms have not been independently verified. The local source manifest records the publisher's CC0 declaration as supplied by the user, not as verified upstream rights. Do not redistribute the source file or represent those rights as confirmed.
- Wyscout's research release supplies a separately audited five-league 2017–18 event sample: 1,826 scheduled matches and 3,071,395 events. It is absent from the other 35 league-season cells. Its event IDs have not been reconciled to the player-season database, and event-derived player credit is not validated.
- Match-results sources are staged for all 40 cells. The refreshed OpenFootball audit found 14,460 scheduled fixture rows, of which 14,339 have base-source full-time scores. A separate exact-fixture supplement verifies 20 missing 2024–25 La Liga and Serie A scores, giving 14,359 scored matches. Ligue 1 2019–20 has 101 unplayed fixtures without scores after the season ended early; these are not missing played results. A separate Football-Data archive has broad scope but one Bundesliga 2024–25 match lacks twelve non-score fields. Club aliases, metric definitions, and 72 date disagreements against the player-appearance source still need review.
- Historical played-position evidence is not complete for every player appearance. The main-position-by-minutes rule must withhold a label when the evidence is incomplete; broad source labels (GK/DF/MF/FW) do not satisfy the owner's specific-position list. The 5-appearance/10% secondary-position threshold cannot be applied exhaustively without match-level role evidence.
- Goalkeeper measures and exposure are assembled from separate archives and corrections, but provider versions, cross-season coverage, identity links, and reuse conditions remain unresolved. They are not yet a complete comparable keeper panel.
- Team budgets, wages, season-start availability, and affordable replacement candidates are not available as a consistent open panel across the 40 cells. Transfer values do not establish club budget or player affordability.

The refreshed `scripts/audit_data.py` inventory pass read 49 local CSVs without read errors. Its broad inventory reported 337 missing-provenance fields and 48 missing coverage mappings across mixed raw sources and presentation assets. These counts are not 337 statistical data errors; they indicate the broad inventory needs source-specific manifests and should not be used as the project readiness score. The isolated core player-season audit reported only its one unresolved provenance item: retrieval date. A rerun of the player-season profile audit again found no numeric parse failures or configured exposure violations, all 40 target cells, and the single approved 512-record Torrasi conflict group; the approved transform produced 22,418 unique configured keys and verified that the raw source bytes were unchanged.

The complete validation suite now passes: 102 tests ran successfully under Python 3.13.1. The first attempt hit Windows sandbox permissions when tests created temporary folders under the default system temp path; setting `TEMP` and `TMP` to an ignored workspace-local folder resolved this environment issue. The `py` launcher was unavailable for this run, so the installed Python executable was invoked directly.

## Free event-source candidates after StatsBomb was dropped

The project already has Wyscout for the 2017–18 five-league pilot. A newly identified candidate is [Impect Open Data](https://github.com/ImpectAPI/open-data): the publisher describes Bundesliga 2023–24 event data, event/player KPIs, lineups, substitutions, player and match metadata. This could provide a later-season, same-league comparison and test player/event identity handling. It cannot fill the other 39 league-season event cells or provide a Big Five panel. Impect directs users to a separate terms PDF and requests attribution and use of its logo; review that agreement and audit the actual files before acquisition or integration.

[Metrica sample data](https://github.com/metrica-sports/sample-data) and [SkillCorner Open Data](https://github.com/SkillCorner/opendata) offer small tracking/event examples, not a historical Big Five player panel. [OpenFootball](https://github.com/openfootball/football.json) provides free CC0 match schedules/results and is already used for match context; it does not add player events. [Football-Data.co.uk's own guidance](https://football-data.co.uk/contact.php) describes intended use as private individuals and rejects commercial or data-training products using automated bots/scrapers/AI, so do not treat it as a general public redistribution source.

No free public source found in this screening supplies comparable event-level player data for all five leagues across all eight seasons. More datasets may improve the foundation, but a patchwork of inconsistent providers cannot be declared complete just because every season cell contains some rows.

## Gate before WAR formula experiments

1. Reconcile the full player-season source row by row against its claimed upstream provider and definitions; retain raw files unchanged and publish a source-specific issue log locally.
2. Complete provider/rights review for each source according to its actual intended use (private research, public analysis, or raw redistribution); record which derived outputs can be shared.
3. Build a source-coverage matrix by league, season, metric, role, and granularity. Keep unknown cells unknown; quantify missingness and disagreements.
4. Validate player/team identities, player-season keys, transfers, playing-time totals, match-result joins, and the correction layer against independent evidence. Preserve unresolved matches for review.
5. Decide whether available position evidence supports position-locked and any-evidenced-position comparison pools. Do not infer specific roles from broad labels or a single nominal formation.
6. Define a minimum viable foundation for each of the six comparison views. The team-accessible view additionally needs a defensible historical affordability/resource proxy; if that evidence remains unavailable, keep that view marked as a scenario design rather than a calculated score.
7. Keep the passing test suite green and repeat source audits and hash checks from a clean working state after any data changes.

Only after these gates are reviewed should the project begin formula experiments. This does not finalize weights, replacement selection, cross-position conversion, or any of the six scores.
