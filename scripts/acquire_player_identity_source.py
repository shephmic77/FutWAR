"""Archive the publisher's CSV downloads; never scrape Transfermarkt pages."""
import hashlib
import json
import urllib.request
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path('data/raw/transfermarkt_publisher/2026-10-10')
MANIFEST=Path('data/player_identity_source_manifest.json')
BASE='https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/'
FILES=['competitions.csv.gz','clubs.csv.gz','players.csv.gz','games.csv.gz','appearances.csv.gz','transfers.csv.gz','player_valuations.csv.gz']


def acquire():
    ROOT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else dict(
        publisher='dcaribou/transfermarkt-datasets',
        download_documentation='https://github.com/dcaribou/transfermarkt-datasets',
        publisher_license='CC0-1.0 (publisher declaration; upstream rights not independently confirmed)',
        license_url='https://github.com/dcaribou/transfermarkt-datasets/blob/master/LICENSE',
        access_method='Publisher public CSV downloads; no upstream scraping',
        redistribution_policy='Private research archive; raw and processed exports excluded from Git',files=[])
    known={r['filename']:r for r in manifest['files']}
    for filename in FILES:
        target=ROOT/filename
        if filename in known:
            if hashlib.sha256(target.read_bytes()).hexdigest()!=known[filename]['sha256']:
                raise ValueError('Archived source changed: '+filename)
            continue
        if target.exists():
            raise ValueError('Unregistered archive exists: '+filename)
        request=urllib.request.Request(BASE+filename,headers={'User-Agent':'FutWAR/0.1 research source audit'})
        with urllib.request.urlopen(request,timeout=45) as response:
            payload=response.read(300_000_001)
            if len(payload)>300_000_000:
                raise ValueError('Source exceeds acquisition size guard')
        with target.open('xb') as handle:handle.write(payload)
        record=dict(filename=filename,path=target.as_posix(),source_url=BASE+filename,
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload))
        manifest['files'].append(record)
        MANIFEST.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(f'{filename}: archived {len(payload):,} bytes',flush=True)
    print('Publisher source archive complete.',flush=True)


if __name__=='__main__':acquire()
