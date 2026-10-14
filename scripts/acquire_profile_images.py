"""Archive a small manually reviewed Commons visual sample with credit metadata."""
import hashlib
import json
import re
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from acquire_open_data_catalog import get

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    ('salah-headshot', 'File:Mohamed Salah 2017 (cropped).jpg', 'portrait', 'Mohamed Salah', 'CC BY-SA 3.0'),
    ('salah', 'File:Mo Salah 2018 (cropped).jpg', 'portrait', 'Mohamed Salah', 'CC BY 2.0'),
    ('ramsdale', 'File:Aaron Ramsdale 2019 (cropped).png', 'portrait', 'Aaron Ramsdale', 'CC BY 3.0'),
    ('liverpool', 'File:Logo Liverpool FC (2024).png', 'club', 'Liverpool', 'Public domain'),
    ('premier-league', 'File:Premier League.svg', 'league', 'Premier League', 'Public domain'),
]


def main():
    target = ROOT / 'data/profile_image_manifest.json'
    manifest = json.loads(target.read_bytes()) if target.exists() else {'purpose': 'Private UI illustration; not historical identity evidence', 'assets': []}
    for identifier, title, kind, label, reviewed_license in ASSETS:
        if any(a['id'] == identifier for a in manifest['assets']):
            continue
        query = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'titles': title,
            'prop': 'imageinfo', 'iiprop': 'url|extmetadata'})
        metadata = json.loads(get('https://commons.wikimedia.org/w/api.php?' + query))
        page = next(iter(metadata['query']['pages'].values()))
        info = page['imageinfo'][0]
        ext = info['extmetadata']
        license_name = ext.get('LicenseShortName', {}).get('value', '')
        if license_name != reviewed_license:
            raise ValueError(f'Review image license before acquisition: {title}: {license_name}')
        url = info['url']
        payload = get(url)
        suffix = Path(urllib.parse.urlparse(url).path).suffix
        path = ROOT / 'data/raw/profile_images/2026-10-10' / (identifier + suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(payload)
        manifest['assets'].append({'id': identifier, 'kind': kind, 'label': label,
            'title': title, 'source_page': info['descriptionurl'], 'source_url': url,
            'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(payload).hexdigest(),
            'license': license_name, 'license_url': ext.get('LicenseUrl', {}).get('value', ''),
            'artist': re.sub('<[^>]+>', '', ext.get('Artist', {}).get('value', 'Unknown')),
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
            'display_changes': 'CSS fit/crop only; original archived unchanged',
            'historical_season_accuracy': 'Illustration only; portrait/logo is not promised to match selected season'})
        target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('Archived ' + identifier, flush=True)
        time.sleep(0.4)


if __name__ == '__main__':
    main()
