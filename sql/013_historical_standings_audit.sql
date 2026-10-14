\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.historical_standings_references (
    source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    competition_id bigint NOT NULL,season_id bigint NOT NULL,club_id bigint NOT NULL,
    revision_id bigint NOT NULL,source_url text NOT NULL,source_team_label text NOT NULL,
    official_position integer NOT NULL CHECK (official_position>0),
    played integer NOT NULL CHECK (played>=0),wins integer NOT NULL CHECK (wins>=0),
    draws integer NOT NULL CHECK (draws>=0),losses integer NOT NULL CHECK (losses>=0),
    goals_for integer NOT NULL CHECK (goals_for>=0),goals_against integer NOT NULL CHECK (goals_against>=0),
    goal_difference integer NOT NULL,reported_table_points integer NOT NULL,
    CHECK (played=wins+draws+losses),CHECK (goal_difference=goals_for-goals_against),
    PRIMARY KEY (source_sha256,competition_id,season_id,club_id),
    FOREIGN KEY (competition_id,season_id,club_id)
        REFERENCES futwar.club_seasons(competition_id,season_id,club_id)
);
CREATE TABLE IF NOT EXISTS futwar.standings_points_adjudications (
    evidence_sha256 text NOT NULL CHECK (evidence_sha256 ~ '^[0-9a-f]{64}$'),
    competition_id bigint NOT NULL,season_id bigint NOT NULL,club_id bigint NOT NULL,
    reference_points integer NOT NULL,reviewed_points integer NOT NULL,points_adjustment integer NOT NULL,
    classification text NOT NULL CHECK (classification IN ('secondary_reference_error','verified_points_deduction')),
    source_urls jsonb NOT NULL CHECK (jsonb_array_length(source_urls)>0),
    note text NOT NULL,reviewed_at date NOT NULL,
    PRIMARY KEY (evidence_sha256,competition_id,season_id,club_id),
    FOREIGN KEY (competition_id,season_id,club_id)
        REFERENCES futwar.club_seasons(competition_id,season_id,club_id)
);
CREATE TEMP TABLE refs (
    source_sha256 text,league text,season text,team text,revision_id bigint,source_url text,
    source_team_label text,official_position integer,played integer,wins integer,draws integer,
    losses integer,goals_for integer,goals_against integer,goal_difference integer,official_points integer
) ON COMMIT DROP;
\copy refs FROM 'data/processed/postgres/historical_standings.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
CREATE TEMP TABLE joined_refs ON COMMIT DROP AS
SELECT r.source_sha256,c.competition_id,s.season_id,cl.club_id,r.revision_id,r.source_url,
    r.source_team_label,r.official_position,r.played,r.wins,r.draws,r.losses,r.goals_for,
    r.goals_against,r.goal_difference,r.official_points AS reported_table_points
FROM refs r JOIN futwar.competitions c ON c.competition_name=r.league
JOIN futwar.seasons s ON s.season_label=r.season
JOIN futwar.clubs cl ON cl.club_key=c.competition_code||':'||r.team;
DO $$ BEGIN
    IF (SELECT count(*) FROM refs)<>780 OR (SELECT count(*) FROM joined_refs)<>780
       OR (SELECT count(DISTINCT (competition_id,season_id,club_id)) FROM joined_refs)<>780 THEN
        RAISE EXCEPTION 'Historical reference coverage or identity join failed';
    END IF;
    IF EXISTS (SELECT 1 FROM joined_refs n JOIN futwar.historical_standings_references r
        USING (source_sha256,competition_id,season_id,club_id)
        WHERE to_jsonb(n) IS DISTINCT FROM to_jsonb(r)) THEN
        RAISE EXCEPTION 'Historical reference changed under same source hash';
    END IF;
