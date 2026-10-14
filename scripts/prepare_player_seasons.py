"""Apply the user-approved, source-specific correction and prepare staging exports."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

if __package__:
    from .audit_data import audit, read_json
else:
    from audit_data import audit, read_json

EXPECTED_SHA = '298ee166002a5fc8759000d8c739cd046c85adbea51f2a17716cbdb19725db45'
NAME = 'Top5_League_Players_2017to2024_dataset.csv'
KEY_COLUMNS = ('league', 'season', 'team', 'player')
APPROVED_KEY = ('ITA-Serie A', '1718', 'Milan', 'Emanuele Torrasi')
TEXT_COLUMNS = {'league', 'season', 'team', 'player', 'nation_', 'pos_'}


def collapse_group(rows):
    """Retain unambiguous values; refuse any conflict beyond the approved field."""
    merged, conflicts = {}, {}
    for column in rows[0]:
        known = list(dict.fromkeys(r[column] for r in rows if r[column].strip()))
        if len(known) > 1:
            conflicts[column] = sorted(known)
            merged[column] = ''
        else:
            merged[column] = known[0] if known else ''
    if conflicts != {'Subs_unSub': ['0', '1']}:
        raise ValueError(f'Conflict pattern differs from approved correction: {conflicts}')
    return merged



def apply_reviewed_enrichments(clean, flags, enrichments):
    """Apply only the explicit sourced position fill; flag numerical disagreements."""
    notes = []
    key = tuple(clean[c] for c in KEY_COLUMNS)
    position = enrichments['position_enrichment']
    if key == tuple(position['key']):
        if clean[position['field']] != position['old_value']:
            raise ValueError('Position no longer matches reviewed missing value')
        clean[position['field']] = position['new_value']
        flags = flags + ['externally_sourced_broad_position']
        notes.append(position)
    discrepancy = enrichments['appearance_discrepancy']
    if key == tuple(discrepancy['key']):
        flags = flags + ['external_appearance_minutes_discrepancy']
        notes.append(discrepancy)
    return flags, notes


def build():
    source = Path('data/raw') / NAME
    source_bytes = source.read_bytes()
    digest = hashlib.sha256(source_bytes).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError('Source fingerprint changed; re-audit and review before correction')
    config = read_json(Path('audit_config.json'))
    settings = config['files'][NAME]
    manifest = read_json(Path('data/source_manifest.json'))
    enrichments = read_json(Path('data/reviewed_enrichments.json'))
    with source.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter=';', strict=True)
        header = reader.fieldnames
        rows = list(reader)
    selected = [(i, r) for i, r in enumerate(rows, start=2) if tuple(r[c] for c in KEY_COLUMNS) == APPROVED_KEY]
    if len(selected) != 512:
        raise ValueError('Approved key must have exactly 512 source records')
    merged = collapse_group([r for _, r in selected])
    selected_numbers = {i for i, _ in selected}
    collapsed, emitted = [], False
    for number, row in enumerate(rows, start=2):
        if number in selected_numbers:
            if emitted:
                continue
            collapsed.append((merged, sorted(selected_numbers), ['collapsed_512_records', 'Subs_unSub_conflict_set_missing']))
            emitted = True
        else:
            collapsed.append((row, [number], []))
    normalized, lineage, seen = [], [], set()
    for ordinal, (row, record_numbers, flags) in enumerate(collapsed, start=1):
        clean = {}
        for column, value in row.items():
            value = value.strip()
            if value in config['null_tokens']:
                clean[column] = ''
            elif column in TEXT_COLUMNS:
                clean[column] = value
            else:
                try:
                    parsed = Decimal(value.replace(',', '.'))
                except InvalidOperation as error:
                    raise ValueError(f'Invalid number in source records {record_numbers}: {column}') from error
                if not parsed.is_finite():
                    raise ValueError('Nonfinite numeric value')
                clean[column] = format(parsed, 'f')
        clean['league'] = settings['league_aliases'][row['league']]
        clean['season'] = settings['season_aliases'][row['season']]
        key = tuple(clean[c] for c in KEY_COLUMNS)
        if key in seen:
            raise ValueError(f'Unresolved duplicate key: {key}')
        seen.add(key)
        flags, enrichment_notes = apply_reviewed_enrichments(clean, flags, enrichments)
        if not clean['pos_']:
            flags = flags + ['unknown_nominal_position']
        if clean['pos_'] == 'GK':
            flags = flags + ['goalkeeper_separate_model']
        normalized.append(clean)
        lineage.append({'output_record': ordinal, 'source_record_numbers_including_header': record_numbers,
                        'quality_flags': flags, 'external_evidence': enrichment_notes})
    output = Path('data/processed/player_seasons')
    output.mkdir(parents=True, exist_ok=True)
    cleaned = output / NAME
    with cleaned.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=header, delimiter=';')
        writer.writeheader()
        writer.writerows(normalized)
    provenance = {'source_sha256': digest, 'output_sha256': hashlib.sha256(cleaned.read_bytes()).hexdigest(),
                  'source_file': NAME, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                  'input_rows': len(rows), 'output_rows': len(normalized),
                  'policy': 'User-approved collapse of Torrasi/Milan/2017-18 only; unique nonblank values retained; Subs_unSub conflict left missing',
                  'normalization': 'Explicit league/season aliases; decimal comma to decimal point; configured missing cells stay missing; nominal positions preserved',
                  'external_validation': 'Broad defender position externally sourced; numerical validation unresolved', 'reviewed_enrichments': enrichments, 'records': lineage}
    Path('data/processed/lineage.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    staging = Path('data/processed/postgres')
    staging.mkdir(exist_ok=True)
    with (staging/'source_files.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['source_sha256','filename','source_url','metadata'])
        writer.writerow([digest, NAME, manifest[NAME]['source_url'], json.dumps(manifest[NAME])])
    with (staging/'player_seasons.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['source_sha256','output_record','source_record_numbers','quality_flags','payload'])
        for row, meta in zip(normalized, lineage):
            payload = {c: None if not v else v if c in TEXT_COLUMNS else v for c,v in row.items()}
            # Numeric strings preserve exact decimal precision; typed SQL casts come later.
            writer.writerow([digest, meta['output_record'], json.dumps(meta['source_record_numbers_including_header']),
                             json.dumps(meta['quality_flags']), json.dumps(payload, ensure_ascii=False)])
    processed_config = json.loads(json.dumps(config))
    processed_config['files'][NAME]['decimal'] = '.'
    metadata = {NAME: {**manifest[NAME], 'transformation': provenance['policy'], 'input_sha256': digest}}
    report = audit(output, Path('reports/processed'), processed_config, metadata)
    Path('reports/processed_config.json').write_text(json.dumps(processed_config,indent=2),encoding='utf-8')
    if source.read_bytes() != source_bytes:
        raise RuntimeError('Raw source changed during processing')
    summary = report['files'][0]
    if summary['rows'] != 22418 or summary['duplicate_key_rows'] or summary['malformed_rows']:
        raise RuntimeError('Processed audit failed')
    print(json.dumps({'input_rows': len(rows), 'processed_rows': len(normalized),
                      'excess_records_removed': len(rows)-len(normalized), 'duplicate_keys': summary['duplicate_key_rows'],
                      'raw_unchanged': True, 'staging_loaded_to_database': False},indent=2))


if __name__ == '__main__':
    build()
