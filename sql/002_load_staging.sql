-- Run through psql from the project root after 001_staging.sql.
\set ON_ERROR_STOP on
BEGIN;
CREATE TEMP TABLE import_source (LIKE futwar.source_files INCLUDING DEFAULTS);
CREATE TEMP TABLE import_players (LIKE futwar.player_season_stage INCLUDING DEFAULTS);
\copy import_source FROM 'data/processed/postgres/source_files.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy import_players FROM 'data/processed/postgres/player_seasons.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
INSERT INTO futwar.source_files SELECT * FROM import_source ON CONFLICT (source_sha256) DO NOTHING;
INSERT INTO futwar.player_season_stage SELECT * FROM import_players ON CONFLICT (source_sha256, output_record) DO NOTHING;
DROP TABLE import_players;
DROP TABLE import_source;
COMMIT;
-- Repeat imports of this approved fixed-source export do not add duplicate records.
