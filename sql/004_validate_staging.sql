-- Fixed-source staging validation; fail loudly if the approved import differs.
\set ON_ERROR_STOP on
DO $$
DECLARE row_count integer; refs integer; groups_count integer;
BEGIN
    SELECT count(*), sum(jsonb_array_length(source_record_numbers))
    INTO row_count, refs FROM futwar.player_season_stage;
    IF row_count <> 22418 OR refs <> 22929 THEN
        RAISE EXCEPTION 'Unexpected staging size or source lineage: %, %', row_count, refs;
    END IF;
    SELECT count(*) INTO groups_count FROM
        (SELECT DISTINCT league, season FROM futwar.player_season_exposure) AS groups;
    IF groups_count <> 40 THEN RAISE EXCEPTION 'Expected 40 observed league-season groups'; END IF;
    IF EXISTS (SELECT 1 FROM futwar.player_season_exposure
        GROUP BY league, season, team_name, player_name HAVING count(*) > 1) THEN
        RAISE EXCEPTION 'Duplicate name key remains';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM futwar.player_season_stage
        WHERE payload ->> 'player' = 'Emanuele Torrasi'
        AND payload ->> 'team' = 'Milan' AND payload ->> 'season' = '2017-18'
        AND payload ->> 'Playing Time_Min' = '6'
        AND payload -> 'Subs_unSub' = 'null'::jsonb
        AND jsonb_array_length(source_record_numbers) = 512) THEN
        RAISE EXCEPTION 'Approved correction or lineage is absent';
    END IF;
END $$;
SELECT count(*) AS processed_records, count(DISTINCT league) AS leagues,
       count(DISTINCT season) AS seasons FROM futwar.player_season_exposure;
SELECT league, season, count(*) AS player_team_records
FROM futwar.player_season_exposure GROUP BY league, season ORDER BY league, season;
