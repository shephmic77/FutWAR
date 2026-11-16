# Cross-provider shot-event actor alignment — 2017–18

## Result

OpenPlay and Wyscout were linked on **1,826 Big Five fixtures** using the independently reconciled fixture keys. Shot events were then paired without using player names or IDs: same fixture, team side, half, and mutually unique nearest event time within five seconds. The second-half clock was converted to elapsed time from that half's start. This paired **37,425 events**, or **92.5% of the smaller provider shot-event total** across leagues. The median event-time gap was about one second in every league.

This is useful evidence that the two feeds often record a corresponding shot in the same match sequence. It is **not** proof that either provider assigned the correct player to each shot. Actor names were compared only after event pairing.

| League | Paired shots / smaller feed total | Exact normalized actor names / paired rows with both names | Constrained name-variant candidates |
|---|---:|---:|---:|
| Premier League | 7,789 / 8,451 (92.2%) | 5,098 / 7,788 (65.5%) | 1,866 |
| La Liga | 7,374 / 7,979 (92.4%) | 1,338 / 7,373 (18.1%) | 4,451 |
| Serie A | 8,137 / 8,806 (92.4%) | 5,507 / 8,136 (67.7%) | 1,971 |
| Bundesliga | 6,399 / 6,898 (92.8%) | 4,781 / 6,399 (74.7%) | 1,092 |
| Ligue 1 | 7,726 / 8,327 (92.8%) | 5,314 / 7,721 (68.8%) | 1,736 |
| **All five** | **37,425 / 40,461 (92.5%)** | **22,038 / 37,417 (58.9%)** | **11,116** |

The name-variant count uses the project's existing conservative one-to-one token matching rule within each match and team. It remains a sensitivity analysis, not an approved identity crosswalk. It is especially consequential in La Liga, where only 18.1% of paired shots have exactly matching normalized actor names.

## What it establishes and what it does not

- Event time and team provide a strong candidate correspondence for most shots in the shared 2017–18 feed.
- Exact actor-name agreement is uneven across leagues. The La Liga result is a clear warning against treating candidate player identities as verified.
- Provider clocks are rounded differently; the pairing window and reciprocal-nearest rule reduce, but do not eliminate, false pairings. The method does not use shot coordinates or independently adjudicated video.
- Name agreement still does not establish correct actor attribution. Both providers could share an error, and non-exact names may be harmless encoding differences or different people.
- The audit covers shots only, one season, and the records in both sources. It does not validate passes, duels, defensive actions, goalkeeper actions, other seasons, or player contribution values.
- No player identity was approved, no raw data were changed, and no player score was generated from this audit.

## Reproduction

From the project root in PowerShell, with the pinned research archives installed:

```powershell
py scripts\audit_cross_provider_shot_actor_alignment.py
```

The script verifies source archives against their manifests and writes aggregate league summaries to the ignored local folder `reports\cross_provider_shot_actor_alignment\`. It does not export event rows or player identities. The script uses the exact-date and home/away-team fixture bridge from `scripts\audit_cross_provider_goal_scorer_agreement.py`.
