"""Download a fixed OpenFootball CC0 snapshot once; preserve original bytes."""
import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

COMMIT = 'e6744429ee395bc86f247348c6184bb08d4eb361'
SEASONS = ['2017-18','2018-19','2019-20','2020-21','2021-22','2022-23','2023-24','2024-25']
CODES = {'en.1':'Premier League','es.1':'La Liga','it.1':'Serie A','de.1':'Bundesliga','fr.1':'Ligue 1'}


def acquire():
    root = Path('data/raw/openfootball') / COMMIT
    root.mkdir(parents=True, exist_ok=True)
    archive = root / 'football.json.zip'
    url = f'https://codeload.github.com/openfootball/football.json/zip/{COMMIT}'
    metadata_path = root/'acquisition.json'
    if not archive.exists():
        request = urllib.request.Request(url, headers={'User-Agent':'FutWAR-research-source-audit/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read()
        with archive.open('xb') as handle:
            handle.write(payload)
        metadata_path.write_text(json.dumps({'source_url':url,'commit':COMMIT,
            'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
            'archive_sha256':hashlib.sha256(payload).hexdigest(),
            'license':'CC0-1.0','license_url':f'https://github.com/openfootball/football.json/blob/{COMMIT}/LICENSE.md'},indent=2),encoding='utf-8')
    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    if hashlib.sha256(archive.read_bytes()).hexdigest() != metadata['archive_sha256']:
        raise ValueError('Snapshot fingerprint mismatch')
    present, absent = [], []
    with zipfile.ZipFile(archive) as zipped:
        prefix = f'football.json-{COMMIT}/'
        for relative in ['LICENSE.md','README.md'] + [f'{season}/{code}.json' for season in SEASONS for code in CODES]:
            member = prefix + relative
            if member not in zipped.namelist():
                absent.append(relative)
                continue
            # Only fixed, explicitly listed paths are written; no arbitrary ZIP extraction.
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = zipped.read(member)
            if target.exists():
                if target.read_bytes() != payload:
                    raise ValueError(f'Existing source file differs: {target}')
            else:
                with target.open('xb') as handle:
                    handle.write(payload)
            present.append(relative)
    manifest = {'acquisition':metadata,'present_files':present,'absent_files':absent,
                'file_sha256':{r:hashlib.sha256((root/r).read_bytes()).hexdigest() for r in present}}
    output = Path('data/openfootball_manifest.json')
    output.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'download_bytes':archive.stat().st_size,'present':len(present),'absent':absent},indent=2))
    for name in ['2017-18/en.1.json','2019-20/fr.1.json','2024-25/fr.1.json']:
        target=root/name
        if target.exists():
            data=json.loads(target.read_text(encoding='utf-8-sig'))
            print(name,'keys',list(data),'sample',str(data)[:500])


if __name__ == '__main__':
    acquire()
