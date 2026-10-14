"""Reconcile recorded spell boundaries with same-provider events; no role rule."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from audit_position_pilot import write_csv

ROOT = Path(__file__).resolve().parents[1]


def clock_seconds(value):
    parts = value.split(':')
    if len(parts) != 2 or not all(p.isdigit() for p in parts) or int(parts[1]) >= 60:
        raise ValueError('Expected a nonnegative minute:second source clock')
    return int(parts[0]) * 60 + int(parts[1])


def boundary_candidates(events, team_id, player_id, reason, side, position_id):
    candidates = []
    for event in events:
        if event.get('team', {}).get('id') != team_id:
            continue
        kind = event['type']['name']
        member = event.get('player', {}).get('id') == player_id
        if reason == 'Starting XI' and side == 'start' and kind == 'Starting XI':
            if any(p['player']['id'] == player_id and p['position']['id'] == position_id
                   for p in event['tactics']['lineup']):
                candidates.append(event)
        elif reason == 'Tactical Shift' and kind == 'Tactical Shift':
            # Start must show the new role. End need only show the player in the snapshot.
            if any(p['player']['id'] == player_id and
                   (side == 'end' or p['position']['id'] == position_id)
                   for p in event['tactics']['lineup']):
                candidates.append(event)
        elif reason.startswith('Substitution - On') and side == 'start' and kind == 'Substitution':
            if event['substitution']['replacement']['id'] == player_id:
                candidates.append(event)
        elif reason.startswith('Substitution - Off') and side == 'end' and kind == 'Substitution' and member:
            candidates.append(event)
        elif reason.startswith('Player On') and side == 'start' and kind == 'Player On' and member:
            candidates.append(event)
        elif reason.startswith('Player Off') and side == 'end' and kind == 'Player Off' and member:
            candidates.append(event)
        elif reason == 'Final Whistle' and side == 'end' and kind == 'Half End':
            candidates.append(event)
    if reason == 'Final Whistle' and candidates:
        last_period = max(e['period'] for e in candidates)
        candidates = [e for e in candidates if e['period'] == last_period]
    return candidates


def inspect_boundaries(events, lineups, match_id):
    rows = []
    for team in lineups:
        for player in team['lineup']:
            for index, spell in enumerate(player.get('positions', [])):
                for side, endpoint in [('start', 'from'), ('end', 'to')]:
                    reason = spell[side + '_reason']
                    candidates = boundary_candidates(events, team['team_id'], player['player_id'],
                                                     reason, side, spell['position_id'])
                    value, period = spell.get(endpoint), spell.get(endpoint + '_period')
                    delta, matches = None, []
                    if value is None or period is None:
                        status = 'open_final_whistle_with_event_context' if (
                            value is None and period is None and reason == 'Final Whistle' and candidates
                        ) else 'missing_boundary'
                        matches = candidates if status.startswith('open_final') else []
                    else:
                        seconds = clock_seconds(value)
                        same_period = [e for e in candidates if e['period'] == period]
                        matches = [e for e in same_period if e['minute'] * 60 + e['second'] == seconds]
                        status = 'exact_event_match' if matches else 'unresolved_event_boundary'
                        if same_period:
                            nearest = min(same_period, key=lambda e: abs(e['minute'] * 60 + e['second'] - seconds))
                            delta = nearest['minute'] * 60 + nearest['second'] - seconds
                    rows.append({'match_id': match_id, 'team_id': team['team_id'],
                        'player_id': player['player_id'], 'player_name': player['player_name'],
                        'spell_index': index, 'position_id': spell['position_id'],
                        'side': side, 'reason': reason, 'source_clock': value,
                        'source_period': period, 'status': status,
                        'matching_event_ids': json.dumps([e['id'] for e in matches]),
                        'candidate_events': len(candidates), 'nearest_same_period_delta_seconds': delta})
    return rows


def main():
    manifest = json.loads((ROOT / 'data/position_pilot_manifest.json').read_bytes())
    files = {f['source_path']: f for f in manifest['files']}
    def read(source):
        item = files[source]
        payload = (ROOT / item['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item['sha256']:
            raise ValueError('Source hash mismatch')
        return json.loads(payload)
    rows, interval_flags = [], []
    for match in manifest['selected_matches']:
        identifier = match['match_id']
        events = read(f'data/events/{identifier}.json')
        lineups = read(f'data/lineups/{identifier}.json')
        rows.extend(inspect_boundaries(events, lineups, identifier))
        for team in lineups:
            for player in team['lineup']:
                for index, spell in enumerate(player.get('positions', [])):
                    if spell.get('from') is None or spell.get('to') is None:
                        continue
                    start = (spell['from_period'], clock_seconds(spell['from']))
                    end = (spell['to_period'], clock_seconds(spell['to']))
                    if end <= start:
                        interval_flags.append({'match_id': identifier, 'player_id': player['player_id'],
                            'player_name': player['player_name'], 'spell_index': index,
                            'position': spell['position'], 'flag': 'zero_length_recorded_spell' if end == start
                            else 'reversed_recorded_spell', 'source_from': spell['from'], 'source_to': spell['to']})
    folder = ROOT / 'reports/position_source/pilot'
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(folder / 'position_boundary_audit.csv', rows)
    unresolved = [r for r in rows if r['status'] in ['missing_boundary', 'unresolved_event_boundary']]
    write_csv(folder / 'unresolved_position_boundaries.csv', unresolved, list(rows[0]))
    write_csv(folder / 'position_interval_flags.csv', interval_flags,
              ['match_id', 'player_id', 'player_name', 'spell_index', 'position', 'flag', 'source_from', 'source_to'])
    summary = {'boundaries': len(rows), 'status_counts': dict(Counter(r['status'] for r in rows)),
        'unresolved_reason_counts': dict(Counter(r['reason'] for r in unresolved)),
        'interval_flag_counts': dict(Counter(r['flag'] for r in interval_flags)),
        'matching_policy': 'Exact minute/second AND period; no tolerance-based correction',
        'final_whistle_policy': 'Retain null endpoints; link final-period Half End events as context only',
        'durations_calculated': False, 'seasonal_counting_rule_selected': False,
        'input_sha256': {f['path']: f['sha256'] for f in files.values()}}
    (folder / 'boundary_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
