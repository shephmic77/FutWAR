-- Preserve the original snapshot; supplement only validated missing full-time scores.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.match_result_supplements (
    league text NOT NULL,
    season text NOT NULL,
    match_date date NOT NULL,
    home_label text NOT NULL,
    away_label text NOT NULL,
    home_goals integer NOT NULL CHECK (home_goals >= 0),
    away_goals integer NOT NULL CHECK (away_goals >= 0),
    base_source_sha256 text NOT NULL REFERENCES futwar.source_files(source_sha256),
    supplement_sha256 text NOT NULL CHECK (supplement_sha256 ~ '^[0-9a-f]{64}$'),
    source_url text NOT NULL,
    verified_on date NOT NULL,
    evidence jsonb NOT NULL,
    PRIMARY KEY (base_source_sha256, match_date, home_label, away_label),
    CHECK (home_label <> away_label)
);
CREATE TEMP TABLE import_supplements (LIKE futwar.match_result_supplements INCLUDING DEFAULTS);
\copy import_supplements FROM 'data/processed/match_results/verified_supplements.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
DO $$
BEGIN
    IF (SELECT count(*) FROM import_supplements) <> 20 THEN
        RAISE EXCEPTION 'Expected exactly 20 reviewed supplement records';
    END IF;
    IF EXISTS (SELECT 1 FROM import_supplements
        WHERE season <> '2024-25' OR league NOT IN ('La Liga', 'Serie A')) THEN
        RAISE EXCEPTION 'Supplement outside reviewed scope';
    END IF;
    IF EXISTS (SELECT 1 FROM import_supplements i JOIN futwar.match_results_stage s
        ON i.base_source_sha256=s.source_sha256 AND i.match_date=s.match_date
        AND i.home_label=s.home_label AND i.away_label=s.away_label) THEN
        RAISE EXCEPTION 'Cannot replace an existing scored snapshot result';
    END IF;
    IF EXISTS (SELECT 1 FROM import_supplements i JOIN futwar.match_result_supplements s
        ON i.base_source_sha256=s.base_source_sha256 AND i.match_date=s.match_date
        AND i.home_label=s.home_label AND i.away_label=s.away_label
        WHERE (i.home_goals,i.away_goals,i.supplement_sha256)
              IS DISTINCT FROM (s.home_goals,s.away_goals,s.supplement_sha256)) THEN
        RAISE EXCEPTION 'Conflicting supplement version requires review';
    END IF;
END $$;
INSERT INTO futwar.match_result_supplements SELECT * FROM import_supplements ON CONFLICT DO NOTHING;
DROP TABLE import_supplements;

CREATE OR REPLACE VIEW futwar.match_results_effective AS
SELECT s.*, 'openfootball_snapshot'::text AS result_origin, f.source_url AS result_source_url
FROM futwar.match_results_stage s JOIN futwar.source_files f USING (source_sha256)
WHERE f.metadata ->> 'commit' = 'e6744429ee395bc86f247348c6184bb08d4eb361'
UNION ALL
SELECT s.league,s.season,s.match_date,s.home_label,s.away_label,s.home_goals,s.away_goals,
       f.filename AS source_file,s.base_source_sha256 AS source_sha256,
       'verified_official_supplement'::text AS result_origin,s.source_url AS result_source_url
FROM futwar.match_result_supplements s JOIN futwar.source_files f
ON s.base_source_sha256=f.source_sha256
WHERE f.metadata ->> 'commit' = 'e6744429ee395bc86f247348c6184bb08d4eb361';

CREATE OR REPLACE VIEW futwar.match_team_coverage AS
WITH appearances AS (
    SELECT league,season,home_label AS club_label FROM futwar.match_results_effective
    UNION ALL
    SELECT league,season,away_label AS club_label FROM futwar.match_results_effective
), match_totals AS (
    SELECT a.league,a.season,a.club_label,m.player_label AS team_name,count(*) AS completed_results
    FROM appearances a LEFT JOIN futwar.club_label_map m
    ON a.league=m.league AND a.club_label=m.match_label
    GROUP BY a.league,a.season,a.club_label,m.player_label
), player_totals AS (
    SELECT league,season,team_name,sum(starts) AS player_starts,sum(minutes) AS player_minutes
    FROM futwar.player_season_eda GROUP BY league,season,team_name
)
SELECT m.*,p.player_starts,p.player_minutes,
       p.player_starts-11*m.completed_results AS starts_difference,
       round(100 * (p.player_minutes/(90*11*m.completed_results)-1),4) AS minutes_difference_pct
FROM match_totals m LEFT JOIN player_totals p
ON m.league=p.league AND m.season=p.season AND m.team_name=p.team_name;

DO $$
BEGIN
    IF (SELECT count(*) FROM futwar.match_results_effective) <> 14359 THEN
        RAISE EXCEPTION 'Unexpected effective match count';
    END IF;
    IF (SELECT count(*) FROM futwar.match_team_coverage) <> 780
       OR EXISTS (SELECT 1 FROM futwar.match_team_coverage WHERE starts_difference IS DISTINCT FROM 0) THEN
        RAISE EXCEPTION 'Club start coverage still differs';
    END IF;
    IF EXISTS (SELECT 1 FROM futwar.match_results_effective
        GROUP BY league,season,home_label,away_label HAVING count(*)>1) THEN
        RAISE EXCEPTION 'Duplicate directed league fixture';
    END IF;
    IF (SELECT count(*) FROM futwar.match_results_effective
        WHERE league='Ligue 1' AND season='2019-20') <> 279 THEN
        RAISE EXCEPTION 'Shortened French season must remain unchanged';
    END IF;
END $$;
COMMIT;
SELECT * FROM futwar.match_season_coverage
WHERE season='2024-25' OR difference_from_benchmark<>0 ORDER BY season,league;
