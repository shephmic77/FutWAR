# OpenPlay action-horizon coverage — 2026-11-05

## Purpose

The owner asked to compare 3-, 5-, and 10-event horizons. This audit checks whether each future-event window exists in the full OpenPlay event streams. It does not fit an outcome model, price an action, credit an actor, or select the preferred horizon.

## Scope and rules

- Hash-verified all 40 pinned Big Five season event files against the OpenPlay source manifest.
- Retained score-reconciled 90-minute matches and first-/second-half event records, matching the scope of the expected-points state walk-forward.
- Excluded matches carrying source issues `score_differs_from_events` or `few_events`.
- Every regulation event row is counted as a possible start. A full window has the requested number of later event rows within that same match. Starts too close to the end are recorded as shortened. No event window crosses a match boundary.
- Each window still contains all intervening own-team events, opponent events, and clock movement. Window availability is not action attribution.

## Aggregate coverage

| Future event rows | Score-reconciled matches | Event rows / possible starts | Complete windows | End-shortened windows | Matches with at least one complete window |
|---:|---:|---:|---:|---:|---:|
| 3 | 14,330 | 22,341,738 | 22,298,748 | 42,990 | 14,330 |
| 5 | 14,330 | 22,341,738 | 22,270,088 | 71,650 | 14,330 |
| 10 | 14,330 | 22,341,738 | 22,198,438 | 143,300 | 14,330 |

The shortened shares of all possible starts are 0.19%, 0.32%, and 0.64%, respectively. Every included fixture has enough records for at least one complete window at all three horizons. The final event of each included match is one of the shortened starts and has zero future event rows.

## Interpretation

Coverage does not tell us which horizon predicts outcomes best or whether any starting action caused the endpoint change. A larger horizon accumulates more opponent events and clock movement. Compare the three on identical future-season fixtures, keep paired-team outcomes together, and report event-family and player-ID coverage before any actor-level analysis. The current event-context transitions remain feature-sensitive and are not calibrated action prices.

## Reproduction

From Windows PowerShell at the repository root:

```powershell
py scripts\audit_openplay_action_horizon_coverage.py
```

Aggregate results are saved under ignored `reports/openplay_action_horizon_coverage/`. Source files are not changed.
