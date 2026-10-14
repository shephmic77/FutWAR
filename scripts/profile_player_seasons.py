"""Additional player-season checks for the explicitly configured first source.

All outputs are audit evidence, not cleaned data. Source cells remain untouched.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
if __package__:
    from .audit_data import LEAGUES, SEASONS, read_json, write_csv
else:
    from audit_data import LEAGUES, SEASONS, read_json, write_csv


def profile(path, output, config):
    settings = {**config, **config['files'][path.name]}
    nulls = set(settings.get('null_tokens', ['']))
    decimal = settings.get('decimal', '.')
    with path.open(encoding=settings.get('encoding', 'utf-8-sig'), newline='') as handle:
        reader = csv.DictReader(handle, delimiter=settings['delimiter'])
        rows = list(reader)
        header = reader.fieldnames
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError('Resolve malformed CSV records before player-season profiling')
    text_columns = {'league', 'season', 'team', 'player', 'nation_', 'pos_'}
    def number(value):
        value = value.strip()
        if value in nulls:
            return None
        try:
            parsed = Decimal(value.replace(decimal, '.'))
            return parsed if parsed.is_finite() else 'invalid'
        except InvalidOperation:
            return 'invalid'
    numeric = []
    for column in header:
        if column in text_columns:
            continue
        values = [number(r[column]) for r in rows]
        valid = [v for v in values if isinstance(v, Decimal)]
        numeric.append({'column': column, 'non_null': sum(v is not None for v in values),
                        'invalid_numeric': values.count('invalid'),
                        'minimum': str(min(valid)) if valid else '',
                        'maximum': str(max(valid)) if valid else ''})
    grouped = defaultdict(list)
    for index, row in enumerate(rows, start=2):
        grouped[tuple(row[k] for k in settings['key_columns'])].append((index, row))
    conflicts = []
    for key, entries in grouped.items():
        if len(entries) < 2:
            continue
        varying = [c for c in header if len({r[c] for _, r in entries}) > 1]
        conflicts.append({'key': dict(zip(settings['key_columns'], key)), 'rows': len(entries),
                          'csv_record_numbers_including_header': [i for i, _ in entries],
                          'conflicting_columns': varying,
                          'policy': 'unresolved; preserve all raw records; do not arbitrarily choose a row'})
    candidate_metrics = ['Playing Time_Min', 'Performance_G-PK', 'Expected_npxG', 'Expected_xA',
                         'Expected_xAG', 'KP_', 'Progression_PrgP', 'Progression_PrgC',
                         'Tackles_Tkl', 'Int_', 'Blocks_Blocks', 'Performance_Recov',
                         'Aerial Duels_Won', 'Carries_Dis', 'Carries_Mis',
                         'Performance_CrdY', 'Performance_CrdR']
    by_target = defaultdict(list)
    for r in rows:
        league = settings['league_aliases'].get(r['league'], r['league'])
        season = settings['season_aliases'].get(r['season'], r['season'])
        by_target[(league, season)].append(r)
    coverage = []
    metrics = []
    for league in LEAGUES:
        for season in SEASONS:
            subset = by_target[(league, season)]
            coverage.append({'league': league, 'season': season, 'rows': len(subset),
                             'team_labels': len({r['team'] for r in subset}),
                             'player_names': len({r['player'] for r in subset}),
                             'goalkeeper_rows': sum(r['pos_'] == 'GK' for r in subset),
                             'unknown_position_rows': sum(r['pos_'].strip() in nulls for r in subset)})
            for metric in candidate_metrics:
                missing = sum(r.get(metric, '').strip() in nulls for r in subset)
                metrics.append({'league': league, 'season': season, 'column': metric,
                                'rows': len(subset), 'missing': missing,
                                'missing_pct': round(100 * missing / len(subset), 4) if subset else '',
                                'availability': 'no_observed_rows' if not subset else 'column_absent' if metric not in header else 'all_missing' if missing == len(subset) else 'partial' if missing else 'populated'})
    violations = Counter()
    for r in rows:
        minutes, matches, starts, nineties = [number(r[c]) for c in ['Playing Time_Min', 'Playing Time_MP', 'Playing Time_Starts', 'Playing Time_90s']]
        if isinstance(minutes, Decimal) and minutes < 0:
            violations['negative_minutes'] += 1
        if isinstance(matches, Decimal) and isinstance(starts, Decimal) and starts > matches:
            violations['starts_exceed_appearances'] += 1
        # The 90s column is displayed at one decimal place; allow its rounding error.
        if isinstance(minutes, Decimal) and isinstance(nineties, Decimal) and abs(minutes / 90 - nineties) > Decimal('0.051'):
            violations['minutes_vs_90s_rounding_mismatch'] += 1
    paired = []
    for left, right in [('Performance_Gls','Standard_Gls'),('Performance_Ast','Ast_'),
                        ('Expected_xAG','xAG_'),('Progression_PrgP','PrgP_'),
                        ('Progression_PrgC','Carries_PrgC'),('Playing Time_90s','90s_'),
                        ('Tackles_TklW','Performance_TklW'),('Int_','Performance_Int')]:
        comparable = mismatches = 0
        for r in rows:
            a, b = number(r[left]), number(r[right])
            if isinstance(a, Decimal) and isinstance(b, Decimal):
                comparable += 1
                mismatches += a != b
        paired.append({'left_column': left, 'right_column': right,
                       'comparable_rows': comparable, 'unequal_rows': mismatches})
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output/'numeric_quality.csv', ['column','non_null','invalid_numeric','minimum','maximum'], numeric)
    write_csv(output/'player_season_coverage.csv', ['league','season','rows','team_labels','player_names','goalkeeper_rows','unknown_position_rows'], coverage)
    write_csv(output/'candidate_stat_coverage.csv', ['league','season','column','rows','missing','missing_pct','availability'], metrics)
    write_csv(output/'related_column_checks.csv', ['left_column','right_column','comparable_rows','unequal_rows'], paired)
    result = {'source_file': path.name, 'decimal_separator': decimal,
              'conflicting_key_groups': conflicts, 'numeric_constraint_violations': dict(violations),
              'numeric_parse_failures': sum(r['invalid_numeric'] for r in numeric),
              'row_grain': 'apparent player-team-season; names are not stable identifiers',
              'checks_are_not_a_completeness_certificate': True}
    (output/'player_season_checks.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'conflict_groups': len(conflicts), 'conflicting_rows': sum(c['rows'] for c in conflicts),
                      'numeric_parse_failures': result['numeric_parse_failures'],
                      'constraint_violations': dict(violations), 'target_coverage': coverage,
                      'paired_column_checks': paired}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('data/raw/Top5_League_Players_2017to2024_dataset.csv'))
    parser.add_argument('--output', type=Path, default=Path('reports'))
    parser.add_argument('--config', type=Path, default=Path('audit_config.json'))
    args = parser.parse_args()
    if args.output.resolve() == args.input.resolve().parent or args.input.resolve().parent in args.output.resolve().parents:
        parser.error('Output must be outside the source directory')
    profile(args.input, args.output, read_json(args.config))
