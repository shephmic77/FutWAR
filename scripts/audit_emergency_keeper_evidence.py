"""Review emergency keeper evidence without assigning season position labels."""
import hashlib
import json
import zipfile

from reconcile_keeper_candidates import ROOT
import pandas as pd


def main():
    manifest = json.loads((ROOT/'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    files, hashes = {}, {}
    for item in manifest['files']:
        path = ROOT/item['path']
        if path.name in ['players.json', 'matches.zip', 'events.zip']:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item['sha256']:
                raise ValueError('Research source changed')
            files[path.name] = path
            hashes[item['path']] = digest
    profiles = {r['wyId']: r for r in json.loads(files['players.json'].read_text(encoding='utf-8'))}
    cases = [('Brais Méndez', 302550, '1997-01-07', 'Spain'),
             ('Ibrahim Amadou', 28232, '1993-04-06', 'France'),
             ('Nicolas de Préville', 25923, '1991-01-08', 'France')]
    evidence, summary = [], []
    with zipfile.ZipFile(files['events.zip']) as event_archive, zipfile.ZipFile(files['matches.zip']) as match_archive:
        for country in ['France', 'Spain']:
            events = json.loads(event_archive.read(f'events_{country}.json'))
            matches = {r['wyId']: r for r in json.loads(match_archive.read(f'matches_{country}.json'))}
            for name, identifier, born, scope in cases:
                if scope != country:
                    continue
                profile = profiles[identifier]
                if profile['birthDate'] != born:
                    raise ValueError('Research identity birth date changed')
                selected = [r for r in events if r['playerId'] == identifier and r['eventId'] in [4,9]]
                for event in selected:
                    match = matches[event['matchId']]
                    evidence.append(dict(player_name=name, research_player_id=identifier,
                        match_id=event['matchId'], date=match['dateutc'][:10], match_label=match['label'],
                        event_id=event['id'], event_name=event['eventName'], period=event['matchPeriod'],
                        event_seconds=event['eventSec'],
                        interpretation='Keeper action evidence, not a successful-save count or exact keeper interval'))
                summary.append(dict(player_name=name, season='2017-18', keeper_action_events=len(selected),
                    keeper_action_matches=len({r['matchId'] for r in selected}),
                    status='keeper_action_corroborated' if selected else 'keeper_participation_unconfirmed',
                    seasonal_gk_label_assigned=False))
    summary.append(dict(player_name='Rúben Vezo', season='2021-22', keeper_action_events=None,
        keeper_action_matches=None, status='official_club_emergency_keeper_report', seasonal_gk_label_assigned=False))
    output = ROOT/'reports/keeper_archive'
    pd.DataFrame(evidence).to_csv(output/'emergency_keeper_events.csv', index=False)
    record = dict(input_sha256=hashes, player_reviews=summary,
        vezo_source_url='https://museo.levanteud.com/2025/12/01/ruben-vezo-el-central-portugues-que-durante-seis-campanas-lidero-la-defensa-granota/',
        interpretation='Observed keeper participation kept separate from 5-appearance/10-percent season labeling.',
        measurements_changed=False)
    (output/'emergency_keeper_review.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    for path, digest in hashes.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Input modified during emergency review')
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
