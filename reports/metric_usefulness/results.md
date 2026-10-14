# Metric usefulness: first diagnostic experiment

Scope: five leagues, eight seasons, 900+ reported-minute exploratory focus.
Included: 11,889 outfield and 959 keeper records; these are stints, not unique people.
Unknown specific profile roles: 719; unavailable team context: 0.
Exclusions and source hashes are retained in the companion CSVs and lineage.

## What these measurements can tell us

Overlap means two measurements often move together within a particular context.
It does not establish how useful either is for player value, or dictate weights.
Low correlation does not prove an independently valuable contribution.

Premier League 2024–25 examples; specific outfield roles are profile proxies:

| Role | Metric pair | Paired records | Spearman |
|---|---|---:|---:|
| ST | goals_per90 / non_penalty_goals_per90 | 32 | 0.930 |
| CM | xa_per90 / xag_per90 | 34 | 0.816 |
| GK | shots_on_target_against_per90 / saves_per90 | 26 | 0.921 |
| CB | tackles_per90 / interceptions_per90 | 62 | 0.231 |
| CM | progressive_passes_per90 / goals_per90 | 34 | 0.258 |

## Workload and team context

Keeper saves and shots faced use the same keeper exposure; their association
helps identify workload dependence. Saves are partly contained in shots faced,
so this association is partly mechanical, not proof of shot-stopping ability.
PSxG faced describes workload and shot difficulty, not a direct positive ability bonus.
Reported PSxG residual combines observed outcomes and model expectations; provider
definitions, arithmetic flags and unresolved model versions remain important.

The following club-level correlations use each club once within role/source,
not every teammate as independent evidence. Rates average compatible eligible
player stints with minutes as exposure. Clubs have equal weight in correlations.
Cross-stopping shares are omitted from these aggregates because they need crosses,
not minutes, as the denominator. None of these rates has been opportunity-adjusted.

| Role | Metric versus team goals conceded/match | Paired clubs | Spearman |
|---|---|---:|---:|
| CB | tackles_per90 | 20 | 0.036 |
| CB | interceptions_per90 | 20 | 0.096 |
| GK | saves_per90 | 20 | 0.448 |

Team goals conceded is an outcome-context proxy, not possession, opponent touches,
shots allowed during this player's actual minutes, or causal defensive difficulty.
These team-season figures include minutes when the player was absent. Shared
outcomes and player actions can influence each other. No team adjustment is fitted.

## Contributions beyond goals and assists

The experiment also includes original recorded blocks, recoveries, aerial duels
won/lost, key passes, progressive receptions, passes into the box, dispossessions,
miscontrols and errors. These rates are recomputed from counts and reported minutes;
coverage by every league-season is exported. Definition/version comparability is
not independently established. Recorded errors are a narrow provider category,
not a complete measure of bad decisions. Missing counts remain missing.

Progressive passes/carries, tackles/interceptions and keeper sweeping/cross stopping
describe additional recorded actions. They need location, pressure, possession
opportunity and subsequent state to establish contribution value. Avoid awarding
fixed bonuses for counts. Missing off-ball prevention is not zero contribution.
No demonstrated predictive usefulness, causal effect or incremental player value
is claimed from these descriptive correlations.

## What remains open

Specific profile labels can reflect another point in a career; they do not establish
historical main positions. Unknown roles are counted, not replaced with broad labels.
The three-pair guard only permits calculation. Small cells remain visibly small;
there are no significance claims, uncertainty intervals or selected features here.
Cells and seasons are dependent, so median cell correlations are descriptive only.
All COVID seasons remain. No WAR weights, replacement pool, league multiplier,
position bonus or final formula has been selected.

Next discussion: choose a bounded pilot with direct event/opportunity evidence,
or a clearly limited team-season prototype. Either requires held-out validation
before calling any measure useful for contribution estimation.
