-- Normalize the audited snapshot without changing source or model decisions.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.competitions (
    competition_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    competition_code text NOT NULL UNIQUE,
    competition_name text NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS futwar.seasons (
    season_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    season_label text NOT NULL UNIQUE,
    start_year integer NOT NULL,
    end_year integer NOT NULL,
    CHECK (end_year = start_year + 1),
    UNIQUE (start_year, end_year)
);
CREATE TABLE IF NOT EXISTS futwar.competition_seasons (
    competition_id bigint NOT NULL REFERENCES futwar.competitions(competition_id),
    season_id bigint NOT NULL REFERENCES futwar.seasons(season_id),
    PRIMARY KEY (competition_id, season_id)
);
CREATE TABLE IF NOT EXISTS futwar.clubs (
    club_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    club_key text NOT NULL UNIQUE,
    display_name text NOT NULL,
    identity_namespace text NOT NULL,
    identity_status text NOT NULL DEFAULT 'provisional_source_label',
    CHECK (identity_status IN ('provisional_source_label', 'externally_reconciled'))
);
CREATE TABLE IF NOT EXISTS futwar.club_source_aliases (
    source_namespace text NOT NULL,
    competition_id bigint NOT NULL REFERENCES futwar.competitions(competition_id),
    source_label text NOT NULL,
    club_id bigint NOT NULL REFERENCES futwar.clubs(club_id),
    PRIMARY KEY (source_namespace, competition_id, source_label)
);
CREATE TABLE IF NOT EXISTS futwar.club_seasons (
    competition_id bigint NOT NULL,
    season_id bigint NOT NULL,
    club_id bigint NOT NULL REFERENCES futwar.clubs(club_id),
    PRIMARY KEY (competition_id, season_id, club_id),
    FOREIGN KEY (competition_id, season_id)
        REFERENCES futwar.competition_seasons(competition_id, season_id)
);
CREATE TABLE IF NOT EXISTS futwar.matches (
    match_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    competition_id bigint NOT NULL,
    season_id bigint NOT NULL,
    match_date date NOT NULL,
    home_club_id bigint NOT NULL,
    away_club_id bigint NOT NULL,
    CHECK (home_club_id <> away_club_id),
    UNIQUE (competition_id, season_id, match_date, home_club_id, away_club_id),
    FOREIGN KEY (competition_id, season_id, home_club_id)
        REFERENCES futwar.club_seasons(competition_id, season_id, club_id),
    FOREIGN KEY (competition_id, season_id, away_club_id)
        REFERENCES futwar.club_seasons(competition_id, season_id, club_id)
);
CREATE TABLE IF NOT EXISTS futwar.match_results (
    match_id bigint PRIMARY KEY REFERENCES futwar.matches(match_id),
    home_goals integer NOT NULL CHECK (home_goals >= 0),
    away_goals integer NOT NULL CHECK (away_goals >= 0)
);
CREATE TABLE IF NOT EXISTS futwar.match_source_records (
    match_id bigint NOT NULL REFERENCES futwar.matches(match_id),
    base_source_sha256 text NOT NULL REFERENCES futwar.source_files(source_sha256),
    source_match_date date NOT NULL,
    source_home_label text NOT NULL,
    source_away_label text NOT NULL,
    result_origin text NOT NULL,
    result_source_url text NOT NULL,
    supplement_sha256 text,
    PRIMARY KEY (match_id, base_source_sha256, result_origin),
    CHECK ((result_origin = 'openfootball_snapshot' AND supplement_sha256 IS NULL)
        OR (result_origin = 'verified_official_supplement' AND supplement_sha256 IS NOT NULL))
);
CREATE TABLE IF NOT EXISTS futwar.player_season_context (
    source_sha256 text NOT NULL,
    output_record integer NOT NULL,
    competition_id bigint NOT NULL,
    season_id bigint NOT NULL,
    club_id bigint NOT NULL,
    PRIMARY KEY (source_sha256, output_record),
    FOREIGN KEY (source_sha256, output_record)
        REFERENCES futwar.player_season_stage(source_sha256, output_record),
    FOREIGN KEY (competition_id, season_id, club_id)
        REFERENCES futwar.club_seasons(competition_id, season_id, club_id)
);

INSERT INTO futwar.competitions (competition_code, competition_name) VALUES
    ('eng-premier-league','Premier League'),('esp-la-liga','La Liga'),
    ('ita-serie-a','Serie A'),('ger-bundesliga','Bundesliga'),('fra-ligue-1','Ligue 1')
ON CONFLICT DO NOTHING;
INSERT INTO futwar.seasons (season_label,start_year,end_year)
SELECT DISTINCT season, left(season,4)::integer,left(season,4)::integer+1
FROM futwar.match_results_effective ORDER BY season ON CONFLICT DO NOTHING;
INSERT INTO futwar.competition_seasons
SELECT DISTINCT c.competition_id,s.season_id FROM futwar.match_results_effective e
JOIN futwar.competitions c ON c.competition_name=e.league
JOIN futwar.seasons s ON s.season_label=e.season ON CONFLICT DO NOTHING;

-- These explicit competition-qualified labels are local, provisional club identities.
INSERT INTO futwar.clubs (club_key,display_name,identity_namespace)
SELECT DISTINCT c.competition_code||':'||p.team_name,p.team_name,'user_fbref_archive:'||c.competition_code
FROM futwar.player_season_eda p JOIN futwar.competitions c ON c.competition_name=p.league
ORDER BY 1 ON CONFLICT DO NOTHING;
INSERT INTO futwar.club_source_aliases
SELECT DISTINCT 'user_fbref_archive',c.competition_id,p.team_name,cl.club_id
FROM futwar.player_season_eda p JOIN futwar.competitions c ON c.competition_name=p.league
JOIN futwar.clubs cl ON cl.club_key=c.competition_code||':'||p.team_name ON CONFLICT DO NOTHING;
INSERT INTO futwar.club_source_aliases
SELECT 'openfootball',c.competition_id,a.match_label,cl.club_id
FROM futwar.club_label_map a JOIN futwar.competitions c ON c.competition_name=a.league
JOIN futwar.clubs cl ON cl.club_key=c.competition_code||':'||a.player_label ON CONFLICT DO NOTHING;
INSERT INTO futwar.club_seasons
SELECT DISTINCT c.competition_id,s.season_id,a.club_id
FROM futwar.player_season_eda p JOIN futwar.competitions c ON c.competition_name=p.league
JOIN futwar.seasons s ON s.season_label=p.season
JOIN futwar.club_source_aliases a ON a.competition_id=c.competition_id
    AND a.source_namespace='user_fbref_archive' AND a.source_label=p.team_name ON CONFLICT DO NOTHING;

CREATE TEMP TABLE normalized_matches AS
SELECT e.*,c.competition_id,s.season_id,h.club_id AS home_club_id,a.club_id AS away_club_id
FROM futwar.match_results_effective e
JOIN futwar.competitions c ON c.competition_name=e.league
JOIN futwar.seasons s ON s.season_label=e.season
JOIN futwar.club_source_aliases h ON h.competition_id=c.competition_id
    AND h.source_namespace='openfootball' AND h.source_label=e.home_label
JOIN futwar.club_source_aliases a ON a.competition_id=c.competition_id
    AND a.source_namespace='openfootball' AND a.source_label=e.away_label;
DO $$
BEGIN
    IF (SELECT count(*) FROM normalized_matches) <> (SELECT count(*) FROM futwar.match_results_effective) THEN
        RAISE EXCEPTION 'Unmatched or multiplied source match joins';
    END IF;
END $$;
INSERT INTO futwar.matches (competition_id,season_id,match_date,home_club_id,away_club_id)
SELECT competition_id,season_id,match_date,home_club_id,away_club_id FROM normalized_matches
ORDER BY competition_id,season_id,match_date,home_club_id,away_club_id ON CONFLICT DO NOTHING;
CREATE TEMP TABLE normalized_match_ids AS
SELECT n.*,m.match_id FROM normalized_matches n JOIN futwar.matches m
USING (competition_id,season_id,match_date,home_club_id,away_club_id);
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM normalized_match_ids n JOIN futwar.match_results r USING (match_id)
        WHERE (n.home_goals,n.away_goals) IS DISTINCT FROM (r.home_goals,r.away_goals)) THEN
        RAISE EXCEPTION 'Normalized score conflicts with existing result; review required';
    END IF;
    IF EXISTS (SELECT 1 FROM normalized_match_ids n JOIN futwar.match_source_records r
        ON n.match_id=r.match_id AND n.source_sha256=r.base_source_sha256 AND n.result_origin=r.result_origin
        WHERE n.result_source_url IS DISTINCT FROM r.result_source_url) THEN
        RAISE EXCEPTION 'Existing match provenance changed; review required';
    END IF;
