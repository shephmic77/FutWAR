"""Acquire a bounded, pinned public StatsBomb position sample; preserve raw files."""
import hashlib
import json
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

from acquire_open_data_catalog import get

ROOT = Path(__file__).resolve().parents[1]
CELLS = [(11, 1), (9, 281)]


def main():
    catalog = json.loads((ROOT / 'data/open_data_catalog_manifest.json').read_text())
    destination = ROOT / 'data/position_pilot_manifest.json'
    manifest = json.loads(destination.read_text()) if destination.exists() else {
        'provider': catalog['provider'], 'commit': catalog['commit'],
        'purpose': 'Six-match recorded-position validation; no seasonal role assignment',
        'access_review': 'Official statsbombpy README permits unauthenticated open data. '
            'Registration requested; linked form redirects and registration remains incomplete. '
            'Private noncommercial research; attribution required; no raw redistribution.',
        'access_evidence_url': 'https://github.com/hudl/statsbombpy#open-data',
        'sample_rule': 'Earliest, middle and latest listed match by date then match_id in each cell',
        'files': [], 'selected_matches': []}
    if manifest['commit'] != catalog['commit']:
        raise ValueError('Pilot and catalog commits differ')

    def archive(source):
        existing = next((f for f in manifest['files'] if f['source_path'] == source), None)
        if existing:
            payload = (ROOT / existing['path']).read_bytes()
            if hashlib.sha256(payload).hexdigest() != existing['sha256']:
                raise ValueError('Pilot raw input changed')
            return json.loads(payload)
        path = ROOT / 'data/raw/statsbomb_position_pilot/2026-10-10' / source
        if path.exists():
            raise ValueError('Unregistered raw pilot file exists')
        url = f"https://raw.githubusercontent.com/hudl/open-data/{manifest['commit']}/" + urllib.parse.quote(source)
        payload = get(url)
        parsed = json.loads(payload)
        if not isinstance(parsed, list):
            raise ValueError('Expected JSON list')
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as handle:
            handle.write(payload)
        manifest['files'].append({'source_path': source, 'path': path.relative_to(ROOT).as_posix(),
            'source_url': url, 'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload),
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat()})
        destination.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('Archived ' + source, flush=True)
        time.sleep(0.3)
        return parsed

    selections = []
    for competition, season in CELLS:
        matches = archive(f'data/matches/{competition}/{season}.json')
        ids = [m['match_id'] for m in matches]
        if len(ids) != len(set(ids)) or not matches:
            raise ValueError('Empty or duplicate match catalog')
        matches.sort(key=lambda m: (m['match_date'], m['match_id']))
        for index in sorted({0, len(matches) // 2, len(matches) - 1}):
            match = matches[index]
            selections.append({'competition_id': competition, 'season_id': season,
                'match_id': match['match_id'], 'date': match['match_date'],
                'catalog_match_count': len(matches)})
            archive(f"data/events/{match['match_id']}.json")
            archive(f"data/lineups/{match['match_id']}.json")
    manifest['selected_matches'] = selections
    destination.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Completed {len(selections)} sample matches; raw statistics unchanged.')


if __name__ == '__main__':
    main()
