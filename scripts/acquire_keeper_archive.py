"""Inspect public archive candidates privately; data reuse rights remain unresolved."""
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/keeper_archive_manifest.json'
COMMIT = '2df143967509ff45584e261a2a033687346d654b'
BASE = 'https://api.github.com/repos/JaseZiv/worldfootballR_data'


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'FutWAR/0.1 archive inspection'})
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = response.read(10_000_001)
    if len(payload) > 10_000_000:
        raise ValueError('Archive inspection size guard exceeded')
    return payload


def main():
    folder = ROOT / 'data/raw/keeper_archive/2026-10-10'
    folder.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    else:
        manifest = dict(repository='https://github.com/JaseZiv/worldfootballR_data', commit=COMMIT,
            rights_status='Data license/upstream reuse unresolved; private candidate inspection only; no adoption or redistribution',
            files=[])

    def archive(name, url, expected_size=None):
        existing = next((f for f in manifest['files'] if f['name'] == name), None)
        if existing:
            payload = (ROOT / existing['path']).read_bytes()
            if hashlib.sha256(payload).hexdigest() != existing['sha256']:
                raise ValueError('Registered archive changed')
            return payload
        path = folder / name
        if path.exists():
            raise ValueError('Unregistered archive exists')
        payload = get(url)
        if expected_size is not None and len(payload) != expected_size:
            raise ValueError('Release size mismatch')
        with path.open('xb') as handle:
            handle.write(payload)
        manifest['files'].append(dict(name=name, path=path.relative_to(ROOT).as_posix(),
            source_url=url, bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
            retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
        MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(name + ': archived', flush=True)
        return payload

    archive('README.md', f'https://raw.githubusercontent.com/JaseZiv/worldfootballR_data/{COMMIT}/README.md')
    release = json.loads(archive('release_metadata.json', BASE + '/releases/tags/fb_big5_advanced_season_stats'))
    for name in ['big5_player_keepers.rds', 'big5_player_keepers_adv.rds']:
        asset = next(a for a in release['assets'] if a['name'] == name)
        archive('release_' + name, asset['browser_download_url'], asset['size'])
        archive('repository_' + name, f'https://raw.githubusercontent.com/JaseZiv/worldfootballR_data/{COMMIT}/data/fb_big5_advanced_season_stats/{name}')
        archive('statsbomb_' + name, f'https://raw.githubusercontent.com/JaseZiv/worldfootballR_data/{COMMIT}/data/fb_big5_advanced_statsbomb/{name}')
    # Separate candidate; its files and upstream data rights are also unresolved.
    nextgen_commit = 'bc1ac3fb3b6bd7a086ea86f05a75244ab9288dca'
    for name in ['goalkeeping_2024-2025.csv', 'advanced_goalkeeping_2024-2025.csv',
                 'goalkeeping_2023-2024.csv', 'advanced_goalkeeping_2023-2024.csv']:
        season = name[-13:-4]
        archive('nextgen_' + name, f'https://raw.githubusercontent.com/MahmoudMahdy448/NextGenEUPlayers/{nextgen_commit}/data/raw/{season}/{name}')


if __name__ == '__main__':
    main()
