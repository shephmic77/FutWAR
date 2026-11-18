# Poisson-lineup player-credit forward proxy check — 2026-11-18

## Question

Does the scoreline model's player-level expected-points change rank players in a way that carries into next season? The model forecast experiment showed a small goal-difference gain but worse expected-points accuracy. This follow-up extracts an experimental per-90 player signal and checks it against next-season player statistics. The next-season stats are a proxy, not ground truth for player impact.

## Candidate signal

For each candidate season (2021–22 through 2024–25), a Poisson goals-for model is fitted on earlier OpenPlay Big Five match rows. Regularization is chosen on the latest season available before the candidate season, then the model is refit on the full prior history. The player signal is the model-implied expected match-points difference between a full 90-minute exposure and zero exposure, averaged over the player's observed match contexts. When the focal player is removed, the model adjusts both their team's and opponent's goal rates using the fitted player coefficient.

This zero-exposure contrast is **not** a comparison with any of FutWAR's six replacement references. It is an experimental model association; the position source is the player's minutes-dominant OpenPlay match position, not the season-start FIFA/EA FC roster role. Goalkeepers are excluded from this outfield check.

## Evaluation

- Candidate-to-future transitions: 2021–22 → 2022–23, 2022–23 → 2023–24, 2023–24 → 2024–25, and 2024–25 → 2025–26.
- Outcomes: eight same-provider next-season rates (goals, assists, npxG, shots, key passes, progressive passes, tackles, and interceptions).
- Rank comparisons are made within league, source-reported position, metric, and season transition. The prior-season same-stat rate is the persistence benchmark.
- Sensitivity thresholds require at least 300, 600, or 900 minutes in the model-score season, the current-stat season, and the future-stat season.
- Group correlations are macro-averaged equally; they are not weighted by group size. No player rows or coefficients are exported.

## Results

| Minimum minutes | League × position × metric × transition groups | Model signal mean rank correlation | Prior same-stat persistence | Groups where model beats persistence |
|---:|---:|---:|---:|---:|
| 300 | 1,704 | 0.078 | 0.471 | 266 / 1,704 (15.6%) |
| 600 | 1,592 | 0.075 | 0.491 | 234 / 1,592 (14.7%) |
| 900 | 1,520 | 0.080 | 0.512 | 207 / 1,520 (13.6%) |

The extracted lineup signal has weak rank association with next-season rates and trails simple same-stat persistence at every exposure setting. This does not validate a player WAR score. It is also not conclusive evidence that the underlying player impact is zero: future box-score rates measure a different target and share the same provider's player IDs and stat definitions.

## Decision and limits

This player-credit extraction does not pass the current player-level proxy check. Combined with the direct expected-points forecast result, it is not ready for the website as a player score. Do not rename it WAR or use its zero-exposure contrast as the replacement baseline. Further development needs a player-level validation target that is closer to contribution, independent identity/source checks, uncertainty for individual estimates, and a frozen future-season evaluation not already inspected in development.

Known limitations include source-ID continuity, lineup-selection/tactical/injury confounding, actual minutes used only retrospectively, dominant source position rather than FIFA/EA roles, no keeper bridge, independent Poisson scoreline assumptions, and all four future transitions having already been examined in development. Group correlations share players and seasons, so the table is descriptive and has no independent-sample confidence interval.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
py scripts\audit_poisson_lineup_player_credit_forward.py
```

Aggregate output is written to ignored `reports/war_prototype/poisson_lineup_player_credit_forward/`.
