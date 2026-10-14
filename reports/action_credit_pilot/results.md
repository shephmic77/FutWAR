# Shot-sequence action-credit comparison

## Purpose

This is a bounded comparison of two ways to assign the same modelled expected-points state changes to players. It does not estimate WAR, causal player impact, or a replacement baseline, and it does not approve a player-credit policy.

## Design

The pilot uses 2017–18 Wyscout events from the five leagues and only valid chronological test fixtures dated March–May 2018. For every action in an eligible shot-ending sequence, the expected-points model predicts the acting team's match points from a pre-action representation and a post-action representation. Their difference is the action's modelled EP state change.

The direct view credits each action's change to its recorded actor. The shared benchmark sums the same action changes inside the sequence and divides that sum equally among the sequence's distinct recorded actors. This equal split is deliberately simple and auditable. It is **not** a Shapley value: it does not evaluate counterfactual coalition worths.

Sequence proxies split on period or team changes, after Shot/Foul/Interruption/Offside, and before a restart Free Kick subtype. A proxy qualifies when its last event is a shot or a penalty/free-kick shot. These rules are practical boundaries over raw events, not validated possession IDs.

## Results

- 545 held-out fixtures across the five leagues.
- 12,581 shot-ending sequence proxies; 11,693 (92.9%) had complete actor IDs that linked to the Wyscout player profiles. The other 888 were excluded from **both** credit views.
- Eligible sequences contain 33,659 actions and 1,970 Wyscout player IDs. The sequence participant counts are in `summary.json`; many sequences contain only one actor, for whom both views assign the same credit.
- Direct credit totals 788.768 modelled EP-change units. Equal participant sharing also totals 788.768. Both exactly equal the eligible sequence sum, as required by the allocation design. This conservation check does not validate the modelled EP changes.
- Across all IDs, direct and shared totals have Spearman rank correlation 0.812; among players appearing in at least 25 eligible sequences, it is 0.881. Median absolute rank movement is 171 places across all 1,970 IDs, 66.5 among the 286 IDs with at least 25 sequences.

| League | Eligible sequences | Actions | Direct summed EP change | Rank correlation among IDs with ≥5 sequences |
| --- | ---: | ---: | ---: | ---: |
| Bundesliga | 1,916 | 5,273 | 126.623 | 0.789 |
| La Liga | 2,578 | 7,492 | 193.824 | 0.840 |
| Ligue 1 | 2,498 | 7,227 | 175.787 | 0.805 |
| Premier League | 2,093 | 6,052 | 140.534 | 0.799 |
| Serie A | 2,608 | 7,615 | 152.000 | 0.879 |

Player credit rankings differ because direct credit gives each action's modelled change to its actor, while the benchmark gives each distinct participant a common share of the full sequence sum. This particularly changes credit for players involved in many multi-actor sequences. These rankings use source IDs only; they are not reconciled to FutWAR player-season records.

## Interpretation and limits

The result demonstrates that credit allocation can change player ordering even when the sequence sum is held fixed. It does not show which ordering better predicts winning. These per-event before/after predictions are not a telescoping path through one continuous match-state series, so their sum must not be interpreted as total expected points created by a team or player. The modelled state changes are not causal effects, and the event model's held-out improvement over score/time/form was modest. Sequence boundaries are unvalidated proxies. The pilot covers one season and one test window, and shot-ending attacks omit most defensive and goalkeeper contribution. There is no league-strength adjustment, position adjustment, uncertainty interval, or identity reconciliation to the multi-season dataset.

The literature provides two useful distinctions. VAEP values adjacent game-state changes for the recorded action actor; it is not a final-points WAR model. Restricted Shapley instead requires player coalition values and admissible coalitions, which this equal-split pilot does not estimate. See [Decroos et al.](https://arxiv.org/abs/1802.07127) and [Cefis et al.](https://arxiv.org/abs/2603.11016).

## Reproduction

From Windows PowerShell at the repository root, using the project's Python 3.13 environment:

```powershell
$env:TEMP = Join-Path (Get-Location) 'reports'
$env:TMP = $env:TEMP
python scripts/run_expected_points_state_pilot.py
python scripts/compare_action_credit_pilot.py
```

The first command verifies source hashes and rebuilds the persisted held-out expected-points model. The second verifies the manifest again, constructs shot-ending sequence proxies, and writes the tables and graph in this folder. Raw source files remain untouched.
