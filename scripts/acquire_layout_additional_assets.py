"""Archive reviewed Commons UI assets, preserving source and licensing metadata."""
import hashlib
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from acquire_open_data_catalog import get

ROOT = Path(__file__).resolve().parents[1]
ASSETS = [
    ('league', 'La Liga', 'File:LaLiga wordmark.svg'),
    ('league', 'Serie A', 'File:Serie A.svg'),
    ('league', 'Bundesliga', 'File:Bundesliga logo.svg'),
    ('league', 'Ligue 1', 'File:Ligue1.svg'),
    ('club', 'Napoli', 'File:SSC Napoli.svg'),
    ('portrait', 'Lorenzo Insigne', 'File:Lorenzo insigne.jpg'),
]

def main():
    target = ROOT / 'data/layout_additional_assets.json'
    manifest = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {'assets': []}
    for kind, label, title in ASSETS:
        if any(a['label'] == label and a['kind'] == kind for a in manifest['assets']):
            continue
        query = urllib.parse.urlencode(dict(action='query', format='json', titles=title, prop='imageinfo', iiprop='url|extmetadata'))
        page = next(iter(json.loads(get('https://commons.wikimedia.org/w/api.php?' + query))['query']['pages'].values()))
        if 'imageinfo' not in page:
            print('No reviewed asset: ' + title, flush=True)
            continue
        info = page['imageinfo'][0]
        ext = info['extmetadata']
        license_name = ext.get('LicenseShortName', {}).get('value', '')
        if license_name not in ('Public domain', 'CC BY-SA 3.0', 'CC BY-SA 4.0', 'CC BY 3.0', 'CC BY 4.0'):
            print('License requires review: ' + title + ': ' + license_name, flush=True)
            continue
        raw = get(info['url'])
        name = re.sub('[^a-z0-9]+', '-', label.lower()).strip('-')
        suffix = '.jpg' if kind == 'portrait' else '.svg'
        path = ROOT / 'data/raw/profile_images/2026-10-10' / (name + '-layout' + suffix)
        if kind != 'portrait' and not raw.lstrip().startswith((b'<svg', b'<?xml', b'<!--')):
            raise ValueError('Expected SVG image')
        path.write_bytes(raw) if not path.exists() else None
        if path.read_bytes() != raw:
            raise ValueError('Existing source asset differs')
        manifest['assets'].append(dict(kind=kind, label=label, title=title, mime='image/jpeg' if kind == 'portrait' else 'image/svg+xml',
            source_page=info['descriptionurl'], source_url=info['url'], license=license_name,
            artist=re.sub('<[^>]+>', '', ext.get('Artist', {}).get('value', 'Unknown')),
            license_url=ext.get('LicenseUrl', {}).get('value', ''),
            path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(raw).hexdigest(),
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
            historical_accuracy='UI illustration; not asserted to match the season edition; trademarks retained'))
        target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Archived ' + label, flush=True)

if __name__ == '__main__':
    main()
