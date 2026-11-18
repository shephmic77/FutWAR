# Lineup exposure identifiability screen — 2026-11-18

## Question

Does the match-level lineup model have no opportunity to distinguish teammates because the same players always share the same minutes? This screen measures whether same-team players have nearly identical match-appearance histories. It is a design-data diagnostic; it does not estimate player impact or validate WAR.

## Method

- Use OpenPlay v0.1.0 Big Five match and lineup tables for 2017–18 through 2024–25.
- Keep in-scope fixtures with a reconciled 90-minute score. Require two listed teams matching the fixture, 11 unique starters for each, no duplicate player-team rows, and recorded minutes from 0 through 140.
- The screen retained 14,324 of 14,330 score-reconciled in-scope fixtures. Six were excluded because at least one side did not have exactly 11 unique listed starters. No other lineup-quality exclusions occurred.
- Within each club-season, include player pairs where both players meet a minimum total exposure of 300, 600, or 900 minutes.
- For each pair, compare their positive-minute appearance sets across that club's retained fixtures. Jaccard overlap is `shared appearances / appearances by either player`. A value of 1 means the pair appeared in exactly the same fixtures; 0.95 means their recorded appearance sets were at least 95% overlapping.
- Also count pairs with exactly identical appearance sets and pairs whose recorded minute totals match in every fixture, including zero-exposure fixtures.
- Output is aggregate only. No player names, IDs, coefficients, or scores are written.

## Results

All three cutoffs cover 780 club-season groups across the 40 league-season cells.

| Minimum minutes per player | Player-team-season records | Teammate pairs | Pairs with at least 95% appearance overlap | Identical appearance sets | Identical minute histories |
|---:|---:|---:|---:|---:|---:|
| 300 | 17,419 | 188,340 | 661 (0.35%) | 207 (0.11%) | 16 (0.01%) |
| 600 | 15,235 | 142,798 | 656 (0.46%) | 202 (0.14%) | 15 (0.01%) |
| 900 | 13,328 | 108,438 | 654 (0.60%) | 200 (0.18%) | 15 (0.01%) |

At 900 minutes, the pair-count-weighted mean of the 780 club-season median overlap values was 0.554. This is an average of group medians, not the median of all 108,438 individual pairs.

## Interpretation and limits

The data do not show that nearly all teammate pairs have identical match-appearance histories. Exact and near-exact overlap patterns are uncommon under these definitions. This makes “everyone always played with everyone” an incomplete explanation for the lineup model's weak results.

The screen does **not** show that player effects are statistically identifiable or accurate. It does not examine outcome information, role similarity, tactics, selection, injuries, changing player quality, within-match substitution timing, or identity errors. High correlation in minutes can remain even when appearance sets differ. Team-level prediction and the lineup model's next-season player-stat check still fail the current release gates. No coefficient, prior, player score, or replacement value is selected by this analysis.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
py scripts\audit_openplay_lineup_identifiability.py
```

Aggregate CSV/JSON outputs are written to ignored `reports/war_prototype/lineup_identifiability/`.
