-- Exploratory views: these do not define WAR, replacement or tactical roles.
CREATE OR REPLACE VIEW futwar.player_season_eda AS
SELECT source_sha256, output_record, quality_flags,
       payload ->> 'league' AS league, payload ->> 'season' AS season,
       payload ->> 'team' AS team_name, payload ->> 'player' AS player_name,
       payload ->> 'pos_' AS nominal_position,
       (payload ->> 'Playing Time_Min')::numeric AS minutes,
       (payload ->> 'Playing Time_MP')::numeric AS appearances,
       (payload ->> 'Playing Time_Starts')::numeric AS starts,
       (payload ->> 'age_')::numeric AS age,
       (payload ->> 'Performance_G-PK')::numeric AS non_penalty_goals,
       (payload ->> 'Expected_npxG')::numeric AS npxg,
       (payload ->> 'Expected_xA')::numeric AS xa,
       (payload ->> 'Expected_xAG')::numeric AS xag,
       (payload ->> 'Progression_PrgP')::numeric AS progressive_passes,
       (payload ->> 'Progression_PrgC')::numeric AS progressive_carries,
       (payload ->> 'Tackles_Tkl')::numeric AS tackles,
       (payload ->> 'Int_')::numeric AS interceptions
FROM futwar.player_season_stage;

CREATE OR REPLACE VIEW futwar.season_exposure_eda AS
WITH totals AS (
    SELECT league, season, count(*) AS player_team_records,
           count(DISTINCT team_name) AS team_labels,
           count(*) FILTER (WHERE nominal_position = 'GK') AS goalkeeper_records,
           count(*) FILTER (WHERE nominal_position IS NULL) AS unknown_position_records,
           sum(minutes) AS all_player_minutes,
           sum(appearances) AS player_appearances,
           sum(starts) AS player_starts,
           count(*) FILTER (WHERE minutes <= 90) AS records_at_most_90_minutes,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY minutes) AS median_record_minutes,
           round(sum(minutes) / nullif(count(DISTINCT team_name), 0), 2) AS player_minutes_per_team
    FROM futwar.player_season_eda GROUP BY league, season
)
SELECT *, round(100 * (player_minutes_per_team /
           nullif(lag(player_minutes_per_team) OVER (PARTITION BY league ORDER BY season), 0) - 1), 2)
           AS player_minutes_per_team_change_pct
FROM totals;

CREATE OR REPLACE VIEW futwar.position_metric_eda AS
WITH long_metrics AS (
    SELECT p.league, p.season, p.nominal_position, p.minutes, m.metric, m.value
    FROM futwar.player_season_eda p
    CROSS JOIN LATERAL (VALUES
        ('non_penalty_goals',p.non_penalty_goals),('npxg',p.npxg),
        ('xa',p.xa),('xag',p.xag),('progressive_passes',p.progressive_passes),
        ('progressive_carries',p.progressive_carries),('tackles',p.tackles),
        ('interceptions',p.interceptions)) AS m(metric,value)
    WHERE p.nominal_position IS NOT NULL AND p.nominal_position <> 'GK'
)
SELECT league, season, nominal_position, metric, count(*) AS records,
       count(*) FILTER (WHERE value IS NULL) AS missing_metric_records,
       count(*) FILTER (WHERE value IS NOT NULL AND minutes > 0) AS rate_eligible_records,
       sum(minutes) FILTER (WHERE minutes > 0) AS group_positive_minutes,
       sum(minutes) FILTER (WHERE value IS NOT NULL AND minutes > 0) AS metric_known_minutes,
       round(100.0 * count(*) FILTER (WHERE value IS NULL) / count(*), 2) AS missing_metric_pct,
       round(90 * sum(value) FILTER (WHERE value IS NOT NULL AND minutes > 0) /
           nullif(sum(minutes) FILTER (WHERE value IS NOT NULL AND minutes > 0), 0), 4)
           AS exposure_weighted_per90,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY 90 * value / nullif(minutes,0))
           FILTER (WHERE value IS NOT NULL AND minutes > 0) AS median_individual_per90,
       count(*) FILTER (WHERE value IS NOT NULL AND minutes > 0 AND minutes <= 90)
           AS rate_eligible_records_at_most_90_minutes
FROM long_metrics GROUP BY league, season, nominal_position, metric;

CREATE OR REPLACE VIEW futwar.team_exposure_eda AS
SELECT league, season, team_name, count(*) AS player_team_records,
       sum(minutes) AS all_player_minutes,
       sum(starts) AS player_starts,
       max(appearances) AS largest_individual_appearance_count
FROM futwar.player_season_eda GROUP BY league, season, team_name;
