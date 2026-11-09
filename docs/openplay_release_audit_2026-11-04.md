# OpenPlay release data audit — 2026-11-04

## Decision

OpenPlay `data-v0.1.0` supplies a substantial, reproducible event panel for all 40 target Big Five league-season cells. It materially improves the event-data foundation, but it does **not** clear the four requirements for a complete player WAR model. The local archive is pinned and hash-checked; source-to-source player links have a strong deterministic subset; exact played-position minutes and a validated goalkeeper common scale remain open. A team-state expected-points model now passes a first rolling-season check; event-action/player out-of-time validation and historical team feasibility/cost remain open.

The publisher declares the release CC BY 4.0. Its own license also describes the underlying event lineage as WhoScored pages displaying Opta/Stats Perform data. This audit does not independently establish the publisher's authority to sublicense every upstream record. Therefore the archive remains local and ignored by Git; do not upload raw files or show player-level derived scores on the public site based on this audit alone. Credit and limitations are recorded in the tracked source manifest.

## Acquisition and reproducibility

- Release: [OpenPlay `data-v0.1.0`](https://github.com/nlbair/openplay/releases/tag/data-v0.1.0), pinned release metadata retrieved 2026-11-04.
- 53 selected assets (40 event files and match, lineup, formation, player-match, shot, card, source-document, and integrity tables): 523,602,217 bytes.
- Every selected asset's byte count and SHA-256 matches the pinned GitHub release metadata/checksum manifest.
- Raw source lives under ignored `data/raw/openplay/data-v0.1.0/`; `data/openplay_source_manifest.json` tracks provenance and hashes without adding raw files to Git.
- Rebuild with `py scripts\acquire_openplay_release.py`; audit with `py scripts\audit_openplay_release.py` from PowerShell. In this environment, the explicit Python 3.13 executable was used because the `py` launcher did not work.
- Aggregate output is local/ignored under `reports/openplay_release_audit/`.

## Gate 1 — reusable event coverage

| Check | Result | Meaning |
|---|---:|---|
| Target cells with a pinned event file | 40 / 40 | All eight target seasons and five leagues have a file. |
| Listed fixtures / fixtures with events | 14,360 / 14,334 | 26 known fixture gaps; 99.82% of listed fixtures have an event file. |
| Event rows | 22,402,157 | Provider event records across the 40 cells. |
| Repeated composite event keys | 1,191 | Each is a distinct event record, not an exact duplicate; see the collision follow-up below. |
| Event records with a missing/zero actor ID | 222,724 (0.99%) | These remain in event-state reconstruction but cannot receive player credit. |
| Distinct event actor match/team/player keys absent from player-match stats | 253 | Quarantined; follow-up classification is documented below. |
| Published source issue records / distinct affected matches | 13 / 10 | Includes score conflicts, very short event files, and incomplete lineups. |
| Cells where source match count differs from the coverage table | 9 | Listed explicitly in the local 40-cell report; do not fill these by inference. |

The 26 gaps and 10 issue matches mean the event panel is not a complete match census. There are no repeated match IDs in the downloaded match table. The match table's event-count reconciliation found zero count-mismatch matches in the per-file audit, but source count deltas and known event-quality issues remain. Use event files with explicit fixture/quality flags; do not claim full-season completeness.

**Follow-up on the 26 listed matches without event files:** a cross-table check confirms that none has player-match statistics, lineup rows, or shots elsewhere in the same OpenPlay release (0/26 in each table). These are complete match-level holes across the release's player contribution inputs, not event-only omissions with auxiliary player records available. Their score/result metadata remain in the match/known-gap tables, but there is no source evidence here to recover player actions, exposure, or shot-stopping records. The per-cell breakdown is reproducibly written to the ignored `reports/openplay_release_audit/known_gap_auxiliary_coverage_by_cell.csv` by `py scripts\audit_openplay_release.py`.

**Follow-up classification of repeated event keys:** the expanded `scripts/audit_openplay_release.py` audit found 1,191 repeated `(match_id, event_id, event_id_sub)` groups across the target 40 cells. Every group contains two distinct full-row payloads; none are exact duplicate rows, every group differs in its period/minute/second/expanded-minute clock tuple, and no pair shares the `expanded_minute` + `second` sort clock used by the transition pipeline. 1,152 also differ in actor or team, and all 1,191 differ in event type or outcome. Thus the composite key is not unique and must not be used to drop records. The current time-first sort resolves the observed pair order; retain both source records and use the timestamp fields before IDs. The per-cell counts are reproducibly recorded in `reports/openplay_release_audit/event_file_quality.csv`.

## Gate 2 — player-season identity, position minutes, goalkeeper comparability

### Event/player-season linking

The audit joined the OpenPlay player-match panel to the corrected FutWAR player-season panel on normalized player name, canonicalized club name, league, and season. No fuzzy matching was used.

| Link check | Player-season rows |
|---|---:|
| Unique exact-key candidate with one OpenPlay player ID | 17,316 / 22,417 (77.2%) |
| Exact-key candidate with matching appearance total | 16,725 / 22,417 (74.6%) |
| Unique candidate with exactly matching appearance total | 16,725 |
| Unique candidate within one appearance | 17,255 |
| Unique candidate with appearance difference greater than one or missing | 61 |
| No exact-key candidate | 5,101 |
| Ambiguous exact keys | 0 |

The 16,725 rows are the strongest deterministic crosswalk subset: exact normalized name/team/league/season, exactly one OpenPlay player ID, and equal season appearance counts. This is strong cross-source join evidence, not an independent manual verification of every identity. The remaining 5,692 rows stay unlinked or flagged. OpenPlay's match minutes include stoppage time; the current player-season source uses standard reported minutes, so their minute totals are not compared as though they shared a definition. All 253 event-actor keys without a same-match player-stat key remain excluded from player action totals; their follow-up classification is below.

**Follow-up on the 61 material appearance conflicts:** all 61 unique exact-key candidates with an appearance difference greater than one are concentrated in six club-seasons, and each of those clubs has event-file gaps in the same season: Angers 2021–22 (9 rows; 2 affected fixtures), Atalanta 2021–22 (13; 3), Napoli 2021–22 (10; 2), Atalanta 2022–23 (16; 3), Cremonese 2022–23 (11; 2), and Spezia 2022–23 (2; 2). An independent season record for one player in each group supports the player-season source appearance count. This points to missing OpenPlay match exposure as the common explanation; it does not prove each of the 61 player links or establish which missing matches each player appeared in. No appearances or IDs were corrected. The 5,692 flagged rows split into 5,101 without an exact key and 591 exact-key candidates with unequal appearance counts (530 within one appearance, 61 over one). Reproduce the aggregate-only check with `py scripts\audit_openplay_identity_exposure_conflicts.py`; see the [follow-up review](openplay_identity_exposure_conflicts_2026-11-06.md). The remaining identity precision/recall gap is still unresolved.

**2026-11-06 club-alias update:** the original counts above are the 2026-11-04 audit snapshot. A follow-up reviewed repeated exact-name/league-season club-label pairs and added 33 aliases to `data/club_aliases.json`; one one-off Valladolid/Real Madrid collision was excluded. The full release audit was rerun with matching raw hashes. Current candidate counts are 20,889 unique exact-key rows, 20,227 with equal appearance totals, 20,828 within one appearance, 61 over one, 1,528 without an exact key, and zero ambiguous keys. This improves deterministic join coverage, but no player ID is approved by the alias file; independent validation, player-attribution checks, and the remaining data/model gates are still required. See [club-alias follow-up](openplay_team_alias_followup_2026-11-06.md).

**Follow-up classification of the 253 event-actor/stat exceptions:** `scripts/audit_openplay_actor_stat_exceptions.py` found that every key has a same-match lineup row marked `Sub`, `played=False`, and zero minutes. Of these, 248 keys have only card event rows (252 rows across 238 matches); five keys include six event rows, five of which are non-card actions (a pass, two fouls, a challenge and a tackle) despite the zero-minute bench status. This clarifies why the keys are absent from player-match stats, but does not prove event attribution. Keep all 253 keys outside player-season action totals; the five contradictory on-field action records remain flagged, and bench-card events may remain in match context without being credited as played contribution. Reproduce with `py scripts\audit_openplay_actor_stat_exceptions.py`; only grouped counts are written under ignored `reports/openplay_actor_stat_exceptions/`.

**Follow-up classification of the 98 lineup played/minute flags:** all 98 have a matching player-match stats row with zero minutes, and all have identical `minute_on` / `minute_off`. Twenty-three have a kickoff-position label and both times are 0; the other 75 are `Sub` rows with both times from minutes 91 through 103. None is a positive-minute appearance missing from player-match stats. Keep their exposure at zero and preserve the conflicting `played=True` source flag for provenance. The full-release audit now writes the grouped breakdown to `reports/openplay_release_audit/lineup_played_minute_mismatch_summary.csv`.

### Played position

- OpenPlay provides kickoff positions and actual appearance minutes, but substitutes are labeled `Sub`; the data dictionary says lineup positions repeat into player-match stats as position-at-kickoff.
- Its codes include `GK`, `DC`, `DL`, `DR`, `DMC`, `MC`, `AMC`, `ML`, `MR`, `AML`, `AMR`, `FW`, plus split-side variants. These can support a role-at-kickoff crosswalk after explicit review, not a complete time-in-role record.
- Formation spells cover 133,045 target spells with matching player/slot-array shapes. Another 2,553 have duplicate player IDs (2,546) or array-length mismatches (7). The published dictionary says the arrays are in slot order but does not provide a slot-to-role mapping for this release. A numeric slot cannot be silently translated into FutWAR's GK/RWB/RB/CB/LWB/LB/CDM/CM/CAM/LM/RM/RW/LW/ST taxonomy.
- There are 98 played-flag/minute inconsistencies in the lineup table. Player-match stats have 106 zero-or-negative minute rows. Starter counts and player-match keys otherwise need to retain the source issue flags.

**Result:** season participation and source kickoff role are available for a large share, but verified match-level minutes in actual specific positions are not complete. Do not present position-locked or flexible-role baselines as complete.

### Goalkeepers

- The target panel contains 28,668 kickoff-listed goalkeeper match rows (two per event-bearing fixture). Keeper action fields are populated in the source player-match table, but some goalkeeper action rows have `Sub` or non-GK kickoff labels; the lineup position alone will miss substituted keepers.
- The shot table has 360,976 target shots, xG on 359,181 (99.50%), and both goal-mouth coordinates on 328,750 (91.07%). Coverage varies by league-season; the per-cell table is in the local audit output.
- The source supplies saves, claims, punches, sweeper actions and other counts, but no validated post-shot xG (PSxG) or complete shot-to-defending-goalkeeper link. Shot placement and shot xG are inputs for a separately fitted keeper model, not a ready-made, calibrated goalkeeper score.

**Result:** enough for a goalkeeper-specific prototype after keeper-substitution reconciliation and shot-model checks; not enough to put keepers on the same value scale as outfield players today.

## Gate 3 — season-specific team-accessible replacements

This gate remains **not passed**.

- Existing documented replacement cases are purposive examples, not a representative candidate pool; no case is established as replacement level.
- The Footy Cap historical spend audit matches only 144 / 780 club-seasons (18.5%) and includes only 32 / 40 league-season cells. It does not supply complete historical club wages/budgets.
- I screened Capology as a possible public salary alternative. Its support page says salary figures are estimates and direct CSV/XLSX export is unavailable on the standard site; its pricing page places full online salary access behind a subscription and says historical coverage is available only for selected leagues/seasons. Its historical coverage is a research lead, not a free, open, reusable 40-cell wage file.
- Transfer history can establish completed moves for some players, but a move alone does not establish a team's ex-ante alternative set or that a player was available at a specific decision date. The local Transfermarkt-derived feed has no wage field, so annualized fee-plus-wage affordability cannot be calculated consistently.
- Per the owner's selected rule, unknown-cost candidates must be marked unknown and excluded from the central affordable pool. Do not fill costs from market value or modern club budgets.

**Result:** team-accessible replacement cannot be calculated for most team-seasons with the current evidence. The all-league and selected-league averages can later be shown as above-average reference cohorts; they are not replacement level. Capology's own [support information](https://capology.com/support/) and [pricing page](https://www.capology.com/) support treating it as paid/estimated data rather than a no-permission free dataset.

## Gate 4 — out-of-time validation

An OpenPlay rolling expected-points **match-state** benchmark has now been run on 683,052 states from 14,330 fully score-reconciled matches. It samples the last observed event state in each two-minute interval, trains only on earlier seasons, and tests on the next full season. Four score/few-event issue matches are excluded; player identity is not used.

| Held-out season | Log loss | Brier | EP RMSE | Brier difference vs prior league-rate baseline | 95% match-bootstrap interval |
|---|---:|---:|---:|---:|---:|
| 2018–19 | 0.792 | 0.464 | 1.021 | -0.186 | [-0.197, -0.174] |
| 2019–20 | 0.788 | 0.461 | 1.039 | -0.185 | [-0.197, -0.174] |
| 2020–21 | 0.780 | 0.458 | 1.018 | -0.203 | [-0.214, -0.192] |
| 2021–22 | 0.799 | 0.467 | 1.030 | -0.183 | [-0.194, -0.171] |
| 2022–23 | 0.764 | 0.447 | 1.010 | -0.196 | [-0.206, -0.184] |
| 2023–24 | 0.810 | 0.474 | 1.040 | -0.177 | [-0.190, -0.164] |
| 2024–25 | 0.796 | 0.467 | 1.033 | -0.186 | [-0.198, -0.175] |

The state model improved over the prior-season league-specific outcome-rate baseline in all seven folds and all 35 league-season folds; every paired match-bootstrap Brier interval excludes zero. Expected-points decile calibration's mean absolute bin gap ranges from 0.057 to 0.077 across test seasons. This supports a team-level expected-points state benchmark across later seasons. It does **not** validate event action value, actor attribution, goalkeeper value, or a player replacement model. The 2024–25 season was used as an exploratory holdout and is not an untouched final evaluation after methods are frozen.

The 2017–18 player-action pilot remains a development sample. The new source supports future chronological action-value tests, but no player-level action credit or WAR was evaluated here. Keep team-level state transitions separate from player scores.

## Current decision and next work

The team-level event-state expected-points validation is complete for this exploratory benchmark. The next model work can compare full transition and clock-adjusted event deltas in out-of-time fixtures, while retaining team-level accounting and source flags. The project is not ready for player WAR values on the website.

Before a player score can be considered, the remaining work is:

1. Independently sample-review the current 20,227 equal-appearance deterministic candidates and resolve the 2,190 flagged rows without fuzzy auto-approval. The 40-case review currently available is targeted and does not estimate crosswalk precision.
2. Keep the 253 actor/stat exceptions quarantined; retain all 1,191 distinct event-key collisions and their time-first ordering; then review the 26 missing fixtures, 10 issue matches and 98 lineup minute conflicts before publishing a reusable clean/flagged derivative with source lineage.
3. Obtain or validate a documented formation-slot mapping and recover goalkeeper substitution minutes; only then produce player-specific-position exposure.
4. Build and evaluate a shot-stopping model from auditable shot/keeper assignments; keep keeper-specific results separate unless a common outcome-scale bridge validates.
5. Add historically timed wages, transfer costs and direct availability evidence for feasible replacement candidates; otherwise keep the team-budget comparison unavailable or explicitly scenario-only.
6. The seven-fold event-context expected-points walk-forward, sampled transition decomposition, feature ablations, and expected-goal-difference cross-check are documented in [the 2026-11-05 follow-up](openplay_action_value_walkforward_2026-11-05.md). These show small forecast-fit changes but a much larger, feature-sensitive transition scale; they do not establish action value. Next, test transition accounting and sampling alternatives without player credit, then assess player-level stability only after identity/position gates pass. Preserve a genuinely untouched season for frozen-method evaluation.
7. Resolve source-use provenance before any public player-level output. Do not publish the raw archive.

This closes the **source acquisition and first-pass audit** for the OpenPlay candidate and establishes a rolling team-state expected-points benchmark. It does not close the full data foundation, approve a WAR formula, or authorize player WAR publication.
