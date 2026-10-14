"""Archive club logos using exact publisher IDs and Wikidata's P7223/P154.

Run from the project root: py scripts/acquire_explorer_club_assets.py
Assets are illustrative editions, not evidence of historical crest versions.
Never overwrite raw files; stop on HTTP 429 rather than bypass restrictions.
"""
import csv
import gzip
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from acquire_open_data_catalog import get

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data/explorer_club_assets.json'
ARCHIVE = ROOT / 'data/raw/explorer_assets/2026-10-10/clubs'
COMPETITIONS = {'L1': 'Bundesliga', 'GB1': 'Premier League', 'FR1': 'Ligue 1',
                'IT1': 'Serie A', 'ES1': 'La Liga'}


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def archive(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError('Immutable raw asset differs: ' + str(path))
    else:
        with path.open('xb') as handle:
            handle.write(payload)


def plain(value):
    return re.sub('<[^>]+>', '', value)


def main():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    teams = set()
    with (ROOT / 'data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv').open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle, delimiter=';'):
            teams.add((row['league'], row['team']))
    profile_export = ROOT / 'reports/player_profile/data.json'
    if profile_export.exists():
        teams.update((r['league'], r['team']) for r in json.loads(profile_export.read_text(encoding='utf-8'))['records'])
    aliases = {}
    for filename in ['identity_club_aliases.json', 'club_aliases.json', 'wikipedia_club_aliases.json']:
        for league, mapping in json.loads((ROOT / 'data' / filename).read_text(encoding='utf-8')).items():
            aliases.setdefault(league, {}).update(mapping)
    matched = {}
    with gzip.open(ROOT / 'data/raw/transfermarkt_publisher/2026-10-10/clubs.csv.gz', 'rt', encoding='utf-8') as handle:
        for club in csv.DictReader(handle):
            league = COMPETITIONS.get(club['domestic_competition_id'])
            label = aliases.get(league, {}).get(club['name'], club['name'])
            if (league, label) in teams:
                matched[league, label] = club
                # Alternate source spelling for the same already mapped club.
                if league == 'Bundesliga' and label == 'Gladbach' and ('Bundesliga', "M'Gladbach") in teams:
                    matched[league, "M'Gladbach"] = club
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {
        'purpose': 'Owner-requested private explorer club identity illustrations',
        'historical_edition_policy': 'Illustrative club logos; exact season editions not established',
        'identity_method': 'Existing reviewed league/club aliases, publisher club_id, Wikidata P7223 exact match',
        'assets': [], 'coverage': []}
    for asset in manifest['assets']:
        if digest((ROOT / asset['path']).read_bytes()) != asset['sha256']:
            raise ValueError('Registered asset hash changed')
    if '--record-rate-limit' in sys.argv:
        manifest['acquisition_stopped_due_to_http_429'] = True
        manifest['rate_limit_event'] = {'source_host': 'upload.wikimedia.org',
            'reported_at_utc': datetime.now(timezone.utc).isoformat(),
            'observation': 'Initial acquisition returned HTTP 429 after five club assets.',
            'action': 'Stopped. Generate coverage from already archived metadata only; no retries or route changes.'}
    query_path = ARCHIVE / 'wikidata_club_logos.json'
    ids = sorted({c['club_id'] for c in matched.values()})
    query = 'SELECT ?id ?club ?logo WHERE { VALUES ?id { ' + ' '.join('"' + i + '"' for i in ids) + ' } ?club wdt:P7223 ?id. OPTIONAL { ?club wdt:P154 ?logo } }'
    query_url = 'https://query.wikidata.org/sparql?' + urllib.parse.urlencode({'query': query, 'format': 'json'})
    if not query_path.exists():
        archive(query_path, get(query_url))
    manifest['wikidata_query'] = {'source_url': query_url, 'path': query_path.relative_to(ROOT).as_posix(),
                                 'sha256': digest(query_path.read_bytes()), 'license': 'CC0 structured data',
                                 'retrieved_at_utc': datetime.fromtimestamp(query_path.stat().st_mtime, timezone.utc).isoformat()}
    candidates = {}
    for binding in json.loads(query_path.read_bytes())['results']['bindings']:
        item = candidates.setdefault(binding['id']['value'], {'qid': binding['club']['value'].rsplit('/', 1)[1], 'titles': []})
        if 'logo' in binding:
            title = 'File:' + urllib.parse.unquote(binding['logo']['value'].split('Special:FilePath/', 1)[1])
            item['titles'].append(title)
    # A researched 2017 edition avoids the current white pictogram for Juventus.
    if '506' in candidates:
        candidates['506']['titles'].insert(0, 'File:Juventus FC - logo black (Italy, 2017).svg')
    title_set = sorted({t for c in candidates.values() for t in c['titles']})
    metadata = {}
    manifest['metadata_archives'] = []
    for start in range(0, len(title_set), 40):
        meta_path = ARCHIVE / ('commons_metadata_' + str(start // 40) + '.json')
        url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode({
            'action': 'query', 'format': 'json', 'titles': '|'.join(title_set[start:start + 40]),
            'prop': 'imageinfo', 'iiprop': 'url|extmetadata', 'redirects': '1'})
        if not meta_path.exists():
            archive(meta_path, get(url)); time.sleep(1)
        result = json.loads(meta_path.read_bytes())
        manifest['metadata_archives'].append({'path': meta_path.relative_to(ROOT).as_posix(),
            'source_url': url, 'sha256': digest(meta_path.read_bytes()),
            'retrieved_at_utc': datetime.fromtimestamp(meta_path.stat().st_mtime, timezone.utc).isoformat()})
        by_title = {p['title']: p for p in result['query']['pages'].values()}
        redirects = {p['from']: p['to'] for p in result['query'].get('redirects', [])}
        for title in title_set[start:start + 40]:
            metadata[title] = by_title.get(redirects.get(title, title))
    stopped = manifest.get('acquisition_stopped_due_to_http_429', False) or '--metadata-only' in sys.argv
    manifest['coverage'] = []
    for league, label in sorted(teams):
        club = matched.get((league, label))
        entry = {'league': league, 'team': label, 'status': 'club_identity_unresolved'}
        if club:
            entry['publisher_club_id'] = club['club_id']
            entry['publisher_name'] = club['name']
            entry['publisher_source_url'] = club['url']
            candidate = candidates.get(club['club_id'])
            if not candidate:
                entry['status'] = 'wikidata_exact_id_not_found'
            else:
                entry['wikidata_id'] = candidate['qid']
                existing = next((a for a in manifest['assets'] if a['publisher_club_id'] == club['club_id']), None)
                if not existing:
                    pages = [(t, metadata.get(t)) for t in candidate['titles']]
                    pages = [(t, p) for t, p in pages if p and p.get('imageinfo')]
                    # Prefer dark/full logos; white variants disappear on the light UI.
                    pages.sort(key=lambda pair: ('white' in pair[0].lower(), 'pictogram' in pair[0].lower()))
                    if pages and not stopped:
                        title, page = pages[0]
                        info = page['imageinfo'][0]
                        url = info['url']
                        path = ARCHIVE / (club['club_id'] + Path(urllib.parse.urlparse(url).path).suffix)
                        try:
                            payload = path.read_bytes() if path.exists() else get(url)
                        except urllib.error.HTTPError as error:
                            if error.code != 429:
                                raise
                            stopped = True
                            manifest['acquisition_stopped_due_to_http_429'] = True
                            manifest['rate_limit_event'] = {'source_url': url,
                                'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                                'action': 'Stop asset downloads. No retries or alternate routes.'}
                            MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                            entry['status'] = 'rate_limited_asset_not_downloaded'
                            manifest['coverage'].append(entry)
                            continue
                        archive(path, payload)
                        ext = info.get('extmetadata', {})
                        existing = {'id': 'club-' + club['club_id'], 'kind': 'club',
                            'publisher_club_id': club['club_id'], 'wikidata_id': candidate['qid'],
                            'label': club['name'], 'title': title, 'source_page': info['descriptionurl'],
                            'source_url': url, 'path': path.relative_to(ROOT).as_posix(),
                            'sha256': digest(payload), 'bytes': len(payload),
                            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                            'license': plain(ext.get('LicenseShortName', {}).get('value', 'No open license verified')),
                            'license_url': ext.get('LicenseUrl', {}).get('value', ''),
                            'artist': plain(ext.get('Artist', {}).get('value', 'See source page')),
                            'historical_season_accuracy': 'Illustrative edition; not verified for every selected season',
                            'trademark_notice': 'Club marks may be trademarked; source license is not trademark clearance',
                            'display_changes': 'CSS contain only; raw unchanged'}
                        manifest['assets'].append(existing)
                        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
                        print('Archived', club['club_id'], club['name'], flush=True)
                        time.sleep(1)
                entry['status'] = 'available' if existing else ('download_paused_rate_limit' if pages and stopped else 'no_commons_logo_recorded')
                if existing:
                    entry['asset_id'] = existing['id']
        manifest['coverage'].append(entry)
    # Repeated runs regenerate coverage, while assets and raw archive stay immutable.
    manifest['coverage'] = list({(r['league'], r['team']): r for r in manifest['coverage']}.values())
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    report = ROOT / 'reports/explorer_club_assets_coverage.csv'
    fields = ['league', 'team', 'status', 'publisher_club_id', 'publisher_name', 'publisher_source_url', 'wikidata_id', 'asset_id']
    with report.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(manifest['coverage'])
    print('Club labels:', len(teams), 'available:', sum(r['status'] == 'available' for r in manifest['coverage']))


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise SystemExit('Provider rate limit: acquisition stopped; no retries or bypass.') from error
        raise
