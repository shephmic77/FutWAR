\set ON_ERROR_STOP on
-- Completed scored fixtures by league-season; Ligue 1 2019-20 remains shortened.
SELECT league,season,count(*) AS scored_matches
FROM futwar.normalized_match_results GROUP BY league,season ORDER BY league,season;

-- Points earned from these results, without official deductions or tie-break rules.
SELECT league,team,played,wins,draws,losses,goals_for,goals_against,earned_match_points
FROM futwar.team_results_baseline WHERE season='2024-25'
ORDER BY league,earned_match_points DESC,team;

-- Demonstrate the context bridge without introducing a normalized player identity.
SELECT c.competition_name AS league,s.season_label AS season,
       count(*) AS player_team_records,count(DISTINCT x.club_id) AS clubs
FROM futwar.player_season_context x
JOIN futwar.competitions c USING (competition_id)
JOIN futwar.seasons s USING (season_id)
GROUP BY c.competition_name,s.season_label ORDER BY league,season;
