"""Apply only approved source-reported PSxG fills to a further separate derivative."""
import csv
import hashlib
import json
import math

from reconcile_keeper_candidates import ROOT
from audit_missing_keeper_psxg import provider_id
import pyreadr

ADDED = ['psxg_original', 'psxg_correction_provenance', 'psxg_correction_warnings']


def apply_records(records, corrections):
    identifiers = [r['keeper_record_id'] for r in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate source records')
    targets = {}
    for correction in corrections:
        identifier = correction['keeper_record_id']
        value = float(correction['approved_value'])
        if correction['field'] != 'psxg' or not math.isfinite(value) or value < 0:
            raise ValueError('Unsupported PSxG correction')
        if identifier in targets or identifier not in identifiers:
            raise ValueError('Missing or duplicate PSxG target')
        targets[identifier] = correction
    output = []
    for original in records:
        row = dict(original)
        row['psxg_original'] = original['psxg']
        row['psxg_correction_provenance'] = ''
        row['psxg_correction_warnings'] = '[]'
        correction = targets.get(original['keeper_record_id'])
        if correction:
            if original['psxg'] != '' or correction['original_value'] != '':
                raise ValueError('PSxG fill would overwrite a populated value')
            for field in ['player_name', 'team_name', 'league', 'season']:
                if original[field] != correction[field]:
                    raise ValueError('PSxG target identity context changed')
            flags = json.loads(original['unresolved_quality_flags'])
            if 'missing_psxg' not in flags:
                raise ValueError('Target no longer has missing-PSxG flag')
            row['psxg'] = correction['approved_value']
            row['psxg_correction_provenance'] = json.dumps(correction, ensure_ascii=False)
            row['psxg_correction_warnings'] = json.dumps(correction['warnings'])
            row['unresolved_quality_flags'] = json.dumps([f for f in flags if f != 'missing_psxg'])
        output.append(row)
    return output


def main():
    source = ROOT / 'data/processed/keeper_archives/keeper_seasons_corrected.csv'
    plan_path = ROOT / 'data/keeper_psxg_corrections.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    fingerprints = {source.relative_to(ROOT).as_posix(): hashlib.sha256(source.read_bytes()).hexdigest()}
    if fingerprints[source.relative_to(ROOT).as_posix()] != plan['input_sha256']:
        raise ValueError('Exposure-corrected input differs from approved snapshot')
    with source.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        fields, records = reader.fieldnames, list(reader)
    if any(field in fields for field in ADDED):
        raise ValueError('Input already has PSxG corrections')
    manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    files = {item['name']: item for item in manifest['files']}
    report_path = ROOT / 'reports/keeper_archive/missing_psxg_candidates.csv'
    fingerprints[report_path.relative_to(ROOT).as_posix()] = hashlib.sha256(report_path.read_bytes()).hexdigest()
    with report_path.open(encoding='utf-8', newline='') as handle:
        candidates = list(csv.DictReader(handle))
    by_id = {r['keeper_record_id']: r for r in records}
    for correction in plan['corrections']:
        item = files[correction['source_file']]
        path = ROOT / item['path']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256'] or digest != correction['source_sha256'] or item['source_url'] != correction['source_url']:
            raise ValueError('Approved PSxG source changed')
        fingerprints[item['path']] = digest
        target = by_id[correction['keeper_record_id']]
        match = [r for r in candidates if r['keeper_record_id'] == correction['keeper_record_id']
                 and r['source_variant'] == correction['source_variant']]
        if len(match) != 1 or match[0]['candidate_status'] != 'exposure_agrees_metric_version_unconfirmed':
            raise ValueError('Candidate evidence no longer supports the fill')
        if float(match[0]['candidate_psxg']) != float(correction['approved_value']):
            raise ValueError('Approved value differs from candidate measurement')
        frame = next(iter(pyreadr.read_r(str(path)).values()))
        selected = frame.loc[frame.Url.map(provider_id).eq(provider_id(target['player_url']))
                             & frame.Season_End_Year.eq(int(target['season'][:4])+1)
                             & frame.Comp.eq(target['league']) & frame.Squad.eq(target['team_name'])]
        if len(selected) != 1 or float(selected.iloc[0].PSxG_Expected) != float(correction['approved_value']):
            raise ValueError('Approved value not present in exact archived source row')
        if int(selected.iloc[0].Born) != int(float(target['birth_year'])):
            raise ValueError('Archived source birth year differs')
    output = apply_records(records, plan['corrections'])
    targets = {c['keeper_record_id'] for c in plan['corrections']}
    for original, row in zip(records, output):
        changed = {field for field in fields if original[field] != row[field]}
        expected = {'psxg', 'unresolved_quality_flags'} if original['keeper_record_id'] in targets else set()
        if changed != expected:
            raise ValueError('Unapproved original field change')
    destination = source.with_name('keeper_seasons_analysis.csv')
    with destination.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields + ADDED)
        writer.writeheader()
        writer.writerows(output)
    for path, digest in fingerprints.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Input modified during PSxG fill')
    summary = dict(input_sha256=fingerprints, plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        output_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(), approved_on=plan['approved_on'],
        rows=len(output), psxg_filled_records=len(targets), remaining_missing_psxg=sum(r['psxg'] == '' for r in output),
        unresolved_flagged_records=sum(r['unresolved_quality_flags'] != '[]' for r in output),
        psxg_warning_records=sum(r['psxg_correction_warnings'] != '[]' for r in output),
        original_modified=False, metric_versions_confirmed=False)
    destination.with_name('psxg_correction_lineage.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
