# FutWAR data foundation gate review

**Reviewed:** 2026-10-16

**Status:** Not yet ready for player-value experiments. This review records reproducible checks and separates structural quality from completeness and comparability. On 2026-10-16, the public player bundles were removed from the deployment tree and rewritten out of reachable Git history; the public site now serves a data-free holding page. Local data and the explorer remain available for research. No source data or WAR decisions were changed by that publication cleanup.

## Summary

The season-level player panel is structurally usable as a descriptive starting point: it covers 40 of 40 Big Five league-season cells, has 22,418 unique player-team-season keys after the documented source-specific collapse, and has no numeric parsing or configured exposure-constraint failures. That does not establish that it contains every eligible player or that provider definitions are comparable.

The blockers for a defensible six-view comparison are historical specific-position evidence, unresolved player identity links, incomplete goalkeeper comparability, and an absent historical budget/availability panel for team-accessible replacements. Detailed event data currently cover only 2017-18. The all-season event/action model therefore cannot be treated as a complete player contribution measure.

## Reproduced checks

| Area | Finding | Gate status |
| --- | --- | --- |
| Player-season source | 22,929 raw rows; source fingerprint matches the configured SHA-256. | Reproducible input; upstream provider/version, acquisition date and complete definitions still need confirmation. |
| Approved source correction | Emanuele Torrasi/Milan/2017-18 has 512 export rows. The approved transform collapses them to one record, retaining a unique nonblank value per field and leaving the `Subs_unSub` 0/1 conflict missing. Raw bytes are unchanged. | Documented, source-specific handling; do not generalize this merge rule to other players. |
| Processed player-season panel | 22,418 rows, 22,418 unique configured keys, 40/40 cells and 18–20 clubs per league-season. Processed SHA-256 matches `data/processed/lineage.json`. | Structurally passes; not an inclusion/completeness certificate. |
| Numeric and exposure checks | Zero numeric parse failures and zero negative-minute, starts-over-appearances or minutes-versus-90s constraint violations. | Passes the defined checks only. |
| Repeated player-stat fields | Eight overlapping column-pair checks have zero unequal values among comparable rows. | Helpful internal consistency check; not independent source validation. |
| Selected advanced metrics | Thirteen of the audited advanced fields are missing for two one-minute records only: Aiden O'Neill and Christian Rutjens in 2017-18. All 13 are blank for each; no zero imputation is appropriate. | Very low missingness in this file, but the two records remain unresolved/low-exposure and should be flagged or excluded from any affected calculation. |
| Biography fields | Three missing birth years/ages and ten missing nationalities. | Non-blocking for rate models if kept unknown; relevant to identity resolution and display. |
| Team/season match results | Refreshed OpenFootball audit: 14,460 scheduled fixture rows, 14,339 with base-source full-time scores; a source-verified supplement covers exactly 20 unscored 2024–25 La Liga and Serie A fixtures, giving 14,359 scored matches. Ligue 1 2019–20's 101 no-score fixtures are unplayed after early season termination. | Broad result coverage; the 72 match-date differences against the appearance provider and detailed source joins still need reconciliation before attaching player events/appearances. |
| Player identity | The archived identity-source audit has 20,521 exact-name/birth-year/historical-appearance candidates, 1,894 without a supported exact-name candidate and 3 without birth year. Candidates are not verified links; the matching method's false-link rate is not measured. | Blocks reliable career aggregation and some replacement-pool deduplication until reviewed or explicitly bounded. |
| Specific played positions | The available player-season positions are broad provider labels; exhaustive historical match-position minutes are not available for all eight seasons. | Blocks the approved specific-position locking and meaningful-secondary-position rule across the full scope. Keep position `unknown` where unsupported. |
| Event/action data | The Wyscout research archive covers 1,826 matches and 3,071,395 events in 2017-18 only. Conservative identity candidates cover 87.50% of actor-event rows, but these links are not independently verified. The other 35 league-season cells have no equivalent event panel. | Suitable only for bounded pilot work after identity/horizon validation; not a complete eight-season contribution input. |
| Goalkeepers | Keeper archives and corrections exist, but source versions, cross-season definitions/coverage, identities and reuse evidence have not been reconciled into a comparable keeper panel. | Blocks an all-position WAR view; retain a separate keeper path until calibrated to the shared outcome scale. |
| Team-accessible replacement | There is no consistent free historical panel of club budgets/wages, season-start availability and feasible candidate options across the 40 cells. Transfer values are not budgets. | This comparison must remain a design/scenario view until direct historical access and cost evidence supports it. |
| Full test suite | 102 tests ran successfully under Python 3.13.1. The first attempt failed only because Windows sandbox permissions denied test-created folders under the default system temp directory; rerunning with workspace-local `TEMP` and `TMP` passed. | Test gate passes in this environment. The Windows `py` launcher was unavailable, so the installed Python executable was called directly. |

