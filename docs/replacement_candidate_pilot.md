# First replacement-candidate evidence pilot

Reviewed 2026-10-10 after the owner approved investigating a small sample of documented low-cost replacements. Four signing cases with accessible official evidence were selected to test the evidence workflow. These cases are not random, representative, or confirmed replacement-level players. Their performance was not combined into a baseline.

## Cases and recorded league exposure

Minutes, appearances and starts below come from the existing audited SQL snapshot, not from the signing announcements. Nominal positions are retained exactly. Research links use the existing local source record plus player/club/league/season labels; no cross-provider player IDs or tactical roles are assigned.

| Player / club / season | Nominal position | Minutes | Appearances | Starts | Official acquisition evidence | Interpretation |
|---|---|---:|---:|---:|---|---|
| Ryan Bertrand / Leicester / 2021-22 | DF | 337 | 4 | 4 | [Club departure notice](https://www.lcfc.com/media-article/Seven-Players-To-Depart-LCFC) confirms an earlier free transfer | [Target-season knee injury report](https://www.lcfc.com/media-article/Rodgers-Delivers-Fitness-Update-On-Barnes-Ricardo-and-Fofana) makes low minutes an unreliable talent classifier; no full absence duration estimated |
| Andros Townsend / Everton / 2021-22 | MF,FW | 1,455 | 21 | 17 | [Premier League signing announcement](https://www.premierleague.com/en/news/2193831) confirms free-agent status after Palace contract expiry | Actual signing establishes availability for this transaction, not low wages or access for every club; complete injury history not reviewed |
| Nampalys Mendy / Lens / 2023-24 | MF | 1,052 | 16 | 13 | [Lens announcement](https://www.rclens.fr/fr/news/mercato-arrivee-rclens-nampalys-mendy-2025-20230904) confirms out-of-contract status and describes adding midfield depth | Relevant depth-signing evidence, but no replacement-level talent conclusion; signed 4 September, so full-season exposure is not assumed |
| Pedro / Roma / 2020-21 | MF,FW | 1,591 | 27 | 20 | [Roma announcement](https://www.asroma.com/en/news/58508/roma-complete-pedro-signing) confirms expired Chelsea contract | An accomplished player can be out of contract; free-agent status does not establish low ability or low total cost |

Wages, signing bonuses, agent costs and total acquisition costs are unknown for all four cases. No historical fitness state is inferred for unreviewed periods. The sample covers three leagues and three distinct seasons, with no La Liga or Bundesliga cases; it does not establish full target coverage or a replacement pool.

## Owner's additional research concerns

The owner proposed that club budget, attraction, league, academy options and free agency could affect the available replacement. This is recorded as a research option, not an adopted budget percentage.

A common replacement standard measures contribution against a shared comparator. A club-specific scenario measures the loss against alternatives that particular club could realistically access. The owner approved keeping the common standard in core FutWAR and the club-specific scenario as a separate comparison on 2026-10-10. The second can change a player's value when club resources change even if their performance does not. A documented transfer does not reveal whether every other club could acquire that player. Numerical standards and any variation by position, league or season remain undecided.

A percentage of budget alone does not identify a player or establish skill. Define which budget and which costs it covers before testing such a scenario. Academy alternatives also need historical eligibility, availability and performance evidence; they are not automatically zero-cost or equivalent to experienced reserves. These variables remain proposed explanatory/context variables, not fixed bonuses or penalties.

The owner also requested protection against low-volume rates and differences in league difficulty. Record these as requirements for future estimation:

- Do not label high per-90 rates from small samples as reliable replacement performance. Investigate statistical stabilization, such as pulling uncertain estimates toward a defensible broader reference, and report uncertainty. The exact estimator and minimum exposure remain undecided.
- Keep player-level averages distinct from exposure-weighted averages. Equal weighting can overemphasize tiny samples; weighting by minutes can allow a few high-minute players to dominate. Report effective sample information and sensitivity rather than choose an average silently.
- Combine club stints only after identity verification. Do not let a short transfer stint classify an otherwise regular starter as a reserve.
- Do not interpret league-specific rates as a common ability scale. Study team, opponent, role, possession and competition context. A Ligue 1-to-Premier League move does not guarantee a particular direction or size of output change.
- For transfer-based comparisons, account for selection into transfers, age, playing time and role changes. Restrict training/context data to information available at the evaluation time. Future outcomes may be used for held-out validation, not leaked into historical estimates.
- Distinguish local replacement-relative value from cross-league transferable strength. Changing replacement pools alone does not calibrate absolute league quality.

No candidate rates were averaged, no league multiplier applied and no performance score calculated in this pilot.

## Reproduction and evidence handling

Factual evidence notes are stored privately in `data/raw/replacement_reviews/pilot_2026-10-10.json`, with official URLs, publication dates, review date, explicit unknowns and a pinned SQL snapshot hash. These are our factual transcriptions, not archived full web pages. References include retrospective reports; their later publication dates must be respected if designing a historical forecasting task.

```powershell
py scripts/audit_replacement_pilot.py
```

The script verifies the snapshot fingerprint, requires one exact reviewed local record per case and rejects repeated record links or missing evidence URLs. It writes ignored `reports/replacement_pilot/candidates.csv` and `run.json`, preserving evidence and snapshot hashes. It does not alter player data, import identities or assign a baseline. The initial run successfully linked all four cases; a repeat run preserved the candidate CSV exactly.

Next, investigate evidence for expanding the shared-standard candidate coverage before estimating replacement performance. Club-specific replacement scenarios and the position-only notebook remain separate. Propose numerical selection and estimation rules for owner review before applying them.
