# Lagged player-form transfer check — 2025–26

**Status:** exploratory transfer diagnostic; not an untouched confirmation and not player-value validation.

## Question

Do season-to-date player-stat rates for the two starting XIs improve match-points forecasts over pre-match team context in the 2025–26 OpenPlay package, after training on 2017–18 through 2024–25?

## Design

- Train on 28,656 team-perspective rows from the eight target seasons, 2017–18 through 2024–25; evaluate 3,504 team-perspective rows from 1,752 2025–26 fixtures.
- Keep the earlier model structure: compare home/away, league, lagged Elo, and recent team form with that context plus differences in the starting teams' mean prior per-90 player rates. The player-rate inputs contain the five requested outfield groups and a separate goalkeeper group.
- Each player's rates use clean records dated before the target match date. Same-day match records cannot enter one another's features. Known source-issue and score/event-mismatch rows are excluded from player-rate history.
- Select logistic-regression regularization on the latest prior season (2024–25), then refit on 2017–18 through 2024–25. The 2025–26 outcomes do not select features or tune the model in this run.
- Compare expected-points MAE, multiclass Brier score and log loss. Paired 95% intervals resample fixtures, keeping both team perspectives together.
- The 2025–26 package has event files for all 1,752 Big Five fixtures; one Ligue 1 match is flagged for unusually few events. Six matches across all nine seasons fail the existing complete-starting-XI gate; none of the 1,752 target fixtures is excluded by that gate.

## Results

Lower forecast error is better. Delta is the player-form model minus the context-only model, so positive values favor context.

| Metric | Context only | Context + lagged player form | Difference | Paired 95% interval |
|---|---:|---:|---:|---:|
| Log loss | 0.99829 | 1.01412 | +0.01583 | +0.00555 to +0.02586 |
| Brier score | 0.59562 | 0.60681 | +0.01119 | +0.00444 to +0.01789 |
| Expected-points MAE | 1.05470 | 1.10619 | +0.05149 | +0.04063 to +0.06235 |

Log loss was worse with player-form inputs in all five leagues. The regularization chosen using 2024–25 was the same for both models (`C=0.003`). On that tuning season, the player-form model had lower log loss (0.9793 vs 0.9852), but the result did not transfer to 2025–26. This is a warning against treating the earlier seven-fold average improvement as stable.

### Diagnostic feature-group ablation

Each row removes one group, reselects regularization using 2024–25 only, and evaluates on the same already-inspected 2025–26 transfer target. Delta and intervals are log loss relative to context-only; positive favors context. These multiple exploratory comparisons locate possible failure sources; they do not select or remove a feature group.

| Feature set | Log-loss difference vs context | 95% paired-fixture interval |
|---|---:|---:|
| All five outfield groups + keepers | +0.01583 | +0.00555 to +0.02586 |
| Without finishing | +0.01097 | +0.00199 to +0.01968 |
| Without chance creation | +0.01438 | +0.00450 to +0.02401 |
| Without progression | +0.00911 | +0.00052 to +0.01756 |
| Without possession losses | +0.01532 | +0.00518 to +0.02521 |
| Without defending/duels | +0.01418 | +0.00438 to +0.02379 |
| Without goalkeeper features | +0.01463 | +0.00468 to +0.02436 |

Every single-group removal remained worse than context-only on log loss, and the point estimates for Brier score and expected-points MAE also remained worse. Omitting progression gave the smallest log-loss penalty in this target, but its interval still barely excludes zero and the season was already used in other project work. This does not establish that progression should be removed; it identifies a candidate for a frozen future-season sensitivity review.

## Interpretation and limits

This diagnostic does **not** show that players have no value. It shows that this particular team-mean summary of prior player statistics did not improve forecasts of the 2025–26 match outcomes beyond the tested team context; all three error metrics and all five league log-loss checks were worse. It cannot establish which individual player contributed, whether player rates are correctly attributed, or what a replacement player would have added.

2025–26 OpenPlay data have already informed other FutWAR research, so this is not a final untouched test. This season also falls outside the website library's current 2017–18 through 2024–25 display scope. Cross-season source/metric comparability, player identity, action credit, goalkeeper scale and replacement feasibility remain unresolved. Do not deploy these forecasts as player values or WAR, and do not tune the formula to this result. Reserve a future, frozen-design evaluation after data and method choices are locked.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
& 'C:\Users\mikey\AppData\Local\Programs\Python\Python313\python.exe' scripts\run_lagged_player_form_2526_transfer.py
```

The script writes aggregate metrics, league metrics, and team-match predictions under ignored `reports/lagged_player_form_2526_transfer/`. It exports no player scores or rankings. The ordinary 2017–18 through 2024–25 analyses retain their own configured input path.