## Publisher provenance and reuse review

The current source manifest attributes the player-season CSV to FBref through a Kaggle publisher description; it records CC0 as a Kaggle-listing declaration supplied by the owner, not as an independently verified license from the upstream data owner. The Kaggle page could not be read in full during this review, so its current data-card license and source explanation remain unverified.

This creates a material question for public hosting. Sports Reference's [Data Use guidance](https://www.sports-reference.com/data_use.html) says users should not create websites or tools based on data scraped from its sites without permission. Its [January 2026 FBref update](https://www.sports-reference.com/blog/2026/01/fbref-stathead-data-update/) says a data provider asserted that Sports Reference's use of its data violated their agreement, after which advanced soccer data were removed. A CC0 label assigned by a Kaggle uploader cannot by itself establish rights to relicense upstream content. The owner previously reported reviewing and approving personal/student use and public inclusion; that report is preserved, but it is not independent verification of upstream rights. Following the owner's later instruction, player bundles were removed from the public deployment and rewritten out of reachable Git history on 2026-10-16. The deployed site is now a data-free holding page; local research data and explorer files were preserved. Public redistribution remains paused pending source-specific provenance and reuse review or replacement by data with clear redistribution terms.

FBref also states in its [position documentation](https://fbref.com/en/about/errata) that position data are constructed from season-level data and may include players who did not regularly play the listed position. Its displayed broad primary groups (GK/DF/MF/FW) and secondary groups do not supply the requested complete match-level minutes needed for the owner's exact position and secondary-position rule. This independently confirms that the current FBref-derived `pos_` field cannot satisfy the FutWAR position gate.

## Reproduction performed

Raw source bytes remained unchanged. The core player-profile and broad-inventory audit outputs were written under ignored `reports/test_tmp/foundation_refresh_20261016/`. The match audit regenerated local derived reports under `reports/match_audit/` and `data/processed/match_results/`; the exact-fixture supplement check regenerated its local manifest and processed supplement. These are the reproduction commands for a Windows Python environment with the project dependencies installed:

```powershell
py scripts/profile_player_seasons.py --output reports/test_tmp/foundation_refresh_20261016/player_season
py scripts/audit_data.py --output reports/test_tmp/foundation_refresh_20261016/inventory
py scripts/prepare_player_seasons.py
py scripts/audit_match_results.py
py scripts/prepare_match_supplement.py
$env:TEMP = Join-Path (Get-Location) 'reports/test_tmp/foundation_refresh_20261016/temp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
py -m unittest discover -s tests -v
```

In this check, the Windows `py` launcher was unavailable, so I used the installed Python 3.13.1 executable directly. The player-season transform verified the source hash, applied only the approved Torrasi collapse, produced 22,418 rows with no duplicate configured keys, and reported `raw_unchanged: true`. The source-specific match audit found 14,339 base scored matches plus the exact-set-verified 20-row supplement; the supplement remains separated from base-source results. The broad inventory read 49 local CSVs without read errors; it is not a data-readiness score because mixed nested sources lack semantic mappings and archives need their own audits. The complete test suite passed all 102 tests when its temporary files were directed to workspace-local temp storage. No files under `data/raw/` were changed.

## What “solid” can mean for this project

No available source found so far supplies comparable events, verified specific played positions, and complete goalkeeper data for every league and season in the full 2017-18 through 2024-25 scope. Therefore the project cannot honestly promise zero real-world errors or a uniformly complete event-level panel. A reviewable foundation can instead be frozen by purpose: (1) the season-level panel and its unresolved rows are versioned and audited; (2) each comparison states exactly which positions, metrics, leagues and seasons it supports; (3) identity and position uncertainty are excluded or shown, never guessed; and (4) unsupported team-budget and goalkeeper comparisons are labeled unavailable rather than filled with proxies without approval.

This review does not declare that scoped foundation accepted. It identifies the remaining gates for owner review and further data work.

## Recommended order of work

1. Reconcile the two flagged one-minute records and document whether they stay visible only as low-exposure records; do not fill their advanced statistics with zero.
2. Improve player identity links using independent historical evidence, quantify precision on a reviewed sample, and keep unresolved names unmerged.
3. Search/audit permitted historical specific-position evidence. Do not claim the position-locked or any-evidenced-position comparison is complete until its league-season coverage is measured.
4. Build a separate goalkeeper data-quality matrix and establish which metric/source combinations can be compared across seasons.
5. Reconcile match/provider date and club mappings, then measure event-player identity and metric coverage for every source actually used.
6. Decide whether the team-accessible baseline remains a scenario-only prototype or whether an adequate historical cost/availability source is found.
7. Install the repository's declared development/reference-audit dependencies in the user's Windows Python environment and rerun the complete test suite. Only then review and close the data gate before new model experiments.

This report is an audit result, not a change to the owner's research goals, feature policy, player credit, replacement definition or WAR formula.
