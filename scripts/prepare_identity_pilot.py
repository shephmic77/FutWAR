"""Export only the explicitly researched five-player pilot; preserve every statistic."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
from audit_standings_and_identity import write_csv


def validate_link(local,candidate,review,profile):
    if local['player']!=review['name'] or local['born_']!=review['date_of_birth'][:4]:
        raise ValueError('Local record differs from reviewed name or birth year')
    if candidate['status']!='unique_candidate_with_historical_appearance' or candidate['candidate_provider_ids']!=review['provider_player_id']:
        raise ValueError('Pilot identity lacks unique historical appearance support')
    if profile['date_of_birth'][:10]!=review['date_of_birth'] or profile['name']!=review['name']:
        raise ValueError('Provider biography differs from researched identity')
    if not review['source_urls']:raise ValueError('Primary identity evidence is required')


def main():
    path=Path('data/raw/identity_reviews/pilot_2026-10-10.json')
    payload=path.read_bytes();review=json.loads(payload.decode('utf-8'))
    digest=hashlib.sha256(payload).hexdigest()
    local_path=Path('data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv')
    if hashlib.sha256(local_path.read_bytes()).hexdigest()!=review['processed_player_sha256']:
        raise ValueError('Processed input changed; re-review pilot')
    with local_path.open(encoding='utf-8-sig',newline='') as f:local=list(csv.DictReader(f,delimiter=';'))
    with Path('reports/player_identity/identity_candidates.csv').open(encoding='utf-8',newline='') as f:
        candidates={int(r['output_record']):r for r in csv.DictReader(f)}
    manifest=json.loads(Path('data/player_identity_source_manifest.json').read_text(encoding='utf-8'))
    source=next(r for r in manifest['files'] if r['filename']=='players.csv.gz')
    if hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()!=source['sha256']:
        raise ValueError('Provider profile snapshot changed')
    with gzip.open(source['path'],'rt',encoding='utf-8-sig',newline='') as f:
        profiles={r['player_id']:r for r in csv.DictReader(f)}
    people=[];links=[]
    for person in review['players']:
        profile=profiles[person['provider_player_id']]
        people.append(dict(provider_namespace='transfermarkt_publisher',provider_player_id=person['provider_player_id'],
            display_name=person['name'],date_of_birth=person['date_of_birth'],profile_url=profile['url'],
            provider_file_sha256=source['sha256'],review_sha256=digest,source_urls=json.dumps(person['source_urls']),
            reviewed_at=person['reviewed_at'],review_status=person['review_status']))
        for number in person['output_records']:
            validate_link(local[number-1],candidates[number],person,profile)
            links.append(dict(source_sha256=review['source_sha256'],output_record=number,
                provider_namespace='transfermarkt_publisher',provider_player_id=person['provider_player_id'],review_sha256=digest))
    if len({r['output_record'] for r in links})!=len(links):raise ValueError('Duplicate pilot link')
    write_csv(Path('data/processed/postgres/identity_pilot_players.csv'),people)
    write_csv(Path('data/processed/postgres/identity_pilot_links.csv'),links)
    print(json.dumps(dict(reviewed_pilot_players=len(people),reviewed_record_links=len(links),
        review_sha256=digest,statistics_modified=False),indent=2))


if __name__=='__main__':main()
