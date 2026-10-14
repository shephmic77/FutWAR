# First SQL exploration

This analysis describes exposure and available statistics. No WAR formula, replacement threshold, role ontology or COVID exclusion policy has been selected.

From PowerShell in the project root, regenerate SQL views and exports:

```powershell
py scripts/export_initial_eda.py
```

Outputs in ignored `reports/eda/`: 40 league-season exposure rows, 780 club-season exposure rows and 2,872 nominal-position/metric groups. The views are defined in `sql/005_exploration_views.sql`.

Open the SQL prompt:

```powershell
docker compose exec postgres psql -U futwar -d futwar
```

Then try:

```sql
SELECT league, season, player_team_records, team_labels,
       player_minutes_per_team, player_minutes_per_team_change_pct
FROM futwar.season_exposure_eda
WHERE league = 'Ligue 1'
ORDER BY season;
```

`GROUP BY` produces one summary per league and season. `LAG` compares a value with the previous season within the same league. Here the value is total recorded player minutes divided by observed club labels. It measures playing exposure, not league strength, distinct matches or data completeness. Both goalkeepers and outfield players contribute to this exposure summary.

A second query compares a single metric within the preserved nominal-position label:

```sql
SELECT league, season, nominal_position, records,
       missing_metric_records, metric_known_minutes,
       exposure_weighted_per90, median_individual_per90
FROM futwar.position_metric_eda
WHERE metric = 'npxg' AND nominal_position = 'FW'
ORDER BY league, season;
```

The weighted rate is `90 * SUM(statistic) / SUM(minutes)`, restricted to records where this statistic is known and minutes are positive. A missing statistic does not become zero, and its minutes are excluded from that metric's denominator. The median uses individual per-90 rates and answers a different question. All positive-minute records are included for this exploratory view, including tiny samples; this is not a modeling eligibility rule.

The position analysis excludes exactly `GK` and unknown position labels. Labels such as `DF,MF` and `MF,DF` remain distinct; no inferred fullback/wingback categories or primary-position remapping are applied. Player-team records can represent different clubs for the same person in the same season and must not be mistaken for unique players.

## Initial measured findings

- The season summaries account for all 22,418 processed records and 28,361,031 recorded player minutes.
- 2,988 player-team records have 90 minutes or fewer. Per-90 comparisons need visible sample size; a minimum-minute model threshold remains undecided.
- One nominal-position record remains unknown and is visible in the exposure report.
- Recorded Ligue 1 player minutes per observed club declined 26.59% in 2019-20 and rebounded 36.21% in 2020-21. These are exposure observations, not causal estimates of COVID impact.
- Ligue 1 2023-24 has 18 observed clubs rather than 20 and a 10.44% decrease in recorded player minutes per club. Changes in competition structure also require context, separately from pandemic effects.
- The eight selected candidate metrics have one missing in-scope position-group record for advanced metrics: Premier League/MF/2017-18. An additional unknown-position record is excluded from the position comparison. The metrics are exploratory candidates, not finalized model features.

## Next research step

Validate observed exposure against independently acquired domestic match results and season schedules. Record comparable team identifiers and league-season match counts before deciding whether exposure differences are genuine schedule changes or ingestion gaps. Results can later support team-strength analysis and connect to European competitions, while lineups/events will be needed for richer tactical context. Only then discuss COVID exclusion or adjustment choices. All eight seasons currently remain included.

## Independent historical context

A [French Council of State account](https://conseil-etat.fr/site/actualites/ligue-1-de-football-le-juge-des-referes-du-conseil-d-etat-valide-la-fin-de-la-saison-et-le-classement-mais-suspend-les-relegations) records the LFP decision to end the 2019-20 season on April 30 because of COVID-19. This provides real schedule context for the observed exposure drop, but does not independently verify every player row or justify automatically removing the season. Match-result coverage is still the next quantitative cross-check.

Validation: the exposure report accounts for all 22,418 database records, and metric-specific known minutes never exceed group minutes. An independent calculation from the processed CSV agrees with the SQL Premier League/MF/2017-18 weighted npxG per 90.

## Enrichment update

The initial unknown-position and missingness findings above describe the pre-enrichment snapshot. Later local research recorded source-cited position and exposure decisions in a separate correction layer; those row-level records are not included in the public repository. No exposure correction or season exclusion has been made in the SQL exploration described here.
