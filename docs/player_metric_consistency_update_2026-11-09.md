# Player metric consistency audit update — 2026-11-09

## Purpose

This is an arithmetic consistency screen of the corrected player-season derivative. It checks whether selected totals, per-90 rates, and reported residual fields agree within allowances for displayed precision. A flag is a review candidate, not evidence that the underlying source is wrong. No source or derivative values were changed.

## Reproduction

From the project root in Windows PowerShell:

```powershell
& 'C:\Users\mikey\AppData\Local\Programs\Python\Python313\python.exe' scripts\audit_player_metric_consistency.py --output reports\player_metric_consistency_20261109
```

The detailed row-level output is local and ignored by Git. The script's aggregate JSON and candidate CSV are under `reports\player_metric_consistency_20261109` on the machine used for this review; they are not part of the public site or repository release.

## Results

- 22,417 player-team-season rows screened.
- 159 arithmetic candidate rows across 65 distinct player-team-seasons.
- At an excess-beyond-rounding threshold of 0.05, 14 checks across eight player-team-seasons were flagged; five checks were in records with at least 900 minutes.
- The five high-exposure checks concern three player-team-seasons: Lucas Stassin (Ligue 1, 2024–25; reported goals-minus-xG and non-penalty-goals-minus-npxG residuals), Alassane Pléa (Bundesliga, 2021–22; non-penalty-goals-minus-npxG residual), and Breel Embolo (Bundesliga, 2021–22; goals-minus-xG and non-penalty-goals-minus-npxG residuals).
- Per-90 versus total comparisons also flag 40 xG/90, 34 npxG/90, and 24 xAG/90 rows at the audit's standard rounding tolerance. These require definition/denominator review before they can be interpreted as errors.

The residual examples show why the displayed totals cannot be assumed to reproduce every residual field: providers may use unrounded values, differing penalty conventions, or different model/source definitions. The current screen does not determine which explanation applies to an individual row.

## Disposition and WAR readiness

Keep all raw and corrected values unchanged. Before using these fields in a player score, trace each flagged field to its exact provider definition and source row, then decide whether the metric is comparable, needs a separate correction with provenance, or should be excluded. Do not infer xG quality or player finishing skill from the residual arithmetic alone.

This audit improves the input review but does not close the event/player identity, actual-position minutes, team-accessible replacement, or untouched out-of-time validation gates. Expected-points action forecasts remain team-level experiments; this audit does not produce or validate a player WAR value.
