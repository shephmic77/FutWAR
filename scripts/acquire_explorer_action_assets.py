"""Acquire reviewed action illustrations; never infer season roles from photographs.

PowerShell: py scripts/acquire_explorer_action_assets.py
Optional discovery: py scripts/acquire_explorer_action_assets.py --catalog
Raw originals remain immutable. Commons file licenses and photographer credits
are retained individually; a Wikimedia catalogue entry is not blanket permission.
"""
import argparse
import csv
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/raw/explorer_assets/2026-10-10/players'
MANIFEST = ROOT / 'data/explorer_action_assets.json'
REVIEWED = [
    ('paulo-dybala-action', 'Paulo Dybala', '206050',
     'File:Frosinone Calcio - Stadio Matusa - vs Juventus 7 2 2016 0-2 - DSC 4255 - Dybala vs Gori (cropped).jpg',
     'CC BY-SA 4.0', '2016-02-07', 'Juventus match action; upstream crop includes full body'),
    ('mohamed-salah-action', 'Mohamed Salah', '148455',
     'File:Mohamed Salah 2017.jpg', 'CC BY-SA 3.0', '2017-09-26', 'Liverpool at Spartak match'),
    ('lorenzo-insigne-action', 'Lorenzo Insigne', '133964',
     'File:Barça - Napoli - 20140806 - 16 (cropped).jpg',
     'CC BY-SA 3.0', '2014-08-06', 'Napoli friendly match action; upstream crop'),
    ('harry-kane-action', 'Harry Kane', '132098',
     'File:Harry Kane 2018.jpg', 'CC BY-SA 3.0', '2018-07-13', 'England World Cup match; international kit'),
]


def get(url):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'FutWAR/0.1 personal research imagery audit',
        'Accept': 'application/json,image/*;q=0.8,*/*;q=0.5'})
    # No retries or alternate domains for a denied or rate-limited request.
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(20_000_001)
    if len(payload) > 20_000_000:
        raise ValueError('Asset size guard exceeded')
    return payload


