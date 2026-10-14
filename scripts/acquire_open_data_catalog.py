"""Archive pinned public catalog and terms/specifications; no match events imported."""
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'FutWAR/0.1 source audit'})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read(20_000_001)
    if len(payload) > 20_000_000:
        raise ValueError('Catalog/specification size guard exceeded')
    return payload


def main():
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / 'data/open_data_catalog_manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    else:
        commit = json.loads(get('https://api.github.com/repos/hudl/open-data/commits/master'))['sha']
        manifest = dict(provider='StatsBomb (Hudl) Open Data', repository='https://github.com/hudl/open-data',
                        commit=commit, terms_status='Archived license requires review; no redistribution assumed',
                        purpose='Catalog and specification inspection; no model or source adoption', files=[])
    paths = ['LICENSE.pdf', 'data/competitions.json', 'doc/Open Data Lineups v2.0.0.pdf',
             'doc/Open Data Events v4.0.0.pdf']
    folder = root / 'data/raw/statsbomb_open/2026-10-10'
    for source_path in paths:
        existing = next((r for r in manifest['files'] if r['source_path'] == source_path), None)
        if existing:
            if hashlib.sha256((root / existing['path']).read_bytes()).hexdigest() != existing['sha256']:
                raise ValueError('Archived catalog or specification changed')
            continue
        target = folder / source_path
        if target.exists():
            raise ValueError('Unregistered archive already exists')
        url = 'https://raw.githubusercontent.com/hudl/open-data/' + manifest['commit'] + '/' + urllib.parse.quote(source_path)
        payload = get(url)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(payload)
        manifest['files'].append(dict(source_path=source_path, path=target.relative_to(root).as_posix(), source_url=url,
                                     sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload),
                                     retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(source_path + ': archived', flush=True)


if __name__ == '__main__':
    main()