END $$;
INSERT INTO futwar.match_results SELECT match_id,home_goals,away_goals FROM normalized_match_ids ON CONFLICT DO NOTHING;
INSERT INTO futwar.match_source_records
SELECT n.match_id,n.source_sha256,n.match_date,n.home_label,n.away_label,
       n.result_origin,n.result_source_url,x.supplement_sha256
FROM normalized_match_ids n LEFT JOIN futwar.match_result_supplements x
ON n.result_origin='verified_official_supplement' AND x.base_source_sha256=n.source_sha256
AND x.match_date=n.match_date AND x.home_label=n.home_label AND x.away_label=n.away_label ON CONFLICT DO NOTHING;
INSERT INTO futwar.player_season_context
SELECT p.source_sha256,p.output_record,c.competition_id,s.season_id,a.club_id
FROM futwar.player_season_eda p JOIN futwar.competitions c ON c.competition_name=p.league
JOIN futwar.seasons s ON s.season_label=p.season
JOIN futwar.club_source_aliases a ON a.competition_id=c.competition_id
AND a.source_namespace='user_fbref_archive' AND a.source_label=p.team_name ON CONFLICT DO NOTHING;
DROP TABLE normalized_match_ids;
DROP TABLE normalized_matches;

CREATE OR REPLACE VIEW futwar.normalized_match_results AS
SELECT m.match_id,c.competition_name AS league,s.season_label AS season,m.match_date,
       h.display_name AS home_team,a.display_name AS away_team,r.home_goals,r.away_goals,
       p.result_origin,p.result_source_url,p.base_source_sha256,p.supplement_sha256
