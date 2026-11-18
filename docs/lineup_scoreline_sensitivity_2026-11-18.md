# Lineup plus expected-goal scoreline sensitivity — 2026-11-18

## Question

Can lineup impact be modeled as goals for and against, then translated into expected match points from the predicted scoreline? This tests a different outcome link from direct regression on observed 0/1/3 points. It is a model-design sensitivity, not a final FutWAR formula or player-credit result.

## Design

- Data: OpenPlay v0.1.0 Big Five matches, 2017–18 through 2024–25; fixtures must have a reconciled 90-minute score and exactly 11 distinct listed starters on both sides.
- Evaluation: seven chronological folds, 2018–19 through 2024–25. In each fold, regularization was selected on the latest earlier season, then refit on all prior seasons. The first fold had only one prior season and used a fixed Poisson penalty of 10 because no inner validation season was available.
- Two goal models: prior-only league, club/opponent, home/away, team-form and Elo context; and the same features plus signed lineup-minute exposure for players on both sides.
- A Poisson model predicts each team-perspective goals-for outcome. Each match's expected points are derived from the independent home/away Poisson scoreline probabilities as `3 × P(win) + P(draw)`. Expected goal difference is reported separately.
- A direct Ridge regression on observed team-perspective 0/1/3 points is retained as a comparison. Regularization is also selected only from earlier seasons.
- Fixture-cluster paired bootstrap intervals compare the scoreline lineup model with the scoreline context model over 12,503 held-out fixtures.

## Results

| Model | Expected-points MAE | Expected-points RMSE | Expected-goal-difference MAE |
|---|---:|---:|---:|
| Direct regression, context + clubs | 1.0471 | 1.2055 | — |
| Direct regression, adjusted plus-minus | 1.0636 | 1.2053 | — |
| Poisson scoreline, context + clubs | 1.0714 | 1.2135 | 1.2931 |
| Poisson scoreline, with lineup exposures | 1.0770 | 1.2113 | 1.2861 |

The scoreline lineup model worsened expected-points MAE versus its context reference by **+0.00553** (95% paired fixture-bootstrap interval **+0.00425 to +0.00674**). It worsened expected-points MAE in six of seven folds. The same model improved expected-goal-difference MAE by **0.00698** (95% interval for candidate-minus-reference **−0.00927 to −0.00453**) and improved goal-difference MAE in all seven folds. Direct regression on match points had lower average expected-points error than either Poisson scoreline model.

## Interpretation and limits

This repeats the outcome-scale conflict seen in other lineup checks: lineup exposure carries a small, consistent goal-difference signal in this setup, but does not improve the owner's primary expected-points target. Better goal-difference forecasts do not validate a player contribution estimate or establish a points conversion. The scoreline approach also assumes independent home and away goals; it does not model score dependence. Around 14%–21% of held-out player-minute exposure slots involve IDs absent from that fold's training history, and lineup IDs, role/position, selection, injuries, and tactics remain imperfectly verified or controlled. The years have already been inspected during development, so this is not a final untouched validation sample.

**Decision:** This scoreline transformation does not rescue lineup impact for the primary target. Keep it as a documented comparison only. Do not export player coefficients or add any of these values to the site. The current lineup model route has no evidence-supported individual player credit; a later valid player score still needs a design that improves expected-points evaluation and independent player-level validation.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
py scripts\run_openplay_lineup_scoreline_sensitivity.py
```

Aggregate metrics are written to ignored `reports/war_prototype/lineup_scoreline_sensitivity/`. No player coefficients, IDs, or scores are exported.
