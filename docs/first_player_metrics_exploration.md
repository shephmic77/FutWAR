# First player-metrics exploration

The project owner selected attacking, progression and defensive distributions by position, focusing on records with at least 900 minutes and reporting excluded records. This is an exploratory display choice, not a model eligibility rule. All five leagues and all eight seasons remain included.

## Reading the notebook

Source: `notebooks/01_player_metrics_exploration.ipynb`. Executed local copy: `reports/exploration/01_player_metrics_exploration.executed.ipynb`. The source stays free of outputs; generated tables, charts, snapshots and the executed copy are ignored by Git.

Each row represents a player at one club in one season. A player who transferred can have multiple rows. The 900-minute filter applies to each club stint; it does not combine identities or minutes across clubs.

The snapshot contains 22,418 records. The displays include 11,889 outfield records and exclude 10,529: 8,871 outfield records below 900 minutes and 1,658 goalkeeper records. Exclusions are also counted separately for every league and season. None of the eligible records is missing the eight selected metrics; this does not establish completeness or accuracy of every source column.

The notebook retains all nine observed outfield position labels, including the order of mixed labels such as `DF,MF` and `MF,DF`. They describe nominal positions, not verified tactical roles. Some league-season-position combinations have no eligible records; the corresponding eight metric summaries show zero records and missing rates, rather than invented values. Six such combinations produce 48 empty metric-summary rows.

## What the charts measure

Individual rates are calculated as `90 × source total / minutes`. Boxplots show these individual rates, including outliers. The season trends use `90 × sum(known metric totals) / sum(minutes for those same records)`. Missing metric values do not become zero and their minutes do not enter that metric's denominator.

The eight measures are non-penalty goals, non-penalty expected goals, expected assists, expected assisted goals, progressive passes, progressive carries, tackles and interceptions. xA and xAG remain separate. Exact historical provider definitions still need confirmation; the field mappings are recorded in [the data dictionary](data_dictionary.md).

The boxplots pool leagues and seasons. The trend charts separate leagues and seasons for the pure DF, MF and FW labels. Differences can reflect team possession, opponents, tactical responsibilities and changing cohorts; these displays do not establish player value or absolute league strength.

For illustration, pooled individual medians among eligible records are:

| Nominal position | Records | npxG per 90 | Progressive passes per 90 | Tackles per 90 |
|---|---:|---:|---:|---:|
| DF | 4,415 | 0.038 | 3.414 | 1.632 |
| MF | 2,741 | 0.068 | 4.963 | 2.035 |
| FW | 1,535 | 0.329 | 1.879 | 0.688 |

These differences provide a reason to investigate positional context before building a shared contribution score. They do not determine weights or replacement levels.

## Schedule and COVID context

A separate chart uses all player records, including goalkeepers, to compare season volume with exposure per completed team-game. Ligue 1's player minutes per club fall from 37,474.45 in 2018-19 to 27,509.15 in 2019-20, while minutes per completed team-game remain close to 986 in both seasons. This distinguishes lower season volume from a large change in recorded exposure per game. It does not measure all pandemic effects or settle whether to exclude or contextualize those seasons.

## Reproduce in Windows PowerShell

Run from the FutWAR project folder. Open Docker Desktop first if refreshing the SQL snapshot.

```powershell
docker compose up -d --wait
py scripts/export_exploration_inputs.py
py scripts/execute_exploration_notebook.py
```

The runner executes the notebook with the same Python interpreter. Dependencies are listed in `requirements-exploration.txt`; they were already available on this machine. With an existing snapshot, Docker is unnecessary for notebook execution. Snapshot hashes are checked before analysis.

Generated outputs in `reports/exploration/` include eligibility counts, 2,880 league-season-position-metric summaries, exposure context, five charts and run metadata. The initial notebook executed all seven code cells without errors. The full test suite passed 39 tests, including checks for missing-value denominators, zero preservation and the 900-minute boundary.

## Decisions still open

Review the plots together before deciding whether to combine mixed position labels, compare other minute cutoffs, choose model inputs, or set contribution weights and replacement baselines. COVID treatment, cross-league comparability and tactical role definitions also remain open. No WAR formula has been applied.
