-- Store reference evidence and administrative flags; never replace match scores.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.standings_reference_records (
    reference_sha256 text NOT NULL CHECK (reference_sha256 ~ '^[0-9a-f]{64}$'),
    competition_id bigint NOT NULL,
    season_id bigint NOT NULL,
    club_id bigint NOT NULL,
    source_team_label text NOT NULL,
    metrics jsonb NOT NULL CHECK (jsonb_typeof(metrics)='object'),
    source_url text NOT NULL,
    reviewed_at date NOT NULL,
    evidence_status text NOT NULL CHECK (evidence_status IN
        ('reviewed_primary_reference','provisional_season_header_conflict')),
    evidence_method text NOT NULL,
    PRIMARY KEY (reference_sha256,competition_id,season_id,club_id),
    FOREIGN KEY (competition_id,season_id,club_id)
        REFERENCES futwar.club_seasons(competition_id,season_id,club_id)
);
CREATE TABLE IF NOT EXISTS futwar.administrative_result_evidence (
    reference_sha256 text NOT NULL CHECK (reference_sha256 ~ '^[0-9a-f]{64}$'),
    match_id bigint NOT NULL REFERENCES futwar.matches(match_id),
    on_field_home_goals integer NOT NULL CHECK (on_field_home_goals>=0),
    on_field_away_goals integer NOT NULL CHECK (on_field_away_goals>=0),
    awarded_home_goals integer NOT NULL CHECK (awarded_home_goals>=0),
    awarded_away_goals integer NOT NULL CHECK (awarded_away_goals>=0),
    source_url text NOT NULL,
    corroborating_url text NOT NULL,
    reviewed_at date NOT NULL,
    note text NOT NULL,
    PRIMARY KEY (reference_sha256,match_id)
);
CREATE TEMP TABLE refs (
    source_sha256 text,league text,season text,team text,source_team_label text,
    metrics jsonb,source_url text,reviewed_at date,evidence_status text,evidence_method text
) ON COMMIT DROP;
\copy refs FROM 'data/processed/postgres/standings_references.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
CREATE TEMP TABLE joined_refs ON COMMIT DROP AS
SELECT r.*,c.competition_id,s.season_id,cl.club_id FROM refs r
JOIN futwar.competitions c ON c.competition_name=r.league
JOIN futwar.seasons s ON s.season_label=r.season
JOIN futwar.clubs cl ON cl.club_key=c.competition_code||':'||r.team;
DO $$ BEGIN
    IF (SELECT count(*) FROM joined_refs) <> (SELECT count(*) FROM refs) THEN
        RAISE EXCEPTION 'Reference club join lost or multiplied records';
    END IF;
    IF EXISTS (SELECT 1 FROM joined_refs n JOIN futwar.standings_reference_records r
        ON (r.reference_sha256,r.competition_id,r.season_id,r.club_id)=
           (n.source_sha256,n.competition_id,n.season_id,n.club_id)
        WHERE (r.metrics,r.source_url,r.evidence_status,r.source_team_label,r.reviewed_at,r.evidence_method)
            IS DISTINCT FROM (n.metrics,n.source_url,n.evidence_status,n.source_team_label,n.reviewed_at,n.evidence_method)) THEN
        RAISE EXCEPTION 'Existing reference changed under same source hash';
    END IF;
END $$;
INSERT INTO futwar.standings_reference_records
SELECT source_sha256,competition_id,season_id,club_id,source_team_label,metrics,
       source_url,reviewed_at,evidence_status,evidence_method FROM joined_refs ON CONFLICT DO NOTHING;
CREATE TEMP TABLE events (
    source_sha256 text,league text,season text,match_date date,home_team text,away_team text,
    on_field_home_goals integer,on_field_away_goals integer,
    awarded_home_goals integer,awarded_away_goals integer,
    source_url text,corroborating_url text,reviewed_at date,note text
) ON COMMIT DROP;
\copy events FROM 'data/processed/postgres/administrative_results.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
CREATE TEMP TABLE joined_events ON COMMIT DROP AS
SELECT e.*,m.match_id,m.home_goals,m.away_goals FROM events e
JOIN futwar.normalized_match_results m USING (league,season,match_date,home_team,away_team);
DO $$ BEGIN
    IF (SELECT count(*) FROM joined_events) <> (SELECT count(*) FROM events)
       OR EXISTS (SELECT 1 FROM joined_events
           WHERE (home_goals,away_goals) IS DISTINCT FROM (awarded_home_goals,awarded_away_goals)) THEN
        RAISE EXCEPTION 'Administrative result did not match its source fixture';
    END IF;
    IF EXISTS (SELECT 1 FROM joined_events n JOIN futwar.administrative_result_evidence r
        ON (n.source_sha256,n.match_id)=(r.reference_sha256,r.match_id)
        WHERE (r.on_field_home_goals,r.on_field_away_goals,r.awarded_home_goals,r.awarded_away_goals,
               r.source_url,r.corroborating_url,r.reviewed_at,r.note)
          IS DISTINCT FROM (n.on_field_home_goals,n.on_field_away_goals,n.awarded_home_goals,
               n.awarded_away_goals,n.source_url,n.corroborating_url,n.reviewed_at,n.note)) THEN
        RAISE EXCEPTION 'Existing administrative evidence changed under same hash';
    END IF;
END $$;
INSERT INTO futwar.administrative_result_evidence
SELECT source_sha256,match_id,on_field_home_goals,on_field_away_goals,
       awarded_home_goals,awarded_away_goals,source_url,corroborating_url,reviewed_at,note
FROM joined_events ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW futwar.standings_reference_comparison AS
SELECT r.reference_sha256,b.league,b.season,b.team,v.key AS metric,
       (to_jsonb(b)->>v.key)::integer AS calculated_value,v.value::integer AS reference_value,
       (to_jsonb(b)->>v.key)::integer-v.value::integer AS difference,
       r.evidence_status,r.source_url
FROM futwar.standings_reference_records r
JOIN futwar.competitions c USING (competition_id)
JOIN futwar.seasons s USING (season_id)
JOIN futwar.clubs cl USING (club_id)
JOIN futwar.team_results_baseline b ON b.league=c.competition_name
    AND b.season=s.season_label AND b.team=cl.display_name
CROSS JOIN LATERAL jsonb_each_text(r.metrics) v;
COMMIT;
SELECT evidence_status,count(*) AS checked_values,
       count(*) FILTER (WHERE difference<>0) AS differences
FROM futwar.standings_reference_comparison GROUP BY evidence_status;