FROM futwar.matches m JOIN futwar.competitions c USING (competition_id)
JOIN futwar.seasons s USING (season_id)
JOIN futwar.clubs h ON h.club_id=m.home_club_id JOIN futwar.clubs a ON a.club_id=m.away_club_id
JOIN futwar.match_results r USING (match_id) JOIN futwar.match_source_records p USING (match_id);

-- Results-derived points, not official standings, tie-break rules or league-strength ratings.
CREATE OR REPLACE VIEW futwar.team_results_baseline AS
WITH sides AS (
    SELECT m.competition_id,m.season_id,m.home_club_id AS club_id,
           r.home_goals AS goals_for,r.away_goals AS goals_against
    FROM futwar.matches m JOIN futwar.match_results r USING (match_id)
    UNION ALL
    SELECT m.competition_id,m.season_id,m.away_club_id AS club_id,
           r.away_goals,r.home_goals FROM futwar.matches m JOIN futwar.match_results r USING (match_id)
)
SELECT c.competition_name AS league,s.season_label AS season,cl.display_name AS team,
       count(*) AS played,count(*) FILTER (WHERE goals_for>goals_against) AS wins,
       count(*) FILTER (WHERE goals_for=goals_against) AS draws,
       count(*) FILTER (WHERE goals_for<goals_against) AS losses,
       sum(goals_for) AS goals_for,sum(goals_against) AS goals_against,
       sum(goals_for-goals_against) AS goal_difference,
       sum(CASE WHEN goals_for>goals_against THEN 3 WHEN goals_for=goals_against THEN 1 ELSE 0 END)
           AS earned_match_points
FROM sides JOIN futwar.competitions c USING (competition_id) JOIN futwar.seasons s USING (season_id)
JOIN futwar.clubs cl USING (club_id) GROUP BY c.competition_name,s.season_label,cl.display_name;

COMMIT;
SELECT 'competitions' AS table_name,count(*) AS records FROM futwar.competitions
UNION ALL SELECT 'seasons',count(*) FROM futwar.seasons
UNION ALL SELECT 'competition_seasons',count(*) FROM futwar.competition_seasons
UNION ALL SELECT 'clubs',count(*) FROM futwar.clubs
UNION ALL SELECT 'club_seasons',count(*) FROM futwar.club_seasons
UNION ALL SELECT 'matches',count(*) FROM futwar.matches
UNION ALL SELECT 'match_results',count(*) FROM futwar.match_results
UNION ALL SELECT 'match_source_records',count(*) FROM futwar.match_source_records
UNION ALL SELECT 'player_season_context',count(*) FROM futwar.player_season_context;
