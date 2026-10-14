"""Populate the private inline layout review from existing analysis exports."""
import json
import re
import base64
import csv
import hashlib
import gzip
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    target = Path(sys.argv[1])
    data = json.loads((root / "reports/player_profile/data.json").read_text(encoding="utf-8"))
    players = []
    for name in ("Mohamed Salah", "Harry Kane"):
        matches = [r for r in data["records"] if r["name"] == name and r["season"] == "2017-18" and r["domain"] == "Outfield"]
        if len(matches) != 1:
            raise ValueError(f"Expected one source record for {name}, found {len(matches)}")
        players.append(matches[0])
    all_outfield = [r for r in data["records"] if r["domain"] == "Outfield"]
    clean_path = root / 'data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv'
    if hashlib.sha256(clean_path.read_bytes()).hexdigest() != '0f2ffe44ab175523ddcffaef71398356207ab4f81c7fbf6e7235b21e5d941297':
        raise ValueError('Audited original-source table changed')
    with clean_path.open(encoding='utf-8-sig', newline='') as handle:
        clean_rows = list(csv.DictReader(handle, delimiter=';'))
    annotations = json.loads((root / 'data/profile_display_annotations.json').read_text(encoding='utf-8'))['records']
    context_notes = json.loads((root / 'data/profile_context_notes.json').read_text(encoding='utf-8'))['records']
    identity_manifest = json.loads((root / 'data/player_identity_source_manifest.json').read_text(encoding='utf-8'))
    profiles_record = next(f for f in identity_manifest['files'] if f['filename'] == 'players.csv.gz')
    profiles_path = root / profiles_record['path']
    if hashlib.sha256(profiles_path.read_bytes()).hexdigest() != profiles_record['sha256']:
        raise ValueError('Profile archive differs from its manifest')
    with gzip.open(profiles_path, 'rt', encoding='utf-8', newline='') as handle:
        provider_profiles = {p['player_id']: p for p in csv.DictReader(handle)}
    candidates = {r['output_record']: r for r in csv.DictReader((root / 'reports/player_identity/identity_candidates.csv').open(encoding='utf-8-sig', newline=''))}
    coverage = []
    for record in all_outfield:
        original = clean_rows[int(record['id'].split(':')[1])-1]
        if tuple(original[k] for k in ('player','team','league','season')) != tuple(record[k] for k in ('name','team','league','season')):
            raise ValueError('Source record alignment differs')
        def number(field):
            value = original[field].strip()
            return float(value.replace(',','.')) if value else None
        if number('Playing Time_Min') != record['minutes']:
            raise ValueError('Source minutes differ')
        record['details'] = dict(appearances=number('Playing Time_MP'), starts=number('Playing Time_Starts'),
                                 age=original['age_'], birth_year=original['born_'], nationality=original['nation_'],
                                 goals=number('Performance_Gls'), assists=number('Performance_Ast'))
        context = context_notes.get(record['id'])
        if context:
            profile = provider_profiles[context['provider_player_id']]
            if not (profile['name'] == record['name'] == context['player_name'] and profile['date_of_birth'][:4] == original['born_'] == context['expected_birth_year'] and original['nation_'].split()[-1] == context['expected_nationality_code'] and profile['country_of_citizenship'] == context['expected_citizenship']):
                raise ValueError('Reviewed profile identity checks differ')
            record['profile_context'] = dict(context, height_cm=int(profile['height_in_cm']), foot=profile['foot'],
                                             profile_position=profile['sub_position'], birth_date=profile['date_of_birth'][:10],
                                             profile_snapshot_retrieved_at=profiles_record['retrieved_at_utc'])
        else:
            candidate = candidates.get(record['id'].split(':')[1])
            if candidate and tuple(candidate[k] for k in ('player_label', 'birth_year', 'league', 'season', 'team')) != (record['name'], original['born_'], record['league'], record['season'], record['team']):
                raise ValueError('Cached identity candidate alignment differs')
            if candidate and candidate['status'] == 'unique_candidate_with_historical_appearance':
                ids = candidate['candidate_provider_ids'].split('|')
                if len(ids) != 1:
                    raise ValueError('Expected a unique historical identity candidate')
                profile = provider_profiles[ids[0]]
                if profile['date_of_birth'][:4] != original['born_']:
                    raise ValueError('Candidate birth year differs')
                record['profile_context'] = dict(
                    height_cm=int(profile['height_in_cm']) if profile['height_in_cm'] else None,
                    foot=profile['foot'] or None, profile_position=profile['sub_position'] or None,
                    birth_date=profile['date_of_birth'][:10], profile_reference=profile['url'],
                    profile_snapshot_retrieved_at=profiles_record['retrieved_at_utc'],
                    identity_review='Provisional profile link: unique normalized full name and birth year, with historical club-season appearance evidence. Not a verified statistical identity merge; profile position is not the historical season role.')
        coverage.append(dict(record_id=record['id'], name=record['name'], league=record['league'], season=record['season'],
                             team=record['team'], profile_candidate=bool(record.get('profile_context')),
                             historical_main_position_verified=False))
        annotation = annotations.get(record['id'])
        if annotation:
            if (annotation['player_name'], annotation['team_name'], annotation['season']) != (record['name'],record['team'],record['season']):
                raise ValueError('Display annotation identity differs')
            record['display_position'] = annotation
    records = [r for r in all_outfield if r['season'] == '2017-18']
    players = [next(r for r in records if r['id'] == p['id']) for p in players]
    images = {i["id"]: i for i in data["images"]}
    crest_record = json.loads((root / 'data/layout_full_crest_manifest.json').read_text(encoding='utf-8'))
    crest = (root / crest_record['path']).read_bytes()
    if hashlib.sha256(crest).hexdigest() != crest_record['sha256']:
        raise ValueError('Crest source hash differs')
    # Columnar records and shared club context avoid repeating source metadata.
    metric_keys = list(records[0]['metrics'])
    detail_keys = list(records[0]['details'])
    teams = {}
    rows = []
    for r in records:
        team_key = r['league'] + '|' + r['team']
        teams[team_key] = r['team_context']
        rows.append([r['id'], r['name'], r['team'], r['league'], r['position'], r['minutes'],
                     [r['metrics'].get(k) for k in metric_keys],
                     [r['details'].get(k) for k in detail_keys],
                     r.get('profile_context'), r.get('display_position')])
    compressed_rows = gzip.compress(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), mtime=0)
    payload = {"playerIds": [p['id'] for p in players], "compressedRows": base64.b64encode(compressed_rows).decode('ascii'),
               "metricKeys": metric_keys, "detailKeys": detail_keys, "teams": teams,
               "sourceLinks": records[0]['source_links'], "warnings": records[0]['warnings'],
               "portrait": images["salah-headshot"]["data_url"],
               "leagueLogos": {'Premier League': images['premier-league']['data_url']},
               "clubLogo": 'data:image/svg+xml;base64,' + base64.b64encode(crest).decode('ascii')}
    asset_manifest = root / 'data/layout_additional_assets.json'
    payload['clubLogos'] = {'Liverpool': payload['clubLogo']}
    payload['portraits'] = {'Mohamed Salah': payload['portrait']}
    data['images'] = [a for a in data['images'] if not (a['kind'] == 'club' and a['label'] == 'Liverpool')]
    data['images'].append(dict(id='liverpool-crest', kind='club', label='Liverpool', title='Liverpool club crest',
                               source_page='https://resources.premierleague.com/premierleague/badges/t14.svg',
                               artist='Liverpool Football Club', license='Rights retained; private preview; no open redistribution license verified',
                               license_url='', data_url=payload['clubLogo']))
    del payload['clubLogo'], payload['portrait']
    if asset_manifest.exists():
        for asset in json.loads(asset_manifest.read_text(encoding='utf-8'))['assets']:
            raw = (root / asset['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != asset['sha256']:
                raise ValueError('Additional asset differs from manifest')
            group = {'league': 'leagueLogos', 'club': 'clubLogos', 'portrait': 'portraits'}[asset['kind']]
            payload[group][asset['label']] = 'data:' + asset['mime'] + ';base64,' + base64.b64encode(raw).decode('ascii')
            data['images'].append(dict(asset, id='layout-'+asset['label'], data_url=payload[group][asset['label']]))
        payload['assetCredits'] = json.loads(asset_manifest.read_text(encoding='utf-8'))['assets']
        payload['assetCredits'].append({k: images['premier-league'][k] for k in ('label', 'source_page', 'artist', 'license', 'license_url')})
    for row in coverage:
        row['portrait_available'] = row['name'] in payload['portraits']
        row['club_crest_available'] = row['team'] in payload['clubLogos']
        row['league_logo_available'] = row['league'] in payload['leagueLogos']
        row['injury_history_complete'] = False
        row['market_value_history_complete'] = False
        row['transfer_history_complete'] = False
    coverage_path = root / 'reports/player_profile/layout_enrichment_coverage.csv'
    with coverage_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(coverage[0]))
        writer.writeheader()
        writer.writerows(coverage)
    # Separate full-scope enriched export. Original analysis export stays immutable.
    (root / 'reports/player_profile/enriched_data.json').write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    summary = dict(total_export_records=len(data['records']), audited_outfield_records=len(coverage),
                   profile_candidates=sum(r['profile_candidate'] for r in coverage),
                   league_season_cells=len({(r['league'], r['season']) for r in coverage}),
                   fields={k: sum(r[k] for r in coverage) for k in ('portrait_available', 'club_crest_available', 'league_logo_available', 'historical_main_position_verified', 'injury_history_complete', 'market_value_history_complete', 'transfer_history_complete')},
                   limitations=['Profile links remain provisional except previously reviewed examples.', 'Profile positions are current archive attributes, not validated seasonal main positions.', 'Keeper rows retain existing data; this pass enriches outfield source rows.', 'Original export already focuses on 900+ minutes. Preview remains 2017-18; the standalone export contains all eight seasons.'])
    (root / 'reports/player_profile/enrichment_run.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    standalone = (root / 'profile/index.html').read_text(encoding='utf-8')
    standalone = standalone.replace('<link rel="stylesheet" href="style.css">', '<style>' + (root / 'profile/style.css').read_text(encoding='utf-8') + '</style>')
    standalone = standalone.replace('<script src="app.js"></script>', '<script type="application/json" id="profile-data">' + json.dumps(data, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c') + '</script><script>' + (root / 'profile/app.js').read_text(encoding='utf-8') + '</script>')
    (root / 'reports/player_profile/FutWAR_Player_Explorer_Enriched.html').write_text(standalone, encoding='utf-8')
    template = root / "profile/layout_review.html"
    markup = template.read_text(encoding="utf-8")
    if markup.count("__FW_DATA__") != 1:
        raise ValueError("Expected one unpopulated data marker")
    markup = markup.replace("__FW_DATA__", json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace("<", "\\u003c"))
    if len(markup.encode("utf-8")) >= 1_000_000:
        raise ValueError("Inline review exceeds size budget")
    target.write_text(markup, encoding="utf-8")
    javascript = re.findall(r"<script>(.*?)</script>", markup, flags=re.S)[0]
    (root / "reports/layout_review_check.js").write_text(javascript, encoding="utf-8")
    print(f"Populated review: {len(players)} examples, {len(records)} searchable outfield records, {target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
