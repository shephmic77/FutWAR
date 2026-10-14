"""Apply only approved fills to a separate table, retaining every original field."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDED = ['keeper_minutes_original', 'appearances_original', 'minute_correction_provenance',
         'exposure_correction_provenance', 'exposure_correction_warnings', 'unresolved_quality_flags']


def apply_records(records, corrections):
    ids = [r['keeper_record_id'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate keeper record IDs')
    mapping = {}
    for correction in corrections:
        identifier = correction['keeper_record_id']
        key = identifier, correction['field']
        if key in mapping or identifier not in ids:
            raise ValueError('Duplicate or missing correction target')
        if correction['field'] not in ['keeper_minutes', 'appearances'] or not correction['approved_value'].isdigit() or int(correction['approved_value']) <= 0:
            raise ValueError('Unsupported correction')
        mapping[key] = correction
    output = []
    for original in records:
        row = dict(original)
        row['keeper_minutes_original'] = original['keeper_minutes']
        row['appearances_original'] = original.get('appearances', '')
        row['minute_correction_provenance'] = ''
        provenance, warnings = [], []
        flags = json.loads(original['quality_flags'])
        for target_field in ['keeper_minutes', 'appearances']:
            correction = mapping.get((original['keeper_record_id'], target_field))
            if not correction:
                continue
            if original[target_field] != correction['original_value']:
                raise ValueError('Correction would overwrite an unexpected value')
            for field in ['player_name', 'team_name', 'league', 'season']:
                if original[field] != correction[field]:
                    raise ValueError('Correction identity context changed')
            row[target_field] = correction['approved_value']
            provenance.append(correction)
            warnings.extend(correction.get('warnings', []))
            if target_field == 'keeper_minutes':
                row['minute_correction_provenance'] = json.dumps(correction, ensure_ascii=False)
            resolved = correction.get('resolved_flags',
                ['missing_or_nonpositive_keeper_minutes'] if correction['original_value'] == '' and target_field == 'keeper_minutes' else [])
            flags = [flag for flag in flags if flag not in resolved]
        row['exposure_correction_provenance'] = json.dumps(provenance, ensure_ascii=False)
        row['exposure_correction_warnings'] = json.dumps(sorted(set(warnings)))
        row['unresolved_quality_flags'] = json.dumps(flags)
        output.append(row)
    return output


def main():
    source = ROOT / 'data/processed/keeper_archives/keeper_seasons.csv'
    plan_path = ROOT / 'data/keeper_minute_corrections.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    exposure_path = ROOT / 'data/keeper_exposure_corrections.json'
    exposure_plan = json.loads(exposure_path.read_text(encoding='utf-8'))
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != plan['input_sha256'] or before != exposure_plan['input_sha256']:
        raise ValueError('Staging input differs from the approved snapshot')
    with source.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        original = list(reader)
    if any(field in fields for field in ADDED):
        raise ValueError('Input is already a corrected table')
    comparison_path = ROOT / 'reports/keeper_archive/playing_time_season_review.csv'
    with comparison_path.open(encoding='utf-8', newline='') as handle:
        comparisons = list(csv.DictReader(handle))
    for correction in plan['corrections']:
        matches = [r for r in comparisons if r['player_name'] == correction['player_name']
                   and r['season'] == correction['season']]
        if len(matches) != 1 or any(float(matches[0][field]) != 1 for field in
                                  ['local_minutes', 'publisher_minutes', 'local_appearances', 'publisher_appearances']):
            raise ValueError('One-minute comparison evidence changed')
    for correction in exposure_plan['corrections']:
        matches = [r for r in comparisons if r['player_name'] == correction['player_name'] and r['season'] == correction['season']]
        column = 'local_minutes' if correction['field'] == 'keeper_minutes' else 'local_appearances'
        if len(matches) != 1 or float(matches[0][column]) != int(correction['approved_value']):
            raise ValueError('Approved main-player exposure evidence changed')
    corrections = plan['corrections'] + exposure_plan['corrections']
    result = apply_records(original, corrections)
    changed = []
    for old, new in zip(original, result):
        differences = [field for field in fields if old[field] != new[field]]
        if differences:
            expected = [c['field'] for c in corrections if c['keeper_record_id'] == old['keeper_record_id']]
            if set(differences) != set(expected):
                raise ValueError('Unapproved field change')
            changed.append(old['keeper_record_id'])
    if set(changed) != {c['keeper_record_id'] for c in corrections}:
        raise ValueError('Unexpected correction count')
    target = source.with_name('keeper_seasons_corrected.csv')
    with target.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields + ADDED)
        writer.writeheader()
        writer.writerows(result)
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise ValueError('Original staging table changed')
    lineage = dict(input_sha256=before, plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        exposure_plan_sha256=hashlib.sha256(exposure_path.read_bytes()).hexdigest(),
        comparison_sha256=hashlib.sha256(comparison_path.read_bytes()).hexdigest(),
        output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(), rows=len(result),
        corrected_records=len(changed), corrected_fields=len(corrections),
        exposure_warning_records=sum(r['exposure_correction_warnings'] != '[]' for r in result),
        original_flagged_records=sum(r['quality_flags'] != '[]' for r in result),
        unresolved_flagged_records=sum(r['unresolved_quality_flags'] != '[]' for r in result),
        approved_on=plan['approved_on'], convention=[plan['convention'], exposure_plan['convention']],
        original_modified=False, exposure_validated=False)
    target.with_name('correction_lineage.json').write_text(json.dumps(lineage, indent=2), encoding='utf-8')
    print(json.dumps(lineage, indent=2))


if __name__ == '__main__':
    main()
