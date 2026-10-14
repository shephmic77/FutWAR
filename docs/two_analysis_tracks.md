# Two player-analysis tracks, including goalkeepers

Owner direction, 2026-10-10: GK belongs alongside outfield players in both the position-specific analysis and the broader player-value research. The keeper domain notebook is supporting detail, not a separate final project. Existing notebooks and research goals are preserved.

## 1. Analysis by position

Subsequent owner direction: final standard analysis groups each player-season under one supported main position. Additional positions and broader injury/transfer/team context are intended for an [interactive player profile](player_profile_direction.md). The current exploratory source labels remain unchanged until specific positions are established.

`notebooks/03_all_positions_exploration.ipynb` is the shared entry point. It includes 11,889 outfield player-club-season records and 959 GK records, using the previously approved 900+ reported-minute focus with exclusions counted. These 12,848 analysis-domain records are not a count of unique people. Transfers remain separate stints; provider identities are not automatically merged.

The notebook describes metrics separately for each available nominal position, league, season and source. Goals and assists are added from the same verified cleaned original CSV records, alongside the eight existing outfield metrics. GK uses the separately audited keeper domains. The original source GK rows are excluded from the outfield cohort, so their outfield-source records do not enter this position analysis again as outfield players. Source input counts are shown separately and must not be summed as unique people.

There are nine observed outfield nominal labels plus GK. DF, MF, FW and mixed labels are provisional source descriptions. They do not satisfy the owner's desired LB/RB/CB/LWB/RWB and other specific historical roles. No nominal labels are converted to invented roles, and mixed labels do not imply verified secondary positions. The five-appearance/10% secondary-position rule remains unchanged; historical role acquisition is still required.

This track displays coverage and within-position distributions only. It has no combined rating, weights or contribution model. Existing outfield and keeper figures remain in notebooks 01 and 02 and are linked as supporting detail.

## 2. Overall player-value research

The owner-selected next diagnostic is implemented in
`notebooks/05_metric_usefulness.ipynb`: expanded recorded-action metrics, overlap
within specific profile proxy strata, and club-level team-context checks.
See [the experiment and limits](metric_usefulness_experiment.md). Profile proxies
do not replace the historical main-position evidence requirement. This adds no
score, weights or replacement rule. The source notebook executed successfully
into `reports/exploration/05_metric_usefulness.executed.ipynb` (three code cells),
and seven diagnostic regression tests passed.

`notebooks/04_player_value_metric_research.ipynb` includes the same outfield and GK cohorts. It starts with metric availability and overlap, before choosing a contribution-estimation method. Its candidate domains are attacking output/creation, progression, defensive actions, and keeper shot stopping/distribution/cross stopping/sweeping. This is the first research step toward judging contribution; it does not yet assign player value.

The target remains observed seasonal contribution above a readily available replacement-level comparator, with eventual calibration to a validated common outcome scale. Different role measurements are not directly interchangeable units of value. Position-relative percentiles would not by themselves make keeper value comparable to outfield value. League strength and tactical fit remain separate questions.

The notebook checks Spearman rank correlations within position × league × season × source, retaining pair counts. Fewer than three available pairs or constant/undefined pairs receive missing correlations. Three is a computability guard, not a reliability threshold. These descriptive associations do not select weights, determine causality or estimate player effects on points. No p-value, model performance or attribution claim is made.

Among Premier League FW records in 2024-25, goals and non-penalty goals correlate at 0.968 over 43 paired records. Among the 26 GK records in that cell, shots faced and saves per 90 correlate at 0.921. These examples highlight overlap/opportunity dependence; they do not prove a weighting rule. Goals, assists and other correlated attacking metrics should not automatically receive additive credit. Goals will not be downweighted merely to force defenders/GK into a preferred leaderboard.

Specific keeper arithmetic flags remain excluded only from the reported residual metric. Approved older-source PSxG fills remain in position descriptions with warnings and are omitted only from source-cohort PSxG correlations to avoid mixing the identified older measurements into those pairs. Other measurements remain available. All exact metric-model versions remain unconfirmed, even where no row-specific warning is present.

The existing `player_value_research.md` and `replacement_baseline_research.md` remain the methodological foundation. Before implementing a value estimator, discuss credit allocation, role comparators, replacement pools, league/opponent context, low-volume stabilization and outcome calibration. No formula, normalization scheme, outcome model, replacement threshold or COVID treatment was selected in this work.

## Execution and validation

Run from the project root in PowerShell:

```powershell
py scripts/execute_exploration_notebook.py --notebook 03_all_positions_exploration.ipynb --in-process
py scripts/execute_exploration_notebook.py --notebook 04_player_value_metric_research.ipynb --in-process
```

Both notebooks executed through the available local IPython runtime: four code cells for the position track and three for the value-research track. The clean source notebooks retain no outputs; executed copies are local under `reports/exploration/`. Reports under ignored `reports/analysis_tracks/` contain cohort accounting, position counts, per-context metric distributions, overlap checks and lineage. The original notebooks are preserved.

The helper checks the audited exploration input hashes, the exact cleaned original CSV hash, complete row/key alignment before adding goals/assists, the corrected keeper hash, unique analysis-domain record keys and source scope. All data sources remain unchanged. Tests verify GK participation in position summaries, separation of league contexts, and exclusion of older-source PSxG only from affected correlations without mutating the descriptive keeper data.
