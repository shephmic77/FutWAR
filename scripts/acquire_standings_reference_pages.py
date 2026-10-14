"""Archive 40 Wikipedia season-table API responses once, at a modest request rate."""
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEAGUES = {'Premier League':'Premier_League', 'La Liga':'La_Liga',
           'Serie A':'Serie_A', 'Bundesliga':'Bundesliga', 'Ligue 1':'Ligue_1'}
ROOT = Path('data/raw/wikipedia_standings/2026-10-10')
MANIFEST = Path('data/wikipedia_standings_manifest.json')


def acquire():
    ROOT.mkdir(parents=True,exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {
        'provider':'English Wikipedia contributors',
        'source_type':'secondary compiled standings, not official certification',
        'terms_url':'https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use',
        'license':'CC BY-SA 4.0; preserve article attribution and modification notice',
        'modifications':'Archived API bytes unchanged; standings extraction and club aliases are separate.',
        'files':[]}
    existing = {r['path']:r for r in manifest['files']}
    for year in range(2017,2025):
        season = f'{year}-{str(year+1)[-2:]}'
        for league,suffix in LEAGUES.items():
            title = f'{year}\u2013{str(year+1)[-2:]}_{suffix}'
            path = ROOT/f'{season}_{suffix}.json'
            relative = path.as_posix()
            if relative in existing:
                if hashlib.sha256(path.read_bytes()).hexdigest() != existing[relative]['sha256']:
                    raise ValueError(f'Archived response changed: {path}')
                continue
            if path.exists():
                raise ValueError(f'Unregistered archive exists: {path}')
            url = 'https://en.wikipedia.org/w/api.php?' + urllib.parse.urlencode({
                'action':'parse','page':title,'prop':'text|revid|externallinks',
                'format':'json','redirects':1,'maxlag':5})
            request = urllib.request.Request(url, headers={
                'User-Agent':'FutWAR/0.1 (research audit; https://github.com/shephmic77/FutWAR)'})
            with urllib.request.urlopen(request,timeout=30) as response:
                payload = response.read()
            data = json.loads(payload.decode('utf-8'))
            if 'error' in data:
                raise ValueError(f'API error: {data["error"]}')
            parsed = data['parse']
            revision = parsed['revid']
            with path.open('xb') as handle:
                handle.write(payload)
            record = dict(path=relative,league=league,season=season,
                title=parsed['title'],revision_id=revision,api_url=url,
                source_url=f'https://en.wikipedia.org/w/index.php?oldid={revision}',
                retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload))
            manifest['files'].append(record)
            MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
            print(f'{league} {season}: archived revision {revision}',flush=True)
            time.sleep(1)
    print(f'Archived {len(manifest["files"])} scoped pages.',flush=True)


if __name__=='__main__':
    acquire()
