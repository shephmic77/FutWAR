# OpenPlay lineup-presence walk-forward — 2026-11-05

## Question and decision

Does player identity/exposure in a match's lineup improve held-out expected-points forecasts beyond a simple pre-match context model? The current answer is **no** at the fixed `C=0.03` shrinkage setting: both kickoff starting-XI features and realized player-minute features increase log loss in every tested future-season fold. This does not prove that every adjusted lineup method is unhelpful. It does mean FutWAR should not add the current lineup-presence signal into a player score, and especially should not call it the portion that action values miss.

This is a match-level prediction experiment, not a causal impact estimate, player score, or final WAR formula. It exports no player coefficients or player-level results. The starting XI is known at kickoff but reflects club selection and availability. Realized minutes are post-match information and can respond to score, substitutions, dismissals, injuries, and coaching decisions.

## Data and model

- Source: pinned local OpenPlay v0.1.0 `matches.parquet` and `lineups.parquet`; Big Five, 2017–18 through 2024–25.
- 14,334 target-scope scored matches were checked; 14,328 had two valid unique starting XIs and entered the analysis. Six were excluded for absent or structurally invalid lineup data.
- Both teams from every fixture remain together. Seven expanding-season folds train on all earlier seasons and test on the next season, 2018–19 through 2024–25.
- The baseline is multinomial logistic regression for team-perspective league points (0/1/3), using league, home/away, pre-match Elo difference, and pre-match last-five-points-per-match difference. Ratings and form update only after all same-day fixtures, preventing same-day result leakage.
- The starting-XI candidate adds signed player identity indicators: +1 for each own starter and −1 for each opposing starter. The realized-exposure candidate instead adds signed player minutes divided by 90. Players absent from training have zero learned effect in a held-out row.
- The lineup model uses fixed `C=0.03`, inherited from an earlier feasibility pilot as a diagnostic setting; it is not selected or approved. Log loss is compared on identical held-out team-match rows. The reported 95% intervals resample whole fixtures and condition on fitted models and this setting; they omit model-refit and feature-selection uncertainty.
- Held-out starting-XI slots containing player IDs absent from the training seasons range from 11.4% to 19.2% by season. Those IDs contribute no learned player coefficient in that fold. This is a separate unseen-player coverage limitation, not missing lineup exposure.

## Results

The difference is lineup model minus pre-match context; positive log-loss differences favor the context-only model.

| Held-out season | Matches | Context log loss | Starting-XI log loss | Difference, 95% fixture-bootstrap interval | Realized-minutes log-loss difference |
|---|---:|---:|---:|---:|---:|
| 2018–19 | 1,826 | 1.00226 | 1.00554 | +0.00328 [−0.01028, +0.01664] | +0.00421 |
| 2019–20 | 1,724 | 1.00153 | 1.01802 | +0.01649 [+0.00394, +0.02901] | +0.01629 |
| 2020–21 | 1,826 | 1.00675 | 1.02209 | +0.01534 [+0.00155, +0.02845] | +0.00872 |
| 2021–22 | 1,811 | 1.00065 | 1.00801 | +0.00736 [−0.00413, +0.01950] | +0.00168 |
| 2022–23 | 1,818 | 0.99377 | 1.01245 | +0.01868 [+0.00601, +0.03222] | +0.00736 |
| 2023–24 | 1,751 | 0.97857 | 1.02076 | +0.04219 [+0.02847, +0.05744] | +0.03248 |
| 2024–25 | 1,751 | 0.98559 | 1.01157 | +0.02598 [+0.01173, +0.04052] | +0.01695 |

Across the seven folds, mean log-loss difference is +0.01848 for the starting-XI model and +0.01253 for the realized-minute model. All seven point estimates favor the pre-match context-only model. Five starting-XI intervals and three realized-minute intervals exclude zero in that direction; the remaining intervals include zero, and none favor adding lineup information. Starting-XI Brier score also worsens in all seven folds (mean difference +0.01228). This is a caution against adding presence coefficients without a stronger, properly selected model.

