# OpenPlay event-to-stat count reconciliation — 2017–18 through 2024–25

## Result

Across all **40 Big Five league-season cells**, nine event families were aggregated by match, team, and player ID and compared with the corresponding `player_match_stats` count. For keys with a recorded positive playing-time row, **all 2,280,038 of 2,280,038 grouped player-match-action counts agreed exactly** for passes, shots, tackles, interceptions, clearances, aerials, ball recoveries, dispossessions, and take-ons.

| Event family | Positive-minute player-match keys | Exact event/stat count matches |
|---|---:|---:|
| Pass | 419,050 | 419,050 |
| Shot | 196,679 | 196,679 |
| Tackle | 234,414 | 234,414 |
| Interception | 171,067 | 171,067 |
| Clearance | 223,257 | 223,257 |
| Aerial | 291,439 | 291,439 |
| Ball recovery | 360,949 | 360,949 |
| Dispossessed | 161,908 | 161,908 |
| Take-on | 221,275 | 221,275 |
| **Total** | **2,280,038** | **2,280,038** |

The release also contains some exceptions outside that eligible positive-minute set. Across the nine separate family checks there were two event-actor keys with no player-match-stat row, 34 event-actor keys without positive exposure, and 44 positive stat keys without a corresponding event row. These are action-family key counts, not unique people; a player-match may appear in more than one family. The event feeds also contain 393 actorless event rows across these families. Details stay in the aggregate local output.

## Interpretation

This verifies that the two tables are internally consistent for the checked action counts when an event actor has a positive-minute stats row. **It does not independently validate the actor ID or real-world player identity.** Both tables are from the same OpenPlay release and may share the same underlying annotation, so the comparison is not an independent ground truth. It also says nothing about event value, causal contribution, keeper calibration, position eligibility, or the replacement baseline. No player score or WAR formula is selected by this result.

## Reproduction

From the project root in PowerShell, with the pinned OpenPlay archive present:

```powershell
py scripts\audit_openplay_event_stat_reconciliation.py
```

The script verifies each source file against `data/openplay_source_manifest.json`, checks for duplicate player-match-stat keys, and writes aggregate summaries under the ignored `reports\openplay_event_stat_reconciliation\` directory. It changes no raw or processed source data and exports no player IDs or event rows.