END $$;
INSERT INTO futwar.historical_standings_references SELECT * FROM joined_refs ON CONFLICT DO NOTHING;
CREATE TEMP TABLE reviews (
    source_sha256 text,league text,season text,team text,reference_points integer,reviewed_points integer,
    points_adjustment integer,classification text,source_urls jsonb,note text,reviewed_at date
) ON COMMIT DROP;
\copy reviews FROM 'data/processed/postgres/points_adjudications.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
CREATE TEMP TABLE joined_reviews ON COMMIT DROP AS
SELECT r.source_sha256 AS evidence_sha256,c.competition_id,s.season_id,cl.club_id,
    r.reference_points,r.reviewed_points,r.points_adjustment,r.classification,
    r.source_urls,r.note,r.reviewed_at
FROM reviews r JOIN futwar.competitions c ON c.competition_name=r.league
JOIN futwar.seasons s ON s.season_label=r.season
JOIN futwar.clubs cl ON cl.club_key=c.competition_code||':'||r.team;
DO $$ BEGIN
    IF (SELECT count(*) FROM joined_reviews)<>9 OR (SELECT count(*) FROM reviews)<>9 THEN
        RAISE EXCEPTION 'Points adjudication join failed';
    END IF;
    IF EXISTS (SELECT 1 FROM joined_reviews n JOIN futwar.standings_points_adjudications r
        USING (evidence_sha256,competition_id,season_id,club_id)
        WHERE to_jsonb(n) IS DISTINCT FROM to_jsonb(r)) THEN
        RAISE EXCEPTION 'Points adjudication changed under same evidence hash';
    END IF;
END $$;
INSERT INTO futwar.standings_points_adjudications SELECT * FROM joined_reviews ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW futwar.historical_standings_comparison AS
SELECT r.source_sha256,b.league,b.season,b.team,r.official_position,
    b.played-r.played AS played_difference,b.wins-r.wins AS wins_difference,
    b.draws-r.draws AS draws_difference,b.losses-r.losses AS losses_difference,
    b.goals_for-r.goals_for AS goals_for_difference,b.goals_against-r.goals_against AS goals_against_difference,
    b.goal_difference-r.goal_difference AS goal_difference_difference,
    b.earned_match_points,r.reported_table_points,
    coalesce(a.reviewed_points,r.reported_table_points) AS reviewed_table_points,
    coalesce(a.points_adjustment,0) AS reviewed_points_adjustment,
    coalesce(a.classification,'matches_secondary_reference') AS evidence_classification,
    a.evidence_sha256,a.source_urls AS primary_evidence_urls,r.source_url,
    b.earned_match_points+coalesce(a.points_adjustment,0)-coalesce(a.reviewed_points,r.reported_table_points)
        AS unexplained_points_difference,
    a.reference_points IS NULL OR a.reference_points=r.reported_table_points AS adjudication_matches_reference
FROM futwar.historical_standings_references r
JOIN futwar.competitions c USING (competition_id) JOIN futwar.seasons s USING (season_id)
JOIN futwar.clubs cl USING (club_id)
JOIN futwar.team_results_baseline b ON b.league=c.competition_name AND b.season=s.season_label
    AND b.team=cl.display_name
LEFT JOIN futwar.standings_points_adjudications a USING (competition_id,season_id,club_id);
DO $$ BEGIN
    IF (SELECT count(*) FROM futwar.historical_standings_comparison)<>780
       OR EXISTS (SELECT 1 FROM futwar.historical_standings_comparison
           WHERE played_difference<>0 OR wins_difference<>0 OR draws_difference<>0 OR losses_difference<>0
              OR goals_for_difference<>0 OR goals_against_difference<>0 OR goal_difference_difference<>0
              OR unexplained_points_difference<>0 OR NOT adjudication_matches_reference) THEN
        RAISE EXCEPTION 'Historical comparison has missing, multiplied or unexplained results';
    END IF;
END $$;
COMMIT;
SELECT evidence_classification,count(*) AS club_seasons FROM futwar.historical_standings_comparison
GROUP BY evidence_classification ORDER BY evidence_classification;