### Earlier-season shrinkage selection

Because the fixed `C=0.03` result could depend on regularization, a second sensitivity selected `C` only from an inner, earlier-season validation fold, then refit on all outer-training seasons and evaluated on the outer held-out season. The grid was `0.003, 0.01, 0.03, 0.1`; the lower value means stronger shrinkage. For the first 2018–19 test fold there was only one training season, so `C=0.03` was retained without tuning. All later outer folds selected on the most recent earlier season. The context model's `C` was also selected using that same inner validation season.

| Outer test | Inner validation | Selected C: context / starting XI / minutes | Starting-XI log-loss difference, 95% interval | Realized-minute difference, 95% interval |
|---|---|---|---:|---:|
| 2018–19 | — | 0.03 / 0.03 / 0.03 | +0.00328 [−0.01083, +0.01653] | +0.00421 [−0.00934, +0.01816] |
| 2019–20 | 2018–19 | 0.003 / 0.01 / 0.01 | +0.00055 [−0.00547, +0.00666] | +0.00025 [−0.00611, +0.00639] |
| 2020–21 | 2019–20 | 0.003 / 0.003 / 0.003 | −0.00285 [−0.00608, +0.00038] | −0.00378 [−0.00706, −0.00049] |
| 2021–22 | 2020–21 | 0.003 / 0.003 / 0.003 | −0.00320 [−0.00609, −0.00019] | −0.00405 [−0.00704, −0.00119] |
| 2022–23 | 2021–22 | 0.003 / 0.003 / 0.01 | −0.00327 [−0.00648, −0.00022] | −0.00529 [−0.01272, +0.00198] |
| 2023–24 | 2022–23 | 0.003 / 0.003 / 0.01 | +0.00277 [−0.00094, +0.00621] | +0.00788 [+0.00028, +0.01547] |
| 2024–25 | 2023–24 | 0.1 / 0.003 / 0.003 | +0.00038 [−0.00365, +0.00462] | −0.00109 [−0.00529, +0.00320] |

The selected-C starting-XI model improves log loss in three of seven folds, with only two paired intervals excluding zero in its favor; the mean difference is −0.00033. The selected-C realized-minute model improves in four folds, with two intervals favoring it and one interval favoring context; mean difference is −0.00027. These changes are tiny relative to context log loss near 1.0 and are not stable across seasons. A single inner validation season also gives noisy hyperparameter selection, so this sensitivity is not a preferred model. Taken together, the data do not support a reliable lineup increment for the combined score yet.

## Interpretation and remaining checks

1. This result is **not** an action-plus-lineup test. The event transition sample is not a continuous, validated player-match action total, so there is no clean action-only forecast to subtract from the lineup forecast.
2. It does not estimate player value or teammate uplift. The lineup model's player coefficients are withheld; player presence is entangled with team selection, coaching, tactical roles, injuries, and opposition.
3. The current feature set has no specific-position minutes, role interactions, or opponent-player interaction terms. The inner temporal shrinkage check uses one validation season at a time and is still a limited sensitivity, not a fully stable tuning procedure. These are candidates for a separate validation-stage model, not reasons to rescue this result by tuning on the outer test seasons.
4. Results are useful evidence against automatically adding a simple lineup component. Keep adjusted lineup and teammate uplift separate until a nested, chronological validation shows incremental value beyond out-of-fold action predictions and controls selection/overlap.
5. The OpenPlay publisher's CC BY 4.0 declaration does not independently resolve upstream authorization for publicly displayed player-derived outputs. Do not add player coefficients or scores to the public site.

## Reproduce

From repository root in Windows PowerShell:

```powershell
py scripts\run_openplay_lineup_presence_walkforward.py
```

The script writes aggregate-only season and league results plus `run.json` under ignored `reports/openplay_lineup_presence_walkforward/`. It does not alter source files or write player values. The implementation also checks lineup structure, fixes team-perspective signs for pre-match strength/form, and resamples paired fixture losses.
