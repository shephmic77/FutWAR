"""Audit source-recorded position spells without choosing seasonal player roles."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect_match(events, lineups, match_id):
    event_ids = [event['id'] for event in events]
    if len(set(event_ids)) != len(event_ids):
        raise ValueError('Duplicate event identifiers')
    starters, entrants = {}, set()
    snapshots = []
    for event in events:
        kind = event['type']['name']
        team = event.get('team', {}).get('id')
        if kind in ('Starting XI', 'Tactical Shift'):
            for member in event['tactics']['lineup']:
                key = (team, member['player']['id'])
                if kind == 'Starting XI':
                    if key in starters:
                        raise ValueError('Duplicate starting player')
                    starters[key] = member['position']['id']
                snapshots.append({'match_id': match_id, 'event_id': event['id'],
                    'event_type': kind, 'team_id': team, 'player_id': key[1],
                    'period': event['period'], 'minute': event['minute'], 'second': event['second'],
                    'position_id': member['position']['id'], 'position': member['position']['name'],
                    'formation': event['tactics']['formation']})
        elif kind == 'Substitution':
            entrants.add((team, event['substitution']['replacement']['id']))
    played = set(starters) | entrants
    spells, players, flags = [], [], []
    seen = set()
    for team in lineups:
        for player in team['lineup']:
            key = (team['team_id'], player['player_id'])
            if key in seen:
                raise ValueError('Duplicate lineup player')
            seen.add(key)
            positions = player.get('positions', [])
            if positions and key not in played:
                flags.append({'match_id': match_id, 'player_id': key[1],
                    'flag': 'position_spells_without_start_or_substitution_evidence'})
            if key in played and not positions:
                flags.append({'match_id': match_id, 'player_id': key[1], 'flag': 'appearance_without_position_spells'})
            if key in starters and positions and positions[0]['position_id'] != starters[key]:
                flags.append({'match_id': match_id, 'player_id': key[1], 'flag': 'starting_position_disagreement'})
            players.append({'match_id': match_id, 'team_id': key[0], 'player_id': key[1],
                'player_name': player['player_name'], 'starter': key in starters,
                'substitution_entrant': key in entrants, 'appearance_evidenced': key in played,
                'position_spells': len(positions),
                'distinct_position_ids': len({p['position_id'] for p in positions})})
            for index, position in enumerate(positions):
                if not 1 <= position['position_id'] <= 25:
                    flags.append({'match_id': match_id, 'player_id': key[1], 'flag': 'unknown_position_id'})
                spells.append({'match_id': match_id, 'team_id': key[0], 'player_id': key[1],
                    'player_name': player['player_name'], 'spell_index': index,
                    'position_id': position['position_id'], 'position': position['position'],
                    'from': position.get('from'), 'to': position.get('to'),
                    'from_period': position.get('from_period'), 'to_period': position.get('to_period'),
                    'start_reason': position.get('start_reason'), 'end_reason': position.get('end_reason'),
                    'evidence_status': 'provider_recorded_spell; not_independently_verified'})
    for key in played - seen:
        flags.append({'match_id': match_id, 'player_id': key[1], 'flag': 'appearing_player_absent_from_lineups'})
    summary = {'match_id': match_id, 'starting_players': len(starters),
        'substitution_entrants': len(entrants - set(starters)), 'appearance_players': len(played),
        'listed_players': len(players), 'unused_listed_players': sum(not p['appearance_evidenced'] for p in players),
        'position_spells': len(spells), 'multi_position_appearances': sum(
            p['appearance_evidenced'] and p['distinct_position_ids'] > 1 for p in players),
        'flags': len(flags)}
    return summary, spells, players, snapshots, flags


def write_csv(path, rows, empty_fields=None):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else empty_fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = json.loads((ROOT / 'data/position_pilot_manifest.json').read_bytes())
    files = {f['source_path']: f for f in manifest['files']}
    def read(source):
        item = files[source]
        payload = (ROOT / item['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item['sha256']:
            raise ValueError('Pilot input hash changed')
        return json.loads(payload)
    collections = [[], [], [], [], []]
    for match in manifest['selected_matches']:
        match_id = match['match_id']
        result = inspect_match(read(f'data/events/{match_id}.json'),
                               read(f'data/lineups/{match_id}.json'), match_id)
        collections[0].append(result[0])
        for target, rows in zip(collections[1:], result[1:]):
            target.extend(rows)
    summaries, spells, players, snapshots, flags = collections
    folder = ROOT / 'reports/position_source/pilot'
    folder.mkdir(parents=True, exist_ok=True)
    for name, rows in zip(['match_audit', 'recorded_position_spells', 'appearance_audit',
                          'tactical_snapshots', 'flags'], collections):
        write_csv(folder / f'{name}.csv', rows, ['match_id', 'player_id', 'flag'])
    coverage = []
    for competition, season in sorted({(m['competition_id'], m['season_id']) for m in manifest['selected_matches']}):
        matches = read(f'data/matches/{competition}/{season}.json')
        club_counts = Counter(m[side]['home_team_name' if side == 'home_team' else 'away_team_name']
                              for m in matches for side in ['home_team', 'away_team'])
        coverage.append({'competition_id': competition, 'season_id': season,
            'listed_matches': len(matches), 'listed_clubs': len({
                m[side]['home_team_id' if side == 'home_team' else 'away_team_id']
                for m in matches for side in ['home_team', 'away_team']}),
            'most_featured_club': club_counts.most_common(1)[0][0],
            'most_featured_club_matches': club_counts.most_common(1)[0][1],
            'sample_matches': sum(m['competition_id'] == competition and m['season_id'] == season
                                  for m in manifest['selected_matches']),
            'complete_league_coverage_verified': False})
    summary = {'sample_matches': len(summaries), 'catalog_coverage': coverage,
        'appearance_players': sum(m['appearance_players'] for m in summaries),
        'unused_listed_players': sum(m['unused_listed_players'] for m in summaries),
        'position_spells': len(spells), 'multi_position_appearances': sum(m['multi_position_appearances'] for m in summaries),
        'position_spell_counts': dict(sorted(Counter(s['position'] for s in spells).items())),
        'flags': len(flags), 'seasonal_positions_assigned': False,
        'durations_inferred': False, 'provider_identity_merge_performed': False,
        'input_sha256': {f['path']: f['sha256'] for f in files.values()}}
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
