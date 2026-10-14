-- Five researched identities only; automated candidate IDs are never loaded as verified links.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.players (
    player_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    display_name text NOT NULL,date_of_birth date NOT NULL,
    identity_status text NOT NULL CHECK (identity_status='reviewed_pilot_identity')
);
CREATE TABLE IF NOT EXISTS futwar.player_source_ids (
    provider_namespace text NOT NULL,provider_player_id text NOT NULL,
    player_id bigint NOT NULL REFERENCES futwar.players(player_id),
    profile_url text NOT NULL,provider_file_sha256 text NOT NULL,
    review_sha256 text NOT NULL,source_urls jsonb NOT NULL,
    reviewed_at date NOT NULL,
    PRIMARY KEY (provider_namespace,provider_player_id)
);
CREATE TABLE IF NOT EXISTS futwar.reviewed_player_record_links (
    source_sha256 text NOT NULL,output_record integer NOT NULL,
    provider_namespace text NOT NULL,provider_player_id text NOT NULL,review_sha256 text NOT NULL,
    PRIMARY KEY (source_sha256,output_record),
    FOREIGN KEY (source_sha256,output_record) REFERENCES futwar.player_season_context(source_sha256,output_record),
    FOREIGN KEY (provider_namespace,provider_player_id)
        REFERENCES futwar.player_source_ids(provider_namespace,provider_player_id)
);
CREATE TEMP TABLE pilot_people (
    provider_namespace text,provider_player_id text,display_name text,date_of_birth date,
    profile_url text,provider_file_sha256 text,review_sha256 text,source_urls jsonb,reviewed_at date,review_status text,
    PRIMARY KEY (provider_namespace,provider_player_id)
) ON COMMIT DROP;
\copy pilot_people FROM 'data/processed/postgres/identity_pilot_players.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
CREATE TEMP TABLE pilot_links (
    source_sha256 text,output_record integer,provider_namespace text,provider_player_id text,review_sha256 text,
    PRIMARY KEY (source_sha256,output_record)
) ON COMMIT DROP;
\copy pilot_links FROM 'data/processed/postgres/identity_pilot_links.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
DO $$
DECLARE person record;new_id bigint;
BEGIN
    IF (SELECT count(*) FROM pilot_people)<>5 OR (SELECT count(*) FROM pilot_links)<>8 THEN
        RAISE EXCEPTION 'Identity pilot scope changed; review required';
    END IF;
    FOR person IN SELECT * FROM pilot_people ORDER BY provider_player_id LOOP
        SELECT player_id INTO new_id FROM futwar.player_source_ids
        WHERE provider_namespace=person.provider_namespace AND provider_player_id=person.provider_player_id;
        IF new_id IS NULL THEN
            INSERT INTO futwar.players (display_name,date_of_birth,identity_status)
            VALUES (person.display_name,person.date_of_birth,person.review_status) RETURNING player_id INTO new_id;
            INSERT INTO futwar.player_source_ids VALUES (person.provider_namespace,person.provider_player_id,new_id,
                person.profile_url,person.provider_file_sha256,person.review_sha256,person.source_urls,person.reviewed_at);
        ELSIF EXISTS (SELECT 1 FROM futwar.players p JOIN futwar.player_source_ids s USING (player_id)
            WHERE p.player_id=new_id AND (p.display_name,p.date_of_birth,s.review_sha256,s.provider_file_sha256,s.source_urls)
                IS DISTINCT FROM (person.display_name,person.date_of_birth,person.review_sha256,person.provider_file_sha256,person.source_urls)) THEN
            RAISE EXCEPTION 'Existing pilot identity or evidence changed';
        END IF;
    END LOOP;
    IF EXISTS (SELECT 1 FROM pilot_links n JOIN futwar.reviewed_player_record_links r
        USING (source_sha256,output_record) WHERE (n.provider_namespace,n.provider_player_id,n.review_sha256)
            IS DISTINCT FROM (r.provider_namespace,r.provider_player_id,r.review_sha256)) THEN
        RAISE EXCEPTION 'Existing reviewed identity link changed';
    END IF;
END $$;
INSERT INTO futwar.reviewed_player_record_links SELECT * FROM pilot_links ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW futwar.reviewed_player_seasons AS
SELECT p.player_id,p.display_name,p.date_of_birth,e.player_name AS original_player_label,
    e.league,e.season,e.team_name,e.minutes,l.source_sha256,l.output_record,
    s.provider_namespace,s.provider_player_id,l.review_sha256
FROM futwar.reviewed_player_record_links l
JOIN futwar.player_source_ids s USING (provider_namespace,provider_player_id)
JOIN futwar.players p USING (player_id)
JOIN futwar.player_season_eda e USING (source_sha256,output_record);
COMMIT;
SELECT count(*) AS pilot_players FROM futwar.players;
SELECT count(*) AS reviewed_record_links FROM futwar.reviewed_player_record_links;
