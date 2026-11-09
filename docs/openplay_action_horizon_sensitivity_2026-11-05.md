# OpenPlay 3/5/10-event horizon sensitivity — 2026-11-05

## Status and purpose

This is a team-state expected-points sensitivity experiment. It compares what the fitted state-only and event-context models predict after 3, 5, or 10 later source event rows in the same match and team perspective. It assigns no player credit, estimates no isolated action value, selects no horizon, and produces no player score.

## Data and split

- Hash-verified OpenPlay v0.1.0 event files from all five leagues and eight seasons.
- Retained 14,330 score-reconciled regulation matches; event-derived scores matched the supplied 90-minute results in all of them.
- Constructed 44,683,476 team-perspective event states. Each chronological test fold samples starts every fifth event row; endpoints are the exact 3rd, 5th, or 10th later row in that same match/team-perspective stream.
- Trained on earlier seasons and evaluated on the next season for seven folds (2018–19 through 2024–25). The final season has already informed method development and is not an untouched final test.
- The paired model views use identical sampled starts and endpoints at each horizon. Match IDs are shared across horizons; repeated transitions and the two team perspectives are clustered within fixtures in the underlying source, so these counts are not independent observations.

## Results

Values below are equal-weight averages of the seven season-fold means. “Full” includes clock movement; “clock-adjusted residual” subtracts a hypothetical forecast with the starting event and score state frozen while the endpoint clock advances. All values are mean absolute expected-points movement per sampled team-perspective endpoint transition.

| Later event rows | Sampled transitions | Held-out fixtures | State-only full | Event-context full | State-only clock-adjusted residual | Event-context clock-adjusted residual | Residual gap · paired 95% match-bootstrap interval |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 7,755,498 | 12,504 | 0.00400 | 0.02116 | 0.00324 | 0.02094 | 0.01770 [0.01761, 0.01779] |
| 5 | 7,745,616 | 12,504 | 0.00664 | 0.02480 | 0.00537 | 0.02446 | 0.01909 [0.01900, 0.01920] |
| 10 | 7,720,608 | 12,504 | 0.01322 | 0.03110 | 0.01072 | 0.03044 | 0.01971 [0.01961, 0.01981] |

For both models, mean absolute movement rises with horizon. Event-context residual movement is about 6.5×, 4.6×, and 2.8× the state-only residual at 3, 5, and 10 rows, respectively. The paired event-context minus state-only residual gaps use the same event-count weighting as the two residual means. Each interval uses 1,000 fixture resamples within held-out season, weights each sampled fixture by its sampled transition count, and gives each season equal weight. It is conditional on already fitted models and does not include model-refit or feature-selection uncertainty. The gap narrows as more events accumulate, but remains material. This reinforces the earlier warning that event features change transition scale much more than their small forecast gains justify. It does not establish that the state-only scale is an action value either.

## Interpretation and limits

- Each endpoint spans all intervening events by both teams, changes in match state, and clock movement. The endpoint delta cannot be assigned to its starting actor or divided among the events as though they were independent credits.
- The clock-only counterfactual is a modeling convention. It retains the starting score, red-card state, and event descriptors while advancing time; the residual therefore is not causal.
- The two models' forecast quality and transition sizes answer different questions. Neither transition series is calibrated against an observed action-level points target.
- Horizon values are aggregate diagnostics only. No event or player-level score is published in this report or saved by this script.
- The paired fixture bootstrap measures sampling uncertainty conditional on fitted models; it does not account for model training, feature selection, source errors, or causal uncertainty.
- Position-specific minutes, independently verified player identities, goalkeeper common-scale calibration, season-specific feasible replacements, and a final untouched validation period remain open gates.

## Reproduction

From the repository root in Windows PowerShell:

```powershell
py scripts\run_openplay_action_horizon_sensitivity.py
```

The script writes aggregate-only tables and a run record under ignored `reports/openplay_action_horizon_sensitivity/`. Its source labels the output as team-level, exploratory, and not player credit. The full outputs are `overall_horizon_summary.csv`, `season_horizon_summary.csv`, `league_season_horizon_summary.csv`, `paired_match_bootstrap.csv`, and `run.json`.
