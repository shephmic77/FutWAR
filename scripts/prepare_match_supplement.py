"""Validate a sourced supplement against the exact pinned, unscored fixtures."""
import csv
import hashlib
import json
from pathlib import Path

if __package__:
    from .acquire_openfootball import COMMIT
    from .audit_data import write_csv
else:
    from acquire_openfootball import COMMIT
    from audit_data import write_csv

KEY_FIELDS = ('league','season','match_date','home_label','away_label')


def validate_supplements(records, expected):
    seen = set()
    for r in records:
        key = tuple(r[k] for k in KEY_FIELDS)
        if key not in expected:
            raise ValueError(f'Supplement is not an approved missing fixture: {key}')
        if key in seen:
            raise ValueError(f'Duplicate supplemented fixture: {key}')
        if any(type(r[k]) is not int or r[k] < 0 for k in ('home_goals','away_goals')):
            raise ValueError('Full-time scores must be nonnegative integers')
        if not r.get('source_url','').startswith('https://') or not r.get('verified_on'):
            raise ValueError('Source URL and verification date required')
        seen.add(key)
    if seen != expected:
        raise ValueError('Supplement does not cover exactly the approved missing fixtures')


def prepare():
    raw = Path('data/raw/match_supplements/2024-25_final_round_verified.json')
    contents = raw.read_bytes()
    digest = hashlib.sha256(contents).hexdigest()
    records = json.loads(contents)['records']
    manifest = json.loads(Path('data/openfootball_manifest.json').read_text(encoding='utf-8'))
    expected = set()
    original_hashes = {}
    for code, league in [('es.1','La Liga'),('it.1','Serie A')]:
        relative=f'2024-25/{code}.json'
        path=Path('data/raw/openfootball')/COMMIT/relative
        source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        if source_hash != manifest['file_sha256'][relative]:
            raise ValueError('Original match source changed')
        original_hashes[relative]=source_hash
        for r in json.loads(path.read_text(encoding='utf-8'))['matches']:
            if (r.get('score') or {}).get('ft') is None:
                if r.get('round') != 'Matchday 38':
                    raise ValueError('Unexpected unscored round')
                expected.add((league,'2024-25',r['date'],r['team1'],r['team2']))
    if len(expected)!=20:
        raise ValueError('Expected exactly 20 unscored final-round fixtures')
    validate_supplements(records, expected)
    output=Path('data/processed/match_results')
    export=[]
    for r in records:
        export.append({**{k:r[k] for k in KEY_FIELDS},'home_goals':r['home_goals'],
            'away_goals':r['away_goals'],'base_source_sha256':original_hashes[r['original_file']],
            'supplement_sha256':digest,'source_url':r['source_url'],'verified_on':r['verified_on'],
            'evidence':json.dumps({k:r[k] for k in ('verification_method','original_file','original_round','source_license')})})
    write_csv(output/'verified_supplements.csv',list(export[0]),export)
    audit = {'supplement_file':raw.as_posix(),'supplement_sha256':digest,
        'record_count':len(records),'original_source_hashes':original_hashes,
        'exact_missing_fixture_set_verified':True,'fulltime_score_recovery_only':True,
        'local_pdf_archiving':'Unavailable: local DNS failed. Official published report text was verified through web tools; remote source URLs retained.',
        'supplement_license':'No open license established; private research evidence stays ignored by Git',
        'effective_scored_match_count_expected':14359,'ligue_1_2019_20_not_supplemented':True}
    Path('data/match_supplement_manifest.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    prepare()