def archive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError(f'Immutable archive differs: {path}')
    else:
        with path.open('xb') as handle:
            handle.write(payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', action='store_true')
    parser.add_argument('--catalog-only', action='store_true', help='Independent discovery; no Commons requests')
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {
        'purpose': 'Cited player action illustrations, separate from statistics',
        'historical_accuracy': 'Photographs are illustrations; selected season or club accuracy is not asserted.',
        'assets': [], 'catalogue': {}}
    if args.catalog_only:
        manifest['access_gap'] = 'Commons original image endpoint returned HTTP 429 on first request; downloads stopped without retries.'
        manifest['reviewed_candidates'] = [{
            'id': identifier, 'player_name': name, 'provider_player_id': provider_id,
            'source_page': 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_')),
            'license': license_name, 'photo_date': photo_date, 'description': description,
            'status': 'reviewed_source_not_archived_due_to_rate_limit'}
            for identifier, name, provider_id, title, license_name, photo_date, description in REVIEWED]
    for identifier, name, provider_id, title, license_name, photo_date, description in ([] if args.catalog_only else REVIEWED):
        existing = next((a for a in manifest['assets'] if a['id'] == identifier), None)
        if existing:
            if hashlib.sha256((ROOT / existing['path']).read_bytes()).hexdigest() != existing['sha256']:
                raise ValueError('Registered original has changed')
            continue
        query = urllib.parse.urlencode({'action': 'query', 'format': 'json', 'titles': title,
                                       'prop': 'imageinfo', 'iiprop': 'url|extmetadata'})
        metadata_url = 'https://commons.wikimedia.org/w/api.php?' + query
        metadata_bytes = get(metadata_url)
        metadata = json.loads(metadata_bytes)
        info = next(iter(metadata['query']['pages'].values()))['imageinfo'][0]
        ext = info['extmetadata']
        if ext.get('LicenseShortName', {}).get('value') != license_name:
            raise ValueError(f'License differs from reviewed source: {title}')
        metadata_path = FOLDER / (identifier + '.metadata.json')
        archive(metadata_path, metadata_bytes)
        try:
            payload = get(info['url'])
        except urllib.error.HTTPError as exc:
            manifest['access_gap'] = f'Image acquisition stopped: HTTP {exc.code}; no retries or endpoint workarounds.'
            manifest['failed_asset'] = {'id': identifier, 'source_url': info['url'],
                'metadata_path': metadata_path.relative_to(ROOT).as_posix()}
            MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
            break
        path = FOLDER / (identifier + Path(urllib.parse.urlparse(info['url']).path).suffix)
        archive(path, payload)
        manifest['assets'].append({
            'id': identifier, 'kind': 'player', 'label': name, 'player_name': name,
            'provider_player_id': provider_id, 'image_style': 'action', 'title': title,
            'source_page': info['descriptionurl'], 'source_url': info['url'],
            'path': path.relative_to(ROOT).as_posix(), 'bytes': len(payload),
            'sha256': hashlib.sha256(payload).hexdigest(), 'metadata_url': metadata_url,
            'metadata_path': metadata_path.relative_to(ROOT).as_posix(),
            'license': license_name, 'license_url': ext.get('LicenseUrl', {}).get('value', ''),
            'artist': re.sub('<[^>]+>', '', ext.get('Artist', {}).get('value', '')),
            'photo_date': photo_date, 'description': description,
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
            'display_changes': 'CSS contain only; original downloaded bytes unchanged',
            'historical_season_accuracy': 'Illustration only; use photo_date and description before claiming season/club accuracy'})
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'Archived {name}', flush=True)
        time.sleep(1)
    if args.catalog or args.catalog_only:
        # Public structured metadata; use stable provider IDs, never guessed names.
        query = ('SELECT ?person ?tmid ?image WHERE { ?person wdt:P2446 ?tmid; '
                 'wdt:P18 ?image. } LIMIT 15000')
        url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': query, 'format': 'json'})
        try:
            payload = get(url)
            archive(FOLDER / 'wikidata-image-catalogue.json', payload)
            bindings = json.loads(payload)['results']['bindings']
            manifest['catalogue'] = {'status': 'discovery_only', 'source_url': url,
                'metadata_license': 'CC0; individual photograph rights require separate Commons review',
                'path': (FOLDER / 'wikidata-image-catalogue.json').relative_to(ROOT).as_posix(),
                'sha256': hashlib.sha256(payload).hexdigest(), 'candidate_rows': len(bindings),
                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'style_warning': 'P18 images may be portraits; no action-photo style assertion',
                'candidates': [{'provider_player_id': b['tmid']['value'],
                    'wikidata_entity': b['person']['value'], 'image_reference': b['image']['value']}
                    for b in bindings]}
        except Exception as exc:
            manifest['catalogue'] = {'status': 'unavailable', 'source_url': url, 'error': str(exc),
                'note': 'No retry or alternate endpoint attempted; separately registered assets, if any, are unchanged.'}
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    data_path = ROOT / 'reports/player_profile/enriched_data.json'
    data = json.loads(data_path.read_text(encoding='utf-8'))
    names = {a['player_name'] for a in manifest['assets']}
    out = ROOT / 'reports/explorer_action_assets_coverage.csv'
    with out.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['league', 'season', 'records', 'action_illustration_records', 'missing_action_records'])
        writer.writeheader()
        for league, season in sorted({(r['league'], r['season']) for r in data['records']}):
            rows = [r for r in data['records'] if r['league'] == league and r['season'] == season]
            present = sum(r['name'] in names for r in rows)
            writer.writerow(dict(league=league, season=season, records=len(rows),
                action_illustration_records=present, missing_action_records=len(rows)-present))
    print(f'Reviewed action assets: {len(manifest["assets"])}; coverage report: {out}', flush=True)


if __name__ == '__main__':
    main()
