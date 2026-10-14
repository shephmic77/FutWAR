-- Fixed-snapshot integration checks. Fail loudly if scope or mappings drift.
\set ON_ERROR_STOP on
BEGIN;
DO $$
BEGIN
    IF (SELECT count(*) FROM futwar.competitions) <> 5
       OR (SELECT count(*) FROM futwar.seasons) <> 8
       OR (SELECT count(*) FROM futwar.competition_seasons) <> 40
       OR (SELECT count(*) FROM futwar.clubs) <> 149
       OR (SELECT count(*) FROM futwar.club_seasons) <> 780
       OR (SELECT count(*) FROM futwar.matches) <> 14359
       OR (SELECT count(*) FROM futwar.match_results) <> 14359
       OR (SELECT count(*) FROM futwar.match_source_records) <> 14359
       OR (SELECT count(*) FROM futwar.player_season_context) <> 22418 THEN
        RAISE EXCEPTION 'Normalized counts differ from audited snapshot';
    END IF;
    IF EXISTS (
        SELECT 1 FROM futwar.club_label_map a
        LEFT JOIN futwar.competitions c ON c.competition_name=a.league
        LEFT JOIN futwar.club_source_aliases x ON x.competition_id=c.competition_id
            AND x.source_namespace='openfootball' AND x.source_label=a.match_label
        LEFT JOIN futwar.clubs cl ON cl.club_id=x.club_id
        WHERE cl.club_key IS DISTINCT FROM c.competition_code||':'||a.player_label
    ) THEN RAISE EXCEPTION 'Alias mapping differs from reviewed club map'; END IF;
    IF EXISTS (
        SELECT 1 FROM futwar.player_season_eda p
        LEFT JOIN futwar.player_season_context x USING (source_sha256,output_record)
        LEFT JOIN futwar.competitions c ON c.competition_id=x.competition_id
        LEFT JOIN futwar.seasons s ON s.season_id=x.season_id
        LEFT JOIN futwar.clubs cl ON cl.club_id=x.club_id
        WHERE c.competition_name IS DISTINCT FROM p.league
           OR s.season_label IS DISTINCT FROM p.season
           OR cl.club_key IS DISTINCT FROM c.competition_code||':'||p.team_name
    ) THEN RAISE EXCEPTION 'Player context dropped or changed source labels'; END IF;
    -- Compare in both directions, including original labels, scores and provenance.
    IF EXISTS (
        (SELECT league,season,match_date,home_label,away_label,home_goals,away_goals,
                source_sha256,result_origin,result_source_url
         FROM futwar.match_results_effective
         EXCEPT ALL
         SELECT c.competition_name,s.season_label,m.match_date,p.source_home_label,
                p.source_away_label,r.home_goals,r.away_goals,p.base_source_sha256,
                p.result_origin,p.result_source_url
         FROM futwar.matches m JOIN futwar.competitions c USING (competition_id)
         JOIN futwar.seasons s USING (season_id)
         JOIN futwar.match_results r USING (match_id)
         JOIN futwar.match_source_records p USING (match_id))
        UNION ALL
        (SELECT c.competition_name,s.season_label,m.match_date,p.source_home_label,
                p.source_away_label,r.home_goals,r.away_goals,p.base_source_sha256,
                p.result_origin,p.result_source_url
         FROM futwar.matches m JOIN futwar.competitions c USING (competition_id)
         JOIN futwar.seasons s USING (season_id)
         JOIN futwar.match_results r USING (match_id)
         JOIN futwar.match_source_records p USING (match_id)
         EXCEPT ALL
         SELECT league,season,match_date,home_label,away_label,home_goals,away_goals,
                source_sha256,result_origin,result_source_url
         FROM futwar.match_results_effective)
    ) THEN RAISE EXCEPTION 'Normalized results differ from effective source results'; END IF;
    IF EXISTS (
        SELECT 1 FROM futwar.match_source_records p
        JOIN futwar.matches m USING (match_id)
        JOIN futwar.club_source_aliases h ON h.source_namespace='openfootball'
            AND h.competition_id=m.competition_id AND h.source_label=p.source_home_label
        JOIN futwar.club_source_aliases a ON a.source_namespace='openfootball'
            AND a.competition_id=m.competition_id AND a.source_label=p.source_away_label
        LEFT JOIN futwar.match_result_supplements x ON x.base_source_sha256=p.base_source_sha256
            AND x.match_date=p.source_match_date AND x.home_label=p.source_home_label
            AND x.away_label=p.source_away_label
        WHERE h.club_id<>m.home_club_id OR a.club_id<>m.away_club_id
            OR p.source_match_date<>m.match_date
            OR (p.result_origin='verified_official_supplement'
                AND p.supplement_sha256 IS DISTINCT FROM x.supplement_sha256)
    ) THEN RAISE EXCEPTION 'Club orientation or supplement lineage changed'; END IF;
    IF (SELECT count(*) FROM futwar.team_results_baseline) <> 780
       OR (SELECT sum(played) FROM futwar.team_results_baseline) <> 2*14359
       OR EXISTS (SELECT 1 FROM futwar.team_results_baseline
                  WHERE played<>wins+draws+losses OR earned_match_points<>3*wins+draws)
       OR (SELECT sum(goals_for)-sum(goals_against) FROM futwar.team_results_baseline) <> 0 THEN
        RAISE EXCEPTION 'Team result accounting failed';
    END IF;
END $$;
-- Rejected writes roll back inside each exception block; no test rows persist.
DO $$
DECLARE sample futwar.matches%ROWTYPE;
BEGIN
    SELECT * INTO sample FROM futwar.matches ORDER BY match_id LIMIT 1;
    BEGIN
        UPDATE futwar.match_results SET home_goals=-1 WHERE match_id=sample.match_id;
        RAISE EXCEPTION 'Negative score was accepted';
    EXCEPTION WHEN check_violation THEN NULL; END;
    BEGIN
        UPDATE futwar.matches SET away_club_id=home_club_id WHERE match_id=sample.match_id;
        RAISE EXCEPTION 'Club playing itself was accepted';
    EXCEPTION WHEN check_violation THEN NULL; END;
    BEGIN
        UPDATE futwar.matches SET home_club_id=-1 WHERE match_id=sample.match_id;
        RAISE EXCEPTION 'Unknown club-season was accepted';
    EXCEPTION WHEN foreign_key_violation THEN NULL; END;
END $$;
ROLLBACK;
SELECT 'Normalized counts, mappings, results, provenance and constraints passed' AS validation;
