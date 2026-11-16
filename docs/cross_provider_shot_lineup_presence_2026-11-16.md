# Cross-provider shot-actor lineup plausibility — 2017–18

## Result

Across 1,826 Big Five fixtures linked between Wyscout and OpenPlay, the audit checked 40,461 Wyscout shot events against the corresponding OpenPlay team lineup and recorded stint. Names were matched only within the same fixture and team. Exact normalized names and the project's constrained, one-to-one unique-token name variants were counted separately.

| League | Shot events | Exact lineup-name match | Name-variant candidates | Within recorded stint | Near boundary, within 4 minutes | Outside after allowance | Unresolved |
|---|---:|---:|---:|---:|---:|---:|
| Premier League | 8,451 | 5,651 | 2,070 | 7,661 | 58 | 2 | 730 |
| La Liga | 7,979 | 1,482 | 4,914 | 6,374 | 22 | 0 | 1,583 |
| Serie A | 8,806 | 6,135 | 2,159 | 8,230 | 63 | 1 | 512 |
| Bundesliga | 6,898 | 5,279 | 1,204 | 6,443 | 39 | 1 | 415 |
| Ligue 1 | 8,327 | 5,884 | 1,900 | 7,736 | 47 | 1 | 543 |
| **All five** | **40,461** | **24,431** | **12,247** | **36,444** | **229** | **5** | **3,783** |

The status columns sum to the shot-event total. “Near boundary” means the event is outside the recorded stint but within the four-minute allowance; it is not counted as strictly within the interval.

Exact names alone mapped to a unique lineup player in 24,431/40,461 events (60.4%); including constrained name variants raises candidate coverage to 36,678/40,461 (90.7%). Variant matches drive most La Liga coverage: 4,914 of 6,396 mapped candidate names there are variants, while exact-name coverage is only 18.6% of the league's shot events.

## Interpretation and limits

- A matching player name in the team lineup and a plausible on-pitch time means the player **could** have taken the shot. It does not establish that they did.
- Five candidate links fall more than four minutes outside the recorded stint. They are audit flags, not confirmed errors. The tolerance is deliberately wide and was motivated by a separate small substitution-time review: among 32 comparable numeric cases, 25 differed by 1–4 minutes. That sample does not estimate population-wide clock accuracy.
- The lineup table is a separate table but comes from the OpenPlay release; it is not an independently adjudicated match sheet. Name variants remain candidate links, especially consequential in La Liga.
- This check covers shots in 2017–18 only. It does not validate all event actors, player-season IDs, player credit, goalkeeper value, expected-points contribution, or WAR.
- No raw event rows or player identities are published by this aggregate audit. No corrections or player scores are produced.

## Reproduction

From the project root in Windows PowerShell:

```powershell
py scripts\audit_cross_provider_shot_lineup_presence.py
```

The script verifies pinned source hashes and writes aggregate outputs to the ignored local directory `reports\cross_provider_shot_lineup_presence\`.
