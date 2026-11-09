# OpenPlay teammate-uplift overlap support — 2026-11-05

## Question and boundary

Across the eight target seasons, do repeated same-team exposures exist to compare a teammate's outcomes while a focal player is on the pitch and while the focal player is off it? This is an exposure-support audit only. It measures neither teammate performance nor whether a player's presence improves it; it creates no player effect, coefficient, or WAR score.

## Data and construction

- Source: pinned OpenPlay `data-v0.1.0/lineups.parquet`, verified against `data/openplay_source_manifest.json` before reading.
- Scope: Big Five domestic leagues, 2017–18 through 2024–25; 14,334 matches, 40 league-season cells, and 780 club-seasons represented.
- Positive-minute intervals use source `minute_on` and `minute_off`, clipped to the nominal 0–90 window. Stoppage and extra-time minutes are excluded to keep a common conservative exposure definition.
- Six of 28,668 club-match lineup groups were excluded because they did not contain exactly 11 source-listed starters. The remaining 28,662 groups have unique player IDs and interval lengths that agree with source minutes. No IDs or pair-level rows are written.
- Zero-minute bench rows with blank on/off times are treated as zero exposure. The 98 rows with `played=True` but zero minutes are retained as zero exposure, consistent with the source player-match minutes; the conflicting flags are counted, not repaired.
- Every ordered focal-player/teammate pair within a club-season accumulates teammate minutes overlapping the focal player's intervals (“with”) and the teammate's other playing minutes (“without”). A teammate may contribute to both states within one match if substitutions overlap only part of the match.

## Aggregate sensitivity results

Cutoffs are exploratory support thresholds, not approved model eligibility rules.

| Minimum teammate minutes in each state | Ordered pair-season records | Distinct source focal IDs | Club-seasons with support | Median with / without minutes | Median matches with / without |
|---:|---:|---:|---:|---:|---:|
| 90 | 334,303 | 6,038 | 780 / 780 | 566 / 806 | 12 / 15 |
| 180 | 261,405 | 5,605 | 780 / 780 | 695 / 871 | 13 / 16 |
| 450 | 138,461 | 4,889 | 780 / 780 | 946 / 1,039 | 17 / 19 |
| 900 | 39,721 | 3,820 | 780 / 780 | 1,251 / 1,294 | 20 / 22 |

Every league-season cell has at least one eligible pair at each threshold. A pair-season record is an ordered source focal ID / teammate ID within one team-season; a pair recurring in another season counts again. The smallest cell-level count at the 900-minute threshold is 353 pair-season records in Ligue 1 2019–20; that league-season has 20 club-seasons and all have some supported pair. This indicates broad overlap support for a future aggregate teammate-outcome study, not enough evidence to identify whose presence raises a teammate's performance. IDs have not been independently verified as real-world player identities.

## Interpretation and next gate

The audit answers the exposure-overlap question more broadly than the earlier 2017–18-only Wyscout report. It does not supply an outcome tied to expected points or goal difference, adjust for opponents, score/time, tactics, roles, selection, or injuries, or establish correct player identity across the player-season panel. Its pair counts are not independent observations; multiple pairs share players, teams, and fixtures. Do not infer significance from these counts.

The next defensible teammate-uplift experiment would need verified identities and an out-of-fold player-action/outcome signal, compare both same-teammate on/off contrasts and adjusted player-by-teammate interactions, use fixture-cluster uncertainty, and reserve future seasons for final validation. Until then, keep teammate uplift out of the player score and present this only as feasibility evidence.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
py scripts\audit_openplay_teammate_uplift_overlap.py
```

Aggregate JSON and sensitivity CSV are written under ignored `reports/openplay_teammate_uplift_overlap/`. The source archive is never edited. The manifest's OpenPlay license declaration and the project's public-output gate remain separate; owner approval does not independently validate upstream rights.
