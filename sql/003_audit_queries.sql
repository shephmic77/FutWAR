-- Counts describe available records, not verified season completeness.
SELECT league, season, count(*) AS player_team_records,
       count(DISTINCT team_name) AS team_labels,
       sum(minutes) AS player_minutes,
       count(*) FILTER (WHERE nominal_position = 'GK') AS goalkeeper_records
FROM futwar.player_season_exposure
GROUP BY league, season ORDER BY league, season;

-- Review the approved correction and unresolved position flags.
SELECT * FROM futwar.player_season_exposure WHERE quality_flags <> '[]'::jsonb
  AND nominal_position IS DISTINCT FROM 'GK';

-- Examples of meaningful window functions, without estimating WAR.
SELECT league, season, team_name, player_name, minutes,
       rank() OVER (PARTITION BY league, season, team_name ORDER BY minutes DESC) AS minutes_rank,
       minutes / nullif(sum(minutes) OVER (PARTITION BY league, season, team_name), 0) AS share_of_team_player_minutes
FROM futwar.player_season_exposure;
