"""Inspect conflict evidence; diagnostic clock minutes never become keeper exposure."""
import hashlib
import json
import zipfile
from pathlib import Path

import pandas as pd
from reconcile_keeper_candidates import ROOT
import pyreadr


def main():
    fingerprints = {}
    manifest = json.loads((ROOT / 'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    sources = {}
    for item in manifest['files']:
        path = ROOT / item['path']
        if path.name in ['players.json', 'matches.zip']:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item['sha256']:
                raise ValueError('Wyscout source changed')
            sources[path.name] = path
            fingerprints[item['path']] = digest
    players = json.loads(sources['players.json'].read_text(encoding='utf-8'))
    profile = [r for r in players if r['wyId'] == 25781]
    if len(profile) != 1 or profile[0]['firstName'] != 'Yohann' or profile[0]['birthDate'] != '1982-11-04':
        raise ValueError('Unexpected Pelé research profile')
    if profile[0]['lastName'].replace('\\u00e9', 'é') != 'Pelé':
        raise ValueError('Unexpected Pelé surname')
    with zipfile.ZipFile(sources['matches.zip']) as archive:
        matches = json.loads(archive.read('matches_France.json'))
    publisher_path = ROOT / 'reports/keeper_archive/playing_time_fixture_review.csv'
    fingerprints[publisher_path.relative_to(ROOT).as_posix()] = hashlib.sha256(publisher_path.read_bytes()).hexdigest()
    publisher = pd.read_csv(publisher_path)
    publisher = publisher.loc[publisher.player_name.eq('Yohann Pelé') & publisher.season.eq('2017-18')]
    if publisher.date.duplicated().any():
        raise ValueError('Multiple candidate fixtures on a date')
    by_date = publisher.set_index('date').to_dict('index')
    rows = []
    for match in matches:
        team = match['teamsData'].get('3771', {})
        formation = team.get('formation', {})
        started = any(r['playerId'] == 25781 for r in formation.get('lineup', []))
        substitutions = formation.get('substitutions') or []
        entered = [r['minute'] for r in substitutions if r['playerIn'] == 25781]
        exited = [r['minute'] for r in substitutions if r['playerOut'] == 25781]
        if not started and not entered:
            continue
        if len(entered) > 1 or len(exited) > 1 or match['duration'] != 'Regular':
            raise ValueError('Unsupported participation history')
        date = match['dateutc'][:10]
        comparison = by_date.get(date)
        if comparison is None:
            raise ValueError('Research appearance lacks a publisher date candidate')
        start = 0 if started else entered[0]
        end = exited[0] if exited else 90
        rows.append(dict(player_name='Yohann Pelé', season='2017-18', date=date,
            wyscout_match_id=match['wyId'], wyscout_label=match['label'],
            publisher_game_id=comparison['game_id'], publisher_url=comparison['fixture_url'],
            started=started, substitution_in_minute=entered[0] if entered else None,
            substitution_out_minute=exited[0] if exited else None,
            diagnostic_nominal_minutes=end-start, publisher_reported_minutes=comparison['reported_minutes'],
            minutes_difference=(end-start)-comparison['reported_minutes'],
            interpretation='Rounded substitution-clock diagnostic; not adopted keeper exposure'))
    if len(rows) != len(publisher):
        raise ValueError('Research and publisher appearance sets differ')
    keeper_manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    variant_rows = []
    for item in keeper_manifest['files']:
        path = ROOT / item['path']
        if path.suffix != '.rds' or not path.name.startswith(('release_', 'repository_', 'statsbomb_')):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item['sha256']:
            raise ValueError('Keeper archive changed')
        fingerprints[item['path']] = digest
        frame = next(iter(pyreadr.read_r(str(path)).values()))
        subset = frame.loc[frame.Player.eq('Yohann Pelé') & frame.Season_End_Year.eq(2018)]
        if len(subset) != 1:
            raise ValueError('Missing/ambiguous snapshot row')
        row = subset.iloc[0]
        def value(*keys):
            return next((row[k] for k in keys if k in row.index), None)
        variant_rows.append(dict(source_file=path.name, source_url=item['source_url'],
            appearances=value('MP_Playing'), minutes=value('Min_Playing'),
            reported_90s=value('Mins_Per_90', 'Mins_Per_90_Playing'),
            goals_against=value('GA_Goals', 'GA'), shots_on_target_against=value('SoTA'),
            saves=value('Saves'), psxg=value('PSxG_Expected')))
    output = ROOT / 'reports/keeper_archive'
    pd.DataFrame(rows).sort_values('date').to_csv(output / 'pele_research_fixture_comparison.csv', index=False)
    pd.DataFrame(variant_rows).to_csv(output / 'pele_snapshot_comparison.csv', index=False)
    summary = dict(input_sha256=fingerprints, research_appearances=len(rows),
        nominal_clock_minutes=sum(r['diagnostic_nominal_minutes'] for r in rows),
        publisher_minutes=sum(r['publisher_reported_minutes'] for r in rows),
        differing_fixture_minutes=sum(r['minutes_difference'] != 0 for r in rows),
        snapshot_rows=len(variant_rows), measurements_changed=False,
        limitations='Nominal 90-minute clock and rounded substitutions are diagnostics; no PSxG/match scope repaired.')
    (output / 'exposure_detail_lineage.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    for path, digest in fingerprints.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Input modified during detailed audit')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
