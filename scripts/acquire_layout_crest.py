"""Archive the official Liverpool crest for the private layout review."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from acquire_open_data_catalog import get

root = Path(__file__).resolve().parents[1]
url = 'https://resources.premierleague.com/premierleague/badges/t14.svg'
target = root / 'data/raw/profile_images/2026-10-10/liverpool-full-crest.svg'
manifest_path = root / 'data/layout_full_crest_manifest.json'
if target.exists():
    if not manifest_path.exists():
        raise ValueError('Existing crest has no registered provenance')
    record = json.loads(manifest_path.read_text(encoding='utf-8'))
    if hashlib.sha256(target.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Archived crest hash changed')
else:
    payload = get(url)
    if b'<svg' not in payload[:1000]:
        raise ValueError('Expected official SVG image')
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(payload)
    record = dict(label='Liverpool', source_url=url, source_page='https://www.premierleague.com/',
                  path=target.relative_to(root).as_posix(), sha256=hashlib.sha256(payload).hexdigest(),
                  retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                  rights_holder='Liverpool Football Club', license='No open reuse license verified',
                  use_scope='Owner-requested private layout preview; no redistribution or public deployment authorized',
                  display_changes='CSS contain only; archived SVG unchanged',
                  terms_reference='https://www.liverpoolfc.com/corporate/brand-protection')
    manifest_path.write_text(json.dumps(record, indent=2), encoding='utf-8')
print('Official crest archived and hash verified; bytes:', target.stat().st_size)
