"""Measure candidate keeper coverage without merging provider generations."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reports/keeper_archive/vendor'))
import pandas as pd
import pyreadr

LEAGUES = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
OUT = ROOT / 'reports/keeper_archive'


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    coverage, metrics, review = [], [], []
    inventory = {}
    reference_path = ROOT / 'data/processed/exploration/team_results.csv'
    reference = pd.read_csv(reference_path)
    fixture_counts = reference.groupby(['league', 'season']).played.sum().div(2)
    if len(fixture_counts) != 40 or any(fixture_counts % 1):
        raise ValueError('Unexpected fixture benchmark coverage')
    for file in manifest['files']:
        path = ROOT / file['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != file['sha256']:
            raise ValueError('Candidate source hash changed')
        if not path.name.endswith(('.rds', '.csv')):
            continue
        header_rows = 0
        if path.name.endswith('.csv'):
            df = pd.read_csv(path)
            original_columns = list(df.columns)
            df = df.rename(columns={f'Unnamed: {i}_level_0_{name}': name
                for i, name in [(1, 'Player'), (3, 'Pos'), (4, 'Squad'), (5, 'Comp'), (7, 'Born')]})
            repeated = df.Comp.eq('Comp') & df.Player.eq('Player')
            header_rows = int(repeated.sum())
            df = df.loc[~repeated].copy()
            aliases = {'eng Premier League': 'Premier League', 'es La Liga': 'La Liga',
                'it Serie A': 'Serie A', 'de Bundesliga': 'Bundesliga', 'fr Ligue 1': 'Ligue 1'}
            if not df.Comp.isin(aliases).all():
                raise ValueError('Unrecognized CSV competition')
            df['Comp'] = df.Comp.map(aliases)
            # Season comes from the pinned source path, not an inferred player identity.
            season_match = re.search(r'_(\d{4})-(\d{4})\.csv$', path.name)
            if not season_match or int(season_match[2]) != int(season_match[1]) + 1:
                raise ValueError('Unrecognized source season filename')
            df['Season_End_Year'] = int(season_match[2])
            df = df.rename(columns={'Playing Time_Min': 'Min_Playing', 'Playing Time_MP': 'MP_Playing'})
            required = ['Season_End_Year', 'Comp', 'Squad', 'Player', 'Born']
            key = ['Season_End_Year', 'Comp', 'Squad', 'Player', 'Born']
        else:
            objects = pyreadr.read_r(str(path))
            if len(objects) != 1:
                raise ValueError('Unexpected RDS object count')
            df = next(iter(objects.values()))
            original_columns = list(df.columns)
            required = ['Season_End_Year', 'Comp', 'Squad', 'Player', 'Url']
            key = ['Season_End_Year', 'Comp', 'Squad', 'Url']
        if not all(c in df for c in required):
            raise ValueError('Unrecognized keeper schema')
        scoped = df[df.Season_End_Year.between(2018, 2025) & df.Comp.isin(LEAGUES)]
        inventory[path.name] = dict(rows=len(df), scoped_rows=len(scoped), columns=original_columns,
            repeated_header_rows=header_rows, candidate_key=key,
            exact_duplicate_rows=int(scoped.duplicated().sum()),
            duplicate_key_rows=int(scoped.duplicated(key, keep=False).sum()),
            source_sha256=file['sha256'])
        for _, row in scoped[scoped.duplicated(key, keep=False)].iterrows():
            review.append(dict(source=path.name, year=int(row.Season_End_Year),
                league=row.Comp, squad=row.Squad, player=row.Player, url=row.get('Url'), issue='duplicate_candidate_key'))
        for year in range(2018, 2026):
            for league in LEAGUES:
                cell = scoped[(scoped.Season_End_Year == year) & (scoped.Comp == league)]
                season = f'{year-1}-{str(year)[2:]}'
                fixture_count = int(fixture_counts.loc[(league, season)])
                minutes = pd.to_numeric(cell['Min_Playing'], errors='coerce').sum() if 'Min_Playing' in cell else None
                nineties = pd.to_numeric(cell['Mins_Per_90'], errors='coerce').sum() if 'Mins_Per_90' in cell else None
                coverage.append(dict(source=path.name, league=league, season=season, records=len(cell),
                    teams=cell.Squad.nunique(), missing_key_rows=int(cell[key].isna().any(axis=1).sum()),
                    duplicate_key_rows=int(cell.duplicated(key, keep=False).sum()),
                    recorded_minutes=minutes, recorded_90s=nineties,
                    benchmark_keeper_minutes=fixture_count*180,
                    minutes_to_benchmark_pct=round(minutes/(fixture_count*180)*100, 2) if minutes is not None else None,
                    status='absent' if cell.empty else 'observed_unverified', rights_status='unresolved'))
                for column in cell.columns:
                    if column in required:
                        continue
                    numeric = pd.to_numeric(cell[column], errors='coerce')
                    metrics.append(dict(source=path.name, league=league, season=season, metric=column,
                        records=len(cell), missing_records=int(cell[column].isna().sum()),
                        nonmissing_records=int(cell[column].notna().sum()),
                        numeric_records=int(numeric.notna().sum()), zero_records=int(numeric.eq(0).sum()),
                        minimum=numeric.min() if numeric.notna().any() else None,
                        maximum=numeric.max() if numeric.notna().any() else None))
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / 'coverage.csv', coverage)
    write_csv(OUT / 'metric_coverage.csv', metrics)
    (OUT / 'duplicate_review.json').write_text(json.dumps(review, indent=2), encoding='utf-8')
    (OUT / 'inventory.json').write_text(json.dumps(dict(files=inventory,
        reader_version=pyreadr.__version__, source_adopted=False, statistics_merged=False,
        benchmark_source=reference_path.relative_to(ROOT).as_posix(),
        benchmark_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        benchmark_note='Existing audited team results: summed team appearances/2; minutes can differ for rounding, outfield emergency keepers, and missing appearances.'), indent=2), encoding='utf-8')
    print('Audited', len(inventory), 'files;', len(coverage), 'source/league/season cells; duplicate review rows:', len(review))


if __name__ == '__main__':
    main()
