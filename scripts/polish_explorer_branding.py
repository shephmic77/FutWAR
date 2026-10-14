"""Install user-supplied branding without altering the original PNG files."""
import hashlib
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--light', required=True, type=Path, help='Path to the light-theme logo PNG')
parser.add_argument('--dark', required=True, type=Path, help='Path to the dark-theme logo PNG')
args = parser.parse_args()
assets = []
for theme, original in (('light', args.light), ('dark', args.dark)):
    target = ROOT / 'data/raw/explorer_branding/2026-10-10' / (theme + '.png')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == original.read_bytes()
    else:
        target.write_bytes(original.read_bytes())
    assets.append({'kind': 'brand', 'label': theme, 'path': target.relative_to(ROOT).as_posix(),
                   'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                   'title': 'FutWAR ' + theme + ' logo', 'artist': 'User supplied',
                   'source_page': '', 'license': 'User supplied for this project; original unchanged',
                   'retrieved_at': '2026-10-10'})
(ROOT / 'data/explorer_branding.json').write_text(json.dumps({'assets': assets}, indent=2), encoding='utf-8')
print('Archived both user-supplied logos unchanged.')
