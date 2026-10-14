"""Measure lineup coverage and appearance links without assigning played positions."""
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_player_identity_source import CODES, read_rows
from audit_standings_and_identity import write_csv


def main():
    root = Path(__file__).resolve().parents[1]
    fingerprints = {}
    for name in ['player_identity_source_manifest.json', 'position_source_manifest.json']:
        manifest = json.loads((root / 'data' / name).read_text(encoding='utf-8'))
        for source in manifest['files']:
            if hashlib.sha256((root / source['path']).read_bytes()).hexdigest() != source['sha256']:
                raise ValueError('Archived source changed: ' + source['filename'])
            fingerprints[source['path']] = source['sha256']
        if 'semantics_review' in manifest:
            source = manifest['semantics_review']
            if hashlib.sha256((root / source['path']).read_bytes()).hexdigest() != source['sha256']:
                raise ValueError('Archived parser evidence changed')
            fingerprints[source['path']] = source['sha256']
    games = {}
    coverage = {}
    for league in CODES.values():
        for year in range(2017, 2025):
            season = f'{year}-{str(year + 1)[-2:]}'
            coverage[league, season] = Counter()
    for row in read_rows('games'):
        if row['competition_id'] in CODES and row['season'] in {str(y) for y in range(2017, 2025)}:
            cell = (CODES[row['competition_id']], f'{row["season"]}-{str(int(row["season"])+1)[-2:]}')
            games[row['game_id']] = (cell, row)
            coverage[cell]['games'] += 1
    profiles = {r['player_id']: r['sub_position'] for r in read_rows('players')}
    appearances = {}
    for row in read_rows('appearances'):
        if row['game_id'] not in games:
            continue
        key = (row['game_id'], row['player_id'], row['player_club_id'])
        if key in appearances:
            raise ValueError('Duplicate scoped appearance key')
        appearances[key] = row
        coverage[games[row['game_id']][0]]['appearance_records'] += 1
    links = defaultdict(list)
    types = Counter()
    positions = Counter()
    lineup_ids = set()
    game_lineup_games = set()
    starters = Counter()
    scoped_rows = 0
    profile_equal = 0
    profile_compared = 0
    total_rows = 0
    path = root / 'data/raw/transfermarkt_publisher/2026-10-10/game_lineups.csv.gz'
    with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames
        for row in reader:
            total_rows += 1
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Malformed lineup record')
            if row['game_id'] not in games:
                continue
            scoped_rows += 1
            cell, game = games[row['game_id']]
            stats = coverage[cell]
            stats['lineup_records'] += 1
            if row['game_lineups_id'] in lineup_ids:
                stats['duplicate_lineup_ids'] += 1
            lineup_ids.add(row['game_lineups_id'])
            game_lineup_games.add(row['game_id'])
            stats['missing_position_records'] += not bool(row['position'])
            stats['date_disagreements'] += row['date'] != game['date']
            stats['club_not_in_fixture'] += row['club_id'] not in [game['home_club_id'], game['away_club_id']]
            types[row['type']] += 1
            positions[row['position']] += 1
            stats['starting_lineup_records'] += row['type'] == 'starting_lineup'
            stats['bench_records'] += row['type'] == 'substitutes'
            if row['type'] == 'starting_lineup':
                starters[row['game_id'], row['club_id']] += 1
            profile = profiles.get(row['player_id'])
            if profile and row['position']:
                profile_compared += 1
                profile_equal += profile == row['position']
            links[row['game_id'], row['player_id'], row['club_id']].append((row['type'], row['position']))
    for game_id, (cell, game) in games.items():
        coverage[cell]['games_with_lineups'] += game_id in game_lineup_games
        coverage[cell]['games_with_two_11_player_starting_lists'] += all(
            starters[game_id, club] == 11 for club in [game['home_club_id'], game['away_club_id']])
    for key, appearance in appearances.items():
        stats = coverage[games[key[0]][0]]
        found = links.get(key, [])
        if not found:
            stats['appearances_without_lineup'] += 1
        elif len(found) > 1:
            stats['appearances_with_ambiguous_lineup'] += 1
        else:
            kind, position = found[0]
            stats['appearances_with_one_lineup'] += 1
            stats['appearances_with_one_populated_position'] += bool(position)
            stats['appeared_from_bench_records'] += kind == 'substitutes'
            stats['goalkeeper_labeled_appearances'] += position == 'Goalkeeper'
    for key, found in links.items():
        stats = coverage[games[key[0]][0]]
        if key not in appearances:
            stats['lineup_keys_without_appearance'] += 1
            stats['bench_keys_without_appearance'] += any(kind == 'substitutes' for kind, _ in found)
        if len(found) > 1:
            stats['repeated_game_player_club_keys'] += 1
    folder = root / 'reports/position_source'
    folder.mkdir(parents=True, exist_ok=True)
    fields = sorted({field for row in coverage.values() for field in row} | {
        'duplicate_lineup_ids', 'repeated_game_player_club_keys', 'appearances_with_ambiguous_lineup'})
    rows = [dict(league=cell[0], season=cell[1], **{field: stats[field] for field in fields},
                 played_position_semantics='not_verified', seasonal_labels_assigned=False)
            for cell, stats in sorted(coverage.items())]
    write_csv(folder / 'coverage.csv', rows)
    write_csv(folder / 'position_labels.csv', [dict(source_position=p, scoped_lineup_records=n) for p, n in sorted(positions.items())])
    totals = {field: sum(r[field] for r in rows) for field in fields}
    if totals['appearance_records'] != sum(totals[f] for f in [
        'appearances_with_one_lineup', 'appearances_without_lineup', 'appearances_with_ambiguous_lineup']):
        raise ValueError('Appearance reconciliation failed')
    if totals['lineup_records'] != sum(types.values()):
        raise ValueError('Lineup row accounting failed')
    summary = dict(all_source_lineup_rows=total_rows, scoped_lineup_rows=scoped_rows, scoped_totals=totals,
                   headers=headers, lineup_types=dict(types), position_vocabulary=dict(positions),
                   lineup_position_equal_to_current_profile=profile_equal, compared_to_current_profile=profile_compared,
                   interpretation='Profile agreement is a diagnostic, not proof of historical played-position meaning',
                   source_fingerprints=fingerprints,
                   secondary_position_rule_applied=False, goalkeeper_performance_fields_available=False)
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
