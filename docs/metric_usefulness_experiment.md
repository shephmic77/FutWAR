# Metric usefulness diagnostic

The owner selected metric overlap, team opportunity and contributions beyond
goals/assists as the next experiment. This follows the earlier two analysis tracks
and does not adopt a contribution model or replacement baseline.

`notebooks/05_metric_usefulness.ipynb` and
`scripts/research_metric_usefulness.py` use the existing fingerprinted player and
keeper cohorts: 11,889 outfield and 959 keeper stints with 900+ reported minutes.
This is an exploratory display focus, not a model or replacement eligibility rule.
Original data and earlier notebooks remain unchanged.

## Decisions and limits

- Use only specific profile codes for provisional diagnostic strata. DM/AM map to
  CDM/CAM and CF/SS to ST under the site's approved display vocabulary. These
  mappings do not establish historical main positions or satisfy minute-based role
  validation. 719 included outfield records have no specific profile role and are
  counted outside role-stratified correlations. Future/current profile information
  must not be used as verified historical input in chronological model evaluation.
- Verify original record IDs against name, team, league and season before attaching
  context. Keeper context reuses existing audited candidate overlay keys; this is
  not independent identity verification. No new fuzzy matching occurs.
- Keep league, season, role and provider source separate in correlations. Each pair
  retains sample size; three pairs only makes correlation computable. No confidence
  or significance claim follows. Same-provider players and repeated seasons remain
  dependent observations.
- Team-context correlations count each club once per role/source cell. Compatible
  rates use minutes-weighted eligible-stint aggregates, with paired clubs and
  metric-specific exposure exported. Keeper cross-stopping shares are omitted from
  this aggregate because their denominator should be crosses, not minutes.
- Goals for/against per match are outcomes, not direct defensive opportunity
  denominators. They include periods when an individual was absent; team results
  and player actions can affect one another. No possession adjustment, causal
  effect, league adjustment or player importance is estimated.
- Retain keeper arithmetic masks and omit warned older-source PSxG fills only from
  PSxG correlations. Source/version uncertainty remains; other metrics stay
  available. Aggregates retain counts of diagnostic/exposure/PSxG warning records.
- Add blocks, recoveries, aerial duels won/lost, key passes, progressive receptions,
  passes into the box, dispossessions, miscontrols and recorded errors from the
  unchanged original CSV. Recompute rates from counts; blanks remain missing and
  negative counts fail validation. Source field mappings and coverage are exported.
  Availability does not independently verify provider definitions or completeness.

## Findings from the first run

Premier League 2024–25 examples: goals versus non-penalty goals among ST profile
proxies have Spearman 0.930 (32 paired records); xA versus xAG among CM proxies
0.816 (34); keeper saves versus shots on target faced 0.921 (26). Tackles versus
interceptions among CB proxies have 0.231 (62). These indicate overlap patterns,
not the importance of any feature. Saves are partly contained in shots faced, so
their association is partly mechanical.

Using each club once, keeper saves/90 versus team goals conceded/match correlate
0.448 across 20 clubs; CB tackle/interception rates correlate 0.036/0.096. This
one-cell result cannot establish that defending is independent of opportunity.
Direct possession, opponent activity, shot difficulty and player-on-pitch evidence
remain the stronger next research need. Weak correlation is not proof of value.

All results, coverage, paired counts and provenance are in
`reports/metric_usefulness/`. No composite score, weights or WAR formula exist.

## Reproduce in PowerShell

```powershell
py scripts/research_metric_usefulness.py
py scripts/execute_exploration_notebook.py --notebook 05_metric_usefulness.ipynb --in-process
py -m unittest discover -s tests -p test_metric_usefulness.py
```

The seven tests cover missing/zero counts, decimal parsing, invalid counts,
pairwise missingness, small/constant samples, exposure-weighted club aggregation,
conflicting context, specific-label vocabulary and record-identity mismatches.

Next method choice remains with the owner: a bounded pilot with direct
event/opportunity evidence versus a limited season-level contribution prototype.
Either needs an explicitly chosen outcome and chronological validation before
making claims of contribution usefulness.
