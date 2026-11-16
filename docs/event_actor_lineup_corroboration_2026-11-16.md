# Cross-provider event-actor lineup corroboration — 2017–18

## Why this check was run

The player-value release gate needs independent evidence that event actors belong to the team and match credited to them. The Wyscout archive passes an internal structural check: nonzero IDs occur in its own match/team roster and player catalog. That alone cannot catch a valid source ID attached to the wrong real-world player. This follow-up checks a reproducible sample against OpenPlay lineups from a separate provider.

## Design

- Independently bridged the two providers' fixtures by competition, date, and home/away clubs, without using scores to create the bridge. The existing audit verified 1,826 of 1,826 fixture links and score agreements for 2017–18.
- Drew a seeded reservoir sample of up to 100 nonzero, catalog-linked Wyscout actors per league and top-level event family. The sample contains 4,500 actor-event rows across five leagues and nine families: Duel, Foul, Free Kick, Goalkeeper leaving line, Offside, Others on the ball, Pass, Save attempt, and Shot. Interruption remains context-only under the owner's decision.
- Checked whether each actor's normalized catalog name appears in the same team's OpenPlay positive-minute lineup for the bridged match. Exact unique name matches are separate from a conservative, unique token-level name-variant candidate.
- Source data are read-only. The reproducible script writes aggregate-only output to ignored `reports/event_actor_lineup_corroboration/`.

## Results

| League | Sampled actor events | Exact unique lineup-name match | Unique name-variant candidate | Unresolved name check |
|---|---:|---:|---:|---:|
| Bundesliga | 900 | 734 (81.6%) | 134 (14.9%) | 32 (3.6%) |
| La Liga | 900 | 170 (18.9%) | 562 (62.4%) | 168 (18.7%) |
| Ligue 1 | 900 | 711 (79.0%) | 138 (15.3%) | 51 (5.7%) |
| Premier League | 900 | 667 (74.1%) | 160 (17.8%) | 73 (8.1%) |
| Serie A | 900 | 659 (73.2%) | 175 (19.4%) | 66 (7.3%) |
| **Sample total** | **4,500** | **2,941 (65.4%)** | **1,169 (26.0%)** | **390 (8.7%)** |

Each league-by-event-family stratum has equal target sample size, so the sample total is **not a population-weighted estimate** of actor-link accuracy. La Liga has a notably different name-match pattern: many records require a name-variant candidate, and unresolved share is higher. That warrants source-specific name review before using a single pooled identity-link threshold.

## What this does and does not establish

An exact name in an independently supplied positive-minute lineup supports that the player appeared for that team in that match. A name-variant candidate is weaker and has not been manually confirmed. Neither result verifies that the player made the particular event, that the event outcome is correct, or that the actor key maps to the correct FutWAR player-season. Lineups do not provide precise on-pitch intervals in this check. The sample also covers only 2017–18.

**Disposition:** useful independent participation evidence, but the event-to-player validation gate remains open. Do not use this as a player-value validation result or publish player WAR from it. Continue with blinded, event-level review and season-specific identity reconciliation before calculating public scores.

## Reproduction and sources

From the repository root in Windows PowerShell:

```powershell
py scripts\audit_cross_provider_event_actor_lineup_corroboration.py
```

The script verifies source hashes against the pinned manifests before reading data. The cross-provider fixture bridge and source-attribution background are documented in the [goal-scorer corroboration audit](cross_provider_goal_scorer_audit_2026-11-13.md). OpenPlay release: [OpenPlay v0.1.0](https://github.com/nlbair/openplay/releases/tag/data-v0.1.0). Wyscout research archive: [Pappalardo et al. (2019)](https://doi.org/10.1038/s41597-019-0247-7). The publisher's license declarations are recorded in the project source manifests; they are not an independent legal opinion.
