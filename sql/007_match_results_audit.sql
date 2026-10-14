-- Audited candidate match results; no final player identity or WAR model.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.match_results_stage (
    league text NOT NULL,
    season text NOT NULL,
    match_date date NOT NULL,
    home_label text NOT NULL,
    away_label text NOT NULL,
    home_goals integer NOT NULL CHECK (home_goals >= 0),
    away_goals integer NOT NULL CHECK (away_goals >= 0),
    source_file text NOT NULL,
    source_sha256 text NOT NULL REFERENCES futwar.source_files(source_sha256),
    CHECK (home_label <> away_label),
    PRIMARY KEY (source_sha256, match_date, home_label, away_label)
);
CREATE TABLE IF NOT EXISTS futwar.club_label_map (
    league text NOT NULL,
    match_label text NOT NULL,
    player_label text NOT NULL,
    PRIMARY KEY (league, match_label)
);
CREATE TEMP TABLE import_match_sources (LIKE futwar.source_files INCLUDING DEFAULTS);
CREATE TEMP TABLE import_results (LIKE futwar.match_results_stage INCLUDING DEFAULTS);
CREATE TEMP TABLE import_clubs (LIKE futwar.club_label_map INCLUDING DEFAULTS);
\copy import_match_sources FROM 'data/processed/match_results/source_files.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy import_results FROM 'data/processed/match_results/openfootball_results.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy import_clubs FROM 'data/processed/match_results/club_labels.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
INSERT INTO futwar.source_files SELECT * FROM import_match_sources ON CONFLICT DO NOTHING;
INSERT INTO futwar.match_results_stage SELECT * FROM import_results ON CONFLICT DO NOTHING;
INSERT INTO futwar.club_label_map SELECT * FROM import_clubs ON CONFLICT DO NOTHING;
DROP TABLE import_results;
DROP TABLE import_match_sources;
DROP TABLE import_clubs;
COMMIT;

CREATE OR REPLACE VIEW futwar.match_team_coverage AS
WITH appearances AS (
    SELECT league,season,home_label AS club_label FROM futwar.match_results_stage
    WHERE source_sha256 IN (SELECT source_sha256 FROM futwar.source_files
        WHERE metadata ->> 'commit' = 'e6744429ee395bc86f247348c6184bb08d4eb361')
    UNION ALL
    SELECT league,season,away_label AS club_label FROM futwar.match_results_stage
    WHERE source_sha256 IN (SELECT source_sha256 FROM futwar.source_files
        WHERE metadata ->> 'commit' = 'e6744429ee395bc86f247348c6184bb08d4eb361')
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

CREATE OR REPLACE VIEW futwar.match_season_coverage AS
SELECT league,season,sum(completed_results)/2 AS completed_matches,
       count(*) AS club_labels,count(*)*(count(*)-1) AS double_round_robin_benchmark,
       sum(completed_results)/2-count(*)*(count(*)-1) AS difference_from_benchmark,
       count(*) FILTER (WHERE starts_difference IS DISTINCT FROM 0) AS clubs_with_start_discrepancy
FROM futwar.match_team_coverage GROUP BY league,season;

SELECT * FROM futwar.match_season_coverage
WHERE difference_from_benchmark <> 0 ORDER BY season,league;
