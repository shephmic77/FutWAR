-- Initial staging preserves provider columns without declaring a final research model.
CREATE SCHEMA IF NOT EXISTS futwar;
CREATE TABLE IF NOT EXISTS futwar.source_files (
    source_sha256 text PRIMARY KEY CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    filename text NOT NULL,
    source_url text,
    metadata jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS futwar.player_season_stage (
    source_sha256 text NOT NULL REFERENCES futwar.source_files(source_sha256),
    output_record integer NOT NULL CHECK (output_record > 0),
    source_record_numbers jsonb NOT NULL CHECK (jsonb_typeof(source_record_numbers) = 'array'),
    quality_flags jsonb NOT NULL CHECK (jsonb_typeof(quality_flags) = 'array'),
    payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    PRIMARY KEY (source_sha256, output_record)
);
-- Names remain labels, not finalized cross-provider identifiers.
CREATE OR REPLACE VIEW futwar.player_season_exposure AS
SELECT source_sha256, output_record,
       payload ->> 'league' AS league,
       payload ->> 'season' AS season,
       payload ->> 'team' AS team_name,
       payload ->> 'player' AS player_name,
       payload ->> 'pos_' AS nominal_position,
       (payload ->> 'Playing Time_Min')::numeric AS minutes,
       quality_flags
FROM futwar.player_season_stage;
