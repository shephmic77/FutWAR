# OpenPlay goalkeeper–shot interval linkage audit — 2026-11-05

## Decision

The OpenPlay formation archive can link a unique mapped goalkeeper to most shot records in a later-season holdout. This is useful for planning a goalkeeper-specific model and substantially better coverage evidence than a season-level keeper label. It is **not** goalkeeper value, shot-stopping credit, a calibrated keeper model, or permission to publish player outputs. Keep goalkeeper contribution separate from outfield scores until the model, identity, and scale gates are reviewed.

## Method

`scripts/audit_openplay_keeper_shot_linkage.py` uses formation-slot mappings learned from earlier seasons in the expanding-window audit. A formation slot is eligible as GK only when its earlier-season starter labels number at least 20 and mapping purity is at least 95%. The audit assigns a shot to the unique player in the opposing team's GK-mapped slot when the shot's expanded minute falls inside that formation spell's half-open time interval. Shootouts and own goals are excluded. If zero or multiple keeper IDs qualify, no keeper is assigned.

This is a cross-season source-derived assignment. The role map is learned from the same publisher's kickoff labels, not an independent ground-truth source; substitute/intermediate goalkeeper labels are not independently verified. Formation rows with invalid time intervals are excluded. The audit writes aggregate-only outputs to ignored `reports/openplay_keeper_shot_linkage/` and does not write player IDs, modify raw files, or calculate value.

## Results

- Scope: 2018–19 through 2024–25, all five leagues (35 league-season cells). 2017–18 provides the initial training history for the earliest holdout.
- The sample contains 314,337 non-shootout, non-own-goal shots, including 107,066 shots on target and 34,013 goals.
- Exactly one goalkeeper interval was linked to 300,005 shots (95.44%) and 102,129 shots on target (95.39%). One shot had ambiguous multiple keeper intervals and was not assigned.
- Of the remaining 14,332 shots, 882 had no mapped keeper interval in that match/team; 13,449 had mapped keeper spells for the match/team but the shot time fell outside those intervals. This points to formation timeline coverage/clock alignment as the main remaining issue, rather than simple absence of a keeper map.
- A clock-length sensitivity check found 189 matches with `expanded_max_minute > 105` despite none of the target matches being flagged `extra_time`. They contain 5,113 shots; only 90.59% of their 1,806 on-target shots linked to a unique keeper. For shots in matches with a maximum timeline of 105 minutes or less, on-target linkage is 95.47%. Some inspected fixtures include long legitimate delays/stoppage, while one event clock is confirmed wrong; review the group match by match. Their lower assignment coverage is not a reason to stretch a keeper's role interval without independent timing evidence.
- On-target assignment ranges from 94.18% to 96.48% across cells. It remains below complete coverage in every cell.
- The formation source has 120,088 rows in the 35-cell holdout scope; 379 have invalid intervals, and no malformed/mismatched player-slot arrays or spells with multiple mapped GK IDs were found in the eligible source sample.
- A separate, unapproved endpoint sensitivity extended final-team spells under four caps (5/10/15/30 minutes). At the 15-minute cap, coverage rose to 98.82% for all shots and 98.88% for on-target shots; on-target coverage was 99.03% for matches with timelines at or below minute 105. Coverage for the >105-minute group remained 90.59%, since those matches are not extended. This is a coverage sensitivity, not validation of the keeper assignment. See the [keeper endpoint sensitivity report](openplay_keeper_stoppage_sensitivity_2026-11-05.md) for unresolved no-interval and outside-interval counts.

These are assignment coverage rates, not assignment precision. The match/interval logic has not been independently checked against official keeper substitution records for a representative sample. A goalkeeper entering the field may still inherit a slot-based identity that lacks an independently verified role label.

## Reproduce

From the repository root in Windows PowerShell:

```powershell
py scripts\audit_openplay_formation_slots.py
py scripts\audit_openplay_keeper_shot_linkage.py
```

The keeper script consumes the formation-slot audit's ignored local mapping output. Run the formation audit first after a clean acquisition or source change.

## Remaining goalkeeper gates

1. Manually validate a stratified sample of shot-to-keeper assignments against match reports or another permitted independent source, including substitutions and boundary minutes.
2. Review the 189 >105-minute match timelines match by match, distinguishing legitimate interruptions from malformed clocks, then explain and reduce the remaining interval-time misses; do not fill them with the nominal starter.
3. Verify player identities across keeper slots, OpenPlay player-match stats, and the FutWAR player-season derivative.
4. Build separate keeper outcomes using appropriate shot-stopping and distribution evidence, with calibration and uncertainty; do not treat shot xG as post-shot xG.
5. Demonstrate a defensible common-scale bridge before combining goalkeeper and outfield values.
6. Resolve source-use provenance before public player-level outputs.

No value or formula choice is made by this audit.
