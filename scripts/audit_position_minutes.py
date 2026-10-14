"""Reconstruct second-resolution position exposure; preserve source endpoints."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_position_boundaries import clock_seconds, inspect_boundaries
from audit_position_pilot import write_csv

ROOT = Path(__file__).resolve().parents[1]
PERIOD_BASE = {1: 0, 2: 45 * 60}


def period_clock(events):
    periods = {e['period'] for e in events}
    if periods != {1, 2}:
        raise ValueError('Only audited two-half league matches are supported')
    ends = {}
    for period in sorted(periods):
        values = {e['minute'] * 60 + e['second'] - PERIOD_BASE[period]
                  for e in events if e['period'] == period and e['type']['name'] == 'Half End'}
        if len(values) != 1 or next(iter(values)) < 45 * 60:
            raise ValueError('Missing, inconsistent or short period endpoint')
        ends[period] = values.pop()
    return ends


def elapsed(period, nominal_seconds, ends):
    local = nominal_seconds - PERIOD_BASE[period]
    if not 0 <= local <= ends[period]:
        raise ValueError('Clock outside recorded period')
    return sum(ends[p] for p in ends if p < period) + local


def interval_totals(intervals):
    intervals = sorted(intervals)
    total, overlap = 0, 0
    previous_end = None
    for start, end in intervals:
        if end < start:
            raise ValueError('Reversed interval')
        total += end - start
        if previous_end is not None:
            overlap += max(0, min(previous_end, end) - start)
        previous_end = max(previous_end or 0, end)
    return total, overlap


def appearance_intervals(events, ends):
    active, intervals, flags = {}, defaultdict(list), []
    for event in sorted(events, key=lambda e: e['index']):
        kind, team = event['type']['name'], event.get('team', {}).get('id')
        changes = []
        if kind == 'Starting XI':
            changes = [('on', p['player']['id']) for p in event['tactics']['lineup']]
        elif kind == 'Substitution':
            changes = [('off', event['player']['id']), ('on', event['substitution']['replacement']['id'])]
        elif kind in ['Player Off', 'Player On']:
            changes = [('off' if kind == 'Player Off' else 'on', event['player']['id'])]
        for action, player in changes:
            key = (team, player)
            point = elapsed(event['period'], event['minute'] * 60 + event['second'], ends)
            if action == 'on':
                if key in active:
                    flags.append((key, 'entry_while_already_active'))
                else:
                    active[key] = point
            elif key not in active:
                flags.append((key, 'exit_without_active_entry'))
            else:
                intervals[key].append((active.pop(key), point))
    final = sum(ends.values())
    for key, start in active.items():
        intervals[key].append((start, final))
    return intervals, flags


def inspect_minutes(events, lineups, match_id):
    ends = period_clock(events)
    boundaries = {(r['team_id'], r['player_id'], r['spell_index'], r['side']): r
                  for r in inspect_boundaries(events, lineups, match_id)}
    exposure, transitions = appearance_intervals(events, ends)
    spells, players = [], []
    for team in lineups:
        for player in team['lineup']:
            key = (team['team_id'], player['player_id'])
            if not player.get('positions') and key not in exposure:
                continue
            intervals, unresolved, by_position = [], 0, Counter()
            for index, spell in enumerate(player.get('positions', [])):
                start_row = boundaries[(*key, index, 'start')]
                end_row = boundaries[(*key, index, 'end')]
                seconds, status = None, 'unresolved_boundary'
                if start_row['status'] == 'exact_event_match' and end_row['status'] in [
                        'exact_event_match', 'open_final_whistle_with_event_context']:
                    start = elapsed(spell['from_period'], clock_seconds(spell['from']), ends)
                    end = (sum(ends.values()) if end_row['status'].startswith('open_final') else
                           elapsed(spell['to_period'], clock_seconds(spell['to']), ends))
                    if end >= start:
                        seconds, status = end - start, 'same_provider_boundary_checked'
                        intervals.append((start, end))
                        by_position[spell['position']] += seconds
                    else:
                        status = 'reversed_interval'
                if seconds is None:
                    unresolved += 1
                spells.append({'match_id': match_id, 'team_id': key[0], 'player_id': key[1],
                    'player_name': player['player_name'], 'spell_index': index, 'position': spell['position'],
                    'position_seconds': seconds, 'status': status,
                    'source_from': spell.get('from'), 'source_to': spell.get('to'),
                    'derived_end_uses_final_whistle': end_row['status'].startswith('open_final')})
            total, overlap = interval_totals(intervals)
            appearance, _ = interval_totals(exposure.get(key, []))
            outside = sum((end - start) - sum(max(0, min(end, b) - max(start, a))
                                            for a, b in exposure.get(key, [])) for start, end in intervals)
            transition_flags = [flag for flagged_key, flag in transitions if flagged_key == key]
            valid = unresolved == 0 and overlap == 0 and outside == 0 and total == appearance and not transition_flags
            players.append({'match_id': match_id, 'team_id': key[0], 'player_id': key[1],
                'player_name': player['player_name'], 'event_appearance_seconds': appearance,
                'checked_position_seconds': total, 'difference_seconds': total - appearance,
                'overlap_seconds': overlap, 'outside_appearance_seconds': outside,
                'unresolved_spells': unresolved, 'transition_flags': json.dumps(transition_flags),
                'fully_reconciled': valid, 'position_seconds': json.dumps(dict(by_position), ensure_ascii=False)})
    return spells, players, ends


def main():
    manifest = json.loads((ROOT / 'data/position_pilot_manifest.json').read_bytes())
    files = {f['source_path']: f for f in manifest['files']}
    def read(source):
        item = files[source]
        payload = (ROOT / item['path']).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item['sha256']:
            raise ValueError('Source changed')
        return json.loads(payload)
    spells, players, periods = [], [], []
    for match in manifest['selected_matches']:
        identifier = match['match_id']
        s, p, ends = inspect_minutes(read(f'data/events/{identifier}.json'), read(f'data/lineups/{identifier}.json'), identifier)
        spells.extend(s)
        players.extend(p)
        periods.append({'match_id': identifier, 'first_half_seconds': ends[1], 'second_half_seconds': ends[2]})
    folder = ROOT / 'reports/position_source/pilot'
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(folder / 'position_minutes.csv', spells)
    write_csv(folder / 'position_minutes_reconciliation.csv', players)
    write_csv(folder / 'period_durations.csv', periods)
    summary = {'player_appearances': len(players), 'fully_reconciled': sum(p['fully_reconciled'] for p in players),
        'unresolved_spells': sum(p['unresolved_spells'] for p in players),
        'nonzero_exposure_differences': sum(p['difference_seconds'] != 0 for p in players),
        'overlap_seconds': sum(p['overlap_seconds'] for p in players),
        'outside_appearance_seconds': sum(p['outside_appearance_seconds'] for p in players),
        'clock_precision': 'Whole seconds from source minute/second; not exact physiological or ball-in-play time',
        'duration_convention': 'Include each half stoppage time, exclude halftime and Player Off/On gaps',
        'seasonal_roles_assigned': False, 'source_values_changed': False,
        'input_sha256': {f['path']: f['sha256'] for f in files.values()}}
    (folder / 'minutes_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
