-- Private context layer: original measurements and analysis views stay unchanged.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.explorer_player_context (
    source_sha256 text NOT NULL,
    output_record integer NOT NULL,
    context_source_sha256 text NOT NULL,
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload)='object'),
    loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_sha256,output_record,context_source_sha256),
    FOREIGN KEY (source_sha256,output_record) REFERENCES futwar.player_season_stage(source_sha256,output_record)
);
CREATE TEMP TABLE explorer_context_import (
    source_sha256 text,output_record integer,context_source_sha256 text,payload jsonb
) ON COMMIT DROP;
\copy explorer_context_import FROM '/workspace/data/processed/postgres/player_season_context.csv' WITH (FORMAT csv,HEADER true,ENCODING 'UTF8')
INSERT INTO futwar.explorer_player_context (source_sha256,output_record,context_source_sha256,payload)
SELECT source_sha256,output_record,context_source_sha256,payload FROM explorer_context_import
ON CONFLICT DO NOTHING;
CREATE OR REPLACE VIEW futwar.explorer_player_market_context AS
SELECT c.source_sha256,c.output_record,c.context_source_sha256,
       s.payload->>'league' AS league,s.payload->>'season' AS season,
       s.payload->>'player' AS player_name,s.payload->>'team' AS team_name,
       c.payload->>'profile_provider_player_id' AS candidate_provider_player_id,
       c.payload->>'profile_identity_status' AS profile_identity_status,
       c.payload->>'profile_position' AS profile_position,
       NULLIF(c.payload->>'height_cm','')::numeric AS height_cm,
       NULLIF(c.payload->>'market_value_eur','')::numeric AS market_value_eur,
       NULLIF(c.payload->>'market_value_date','')::date AS market_value_date,
       (c.payload->>'market_value_cutoff')::date AS market_value_cutoff,
       c.payload->>'market_value_source' AS market_value_source,
       c.payload->>'review_flags' AS review_flags
FROM futwar.explorer_player_context c
JOIN futwar.player_season_stage s USING (source_sha256,output_record);
COMMIT;
