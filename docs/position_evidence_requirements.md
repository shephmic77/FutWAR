# Specific positions and goalkeeper inclusion

Owner decisions recorded 2026-10-10. These supersede broad position families as the intended model labels, while preserving the original data and existing descriptive notebook.

## Position labels

Owner clarification: standard analysis uses only the main position per player-season, selected by **most total evidenced position minutes**. Additional evidenced positions belong in a separate interactive player profile and detailed history; see [profile direction](player_profile_direction.md). The existing five-appearance/10% rule remains for meaningful secondary labels. Sustained within-match secondary-role counting remains open, and current nominal labels are not automatically changed.

Use historically supported specific positions, such as LB, RB, CB, LWB and RWB. Do not silently interchange those positions in the replacement comparison. Specific midfield and attacking positions also require evidence; DF/MF/FW and their mixed source labels are insufficient. A final complete position vocabulary is still to be reviewed.

A secondary position requires both:

- At least **5 appearances** in that position.
- At least **10% of total appearances** in the analyzed season.

Both boundaries are inclusive. One isolated match does not produce a secondary label. The share denominator includes appearances with an unknown position; it cannot be reduced to just the conveniently labeled matches. Counts concern the scoped domestic leagues, not an unmarked mixture of league, cup and European matches. Aggregating a player across club stints requires identity verification first.

`main_position_by_time` implements the approved minute-based main-position rule and withholds assignments for incomplete coverage, unresolved spells, zero exposure or ties. The earlier appearance-frequency helper remains a legacy candidate diagnostic, explicitly marked non-final; it must not determine the standard-analysis main position. Observed qualifying secondary counts remain visible when coverage is incomplete, without claiming an exhaustive position list. The five-appearance rule concerns secondary position labels; it is not a performance-reliability threshold or a replacement-eligibility rule.

## Evidence needed

For each player appearance, establish a match identifier, historical club, competition/season, whether the player actually appeared, and a specific position with provenance. A player listed on the bench but never entering does not count as an appearance. Deduplicate by actual match and player before counting positions.

Current profile positions cannot be projected backward across eight seasons. A signing announcement can describe a position but does not count the games played there. Nominal starting formations do not prove wingback roles or in-game behavior. Substitutes and in-match role changes need adequate evidence; the first helper accepts one evidenced position per appearance and does not yet allocate multi-role spells within one match. That data representation needs review before applying the rule to such cases.

The publisher [documents game-lineup exports](https://github.com/dcaribou/transfermarkt-datasets), which are a research lead. Its description of starting and bench lineups does not verify played-position definitions, substitution coverage or all 40 league-seasons. Our six archived publisher exports do not yet establish this evidence. Audit definitions, terms, coverage and identities before importing new labels.

## Goalkeepers

Goalkeepers are included in the overall project. Develop their contribution method separately, then compare on a validated common goal/expected-points scale. Retain a goalkeeper-specific replacement comparator. The existing outfield notebook remains an outfield analysis; goalkeeper inclusion does not make its eight features adequate keeper measures.

Candidate domains to audit are shot stopping conditional on shot difficulty, cross/claim decisions, sweeping, distribution and costly errors. [StatsBomb's post-shot xG explanation](https://blogarchive.statsbomb.com/articles/soccer/a-new-way-to-measure-keepers-shot-stopping-post-shot-expected-goals/) distinguishes information about an on-target shot from pre-shot chance quality. [ASA's keeper goals-added research](https://www.americansocceranalysis.com/home/2021/6/20/valuing-goalkeepers-with-goals-added) illustrates a separate keeper treatment within an action-value framework. Neither method is adopted here.

An above-average shot-stopping measure is a possible component, not a change from the owner's above-replacement target. Provider definitions, calibration, opportunity exposure and overlap with defenders' credit require review. Clean sheets and save counts alone cannot establish isolated keeper value. Small samples need explicit uncertainty, including shot exposure rather than minutes alone.

The supplied CSV has 178 headers. A header scan found no names containing save, psxg, keeper, clean, cross, sweep, gk or goals against. This is a preliminary field-availability check, not a semantic audit of every column. Detailed keeper fields and comparable coverage remain unestablished.

## Implementation and checks

`scripts/position_labels.py` implements the owner's inclusive 5-appearance/10% rule without changing real player records. It rejects broad or comma-combined input positions, duplicate match IDs and evidence exceeding total appearances. Six synthetic tests cover both thresholds, incomplete coverage, duplicates, ties and zero appearances. All 45 project tests passed after directing temporary test files into the writable workspace; the first attempt failed because the sandbox's default temporary directory was inaccessible.

No full historical position labels or FutWAR values have been generated. The immediate data task is to audit a permitted historical match-position source, including substitutes and role definitions, alongside keeper-stat coverage.
