-- Preserve an explicit audit trail for externally sourced enrichment.
\set ON_ERROR_STOP on
BEGIN;
CREATE TABLE IF NOT EXISTS futwar.reviewed_enrichments (
    source_sha256 text NOT NULL REFERENCES futwar.source_files(source_sha256),
    output_record integer NOT NULL,
    field_name text NOT NULL,
    original_value jsonb,
    enriched_value jsonb,
    source_url text NOT NULL,
    evidence text NOT NULL,
    PRIMARY KEY (source_sha256, output_record, field_name),
    FOREIGN KEY (source_sha256, output_record)
        REFERENCES futwar.player_season_stage(source_sha256, output_record)
);
INSERT INTO futwar.reviewed_enrichments
SELECT source_sha256, output_record, 'pos_', 'null'::jsonb, '"DF"'::jsonb,
       'https://img.legaseriea.it/vimages/632c27e0/2017-18_A_UNICO_UNI_29_BENCAG.pdf',
       'Benevento squad list in 2017-18 match preview, page 2: CHRISTIAN RUTJENS OLIVA under DIFENSORI. Broad squad position, not match role.'
FROM futwar.player_season_stage
WHERE payload ->> 'player' = 'Christian Rutjens'
  AND payload ->> 'team' = 'Benevento' AND payload ->> 'season' = '2017-18'
  AND payload -> 'pos_' IN ('null'::jsonb, '"DF"'::jsonb)
ON CONFLICT DO NOTHING;
UPDATE futwar.player_season_stage AS s
SET payload = jsonb_set(s.payload, '{pos_}', e.enriched_value),
    quality_flags = (s.quality_flags - 'unknown_nominal_position') || '["externally_sourced_broad_position"]'::jsonb
FROM futwar.reviewed_enrichments e
WHERE s.source_sha256 = e.source_sha256 AND s.output_record = e.output_record
  AND e.field_name = 'pos_' AND s.payload -> 'pos_' = e.original_value;
UPDATE futwar.player_season_stage
SET quality_flags = quality_flags || '["external_appearance_minutes_discrepancy"]'::jsonb
WHERE payload ->> 'player' = 'Aiden O''Neill' AND payload ->> 'team' = 'Burnley'
  AND payload ->> 'season' = '2017-18'
  AND NOT quality_flags ? 'external_appearance_minutes_discrepancy';
DO $$
BEGIN
    IF (SELECT count(*) FROM futwar.player_season_stage WHERE payload ->> 'player' = 'Christian Rutjens'
        AND payload ->> 'team' = 'Benevento' AND payload ->> 'season' = '2017-18'
        AND payload ->> 'pos_' = 'DF') <> 1 THEN
        RAISE EXCEPTION 'Expected exactly one Rutjens position enrichment';
    END IF;
END $$;
COMMIT;
