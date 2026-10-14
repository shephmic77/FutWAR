"""Review candidate keys and keeper exposure; never merge statistics into FutWAR."""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reports/keeper_archive/vendor'))
import pandas as pd
import pyreadr

OUT = ROOT / 'reports/keeper_archive'
RAW = ROOT / 'data/raw/keeper_archive/2026-10-10'


def normalize(value):
    value = unicodedata.normalize('NFKD', str(value)).casefold()
    return ''.join(c for c in value if c.isalnum() and not unicodedata.combining(c))


def load_csv(name, advanced):
    df = pd.read_csv(RAW / name)
    df = df.rename(columns={f'Unnamed: {i}_level_0_{n}': n
        for i, n in [(1, 'Player'), (3, 'Pos'), (4, 'Squad'), (5, 'Comp'), (7, 'Born')]})
    df = df.loc[~(df.Player.eq('Player') & df.Comp.eq('Comp'))].copy()
    aliases = {'eng Premier League': 'Premier League', 'es La Liga': 'La Liga',
        'it Serie A': 'Serie A', 'de Bundesliga': 'Bundesliga', 'fr Ligue 1': 'Ligue 1'}
    if not df.Comp.isin(aliases).all():
        raise ValueError('Unknown competition')
    df.Comp = df.Comp.map(aliases)
    df['Season_End_Year'] = int(re.search(r'_(\d{4})-(\d{4})\.csv$', name)[2])
    mapping = {'Unnamed: 8_level_0_90s': 'nineties', 'Expected_PSxG': 'psxg',
        'Goals_GA': 'ga', 'Goals_OG': 'og', 'Expected_PSxG+/-': 'psxg_delta'} if advanced else {
        'Playing Time_Min': 'minutes', 'Playing Time_MP': 'appearances',
        'Unnamed: 11_level_0_90s': 'nineties', 'Performance_GA': 'ga',
        'Performance_W': 'wins', 'Performance_D': 'draws', 'Performance_L': 'losses'}
    df = df.rename(columns=mapping)
    for column in mapping.values():
        df[column] = pd.to_numeric(df[column], errors='coerce')
    return df


def main():
    manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    fingerprints = {}
    for file in manifest['files']:
        digest = hashlib.sha256((ROOT / file['path']).read_bytes()).hexdigest()
        if digest != file['sha256']:
            raise ValueError('Candidate source changed')
        fingerprints[file['path']] = digest
    local_path = ROOT / 'data/processed/exploration/player_team_seasons.csv'
    local = pd.read_csv(local_path)
    fingerprints[local_path.relative_to(ROOT).as_posix()] = hashlib.sha256(local_path.read_bytes()).hexdigest()
    evidence_path = RAW / 'factual_review.json'
    fingerprints[evidence_path.relative_to(ROOT).as_posix()] = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    index = {}
    for row in local.itertuples():
        key = (row.league, row.season, normalize(row.team_name), normalize(row.player_name))
        index.setdefault(key, []).append(int(row.output_record))
    pairs, issues, candidates = [], [], []
    club_minutes = []
    for source in ['release', 'repository', 'statsbomb', 'nextgen']:
        if source == 'nextgen':
            basic = load_csv('nextgen_goalkeeping_2024-2025.csv', False)
            advanced = load_csv('nextgen_advanced_goalkeeping_2024-2025.csv', True)
            key = ['Season_End_Year', 'Comp', 'Squad', 'Player', 'Born']
        else:
            basic = next(iter(pyreadr.read_r(str(RAW / f'{source}_big5_player_keepers.rds')).values()))
            advanced = next(iter(pyreadr.read_r(str(RAW / f'{source}_big5_player_keepers_adv.rds')).values()))
            basic = basic.rename(columns={'Min_Playing': 'minutes', 'MP_Playing': 'appearances',
                'Mins_Per_90': 'nineties', 'Mins_Per_90_Playing': 'nineties', 'GA': 'ga',
                'W': 'wins', 'D': 'draws', 'L': 'losses'})
            advanced = advanced.rename(columns={'Mins_Per_90': 'nineties', 'PSxG_Expected': 'psxg',
                'GA_Goals': 'ga', 'OG_Goals': 'og', 'PSxG+_per__minus__Expected': 'psxg_delta'})
            key = ['Season_End_Year', 'Comp', 'Squad', 'Url']
        basic = basic.loc[basic.Season_End_Year.between(2018, 2025)].copy()
        advanced = advanced.loc[advanced.Season_End_Year.between(2018, 2025)].copy()
        if basic.duplicated(key).any() or advanced.duplicated(key).any():
            raise ValueError('Ambiguous basic/advanced candidate key')
        joined = basic.merge(advanced, on=key, how='outer', suffixes=('_basic', '_advanced'), indicator=True, validate='one_to_one')
        comparable = joined.psxg.notna() & joined.psxg_delta.notna() & joined.ga_advanced.notna() & joined.og.notna()
        residual = (joined.psxg - (joined.ga_advanced - joined.og) - joined.psxg_delta).abs()
        pairs.append(dict(source=source, basic_rows=len(basic), advanced_rows=len(advanced),
            linked_rows=int(joined._merge.eq('both').sum()), basic_only=int(joined._merge.eq('left_only').sum()),
            advanced_only=int(joined._merge.eq('right_only').sum()),
            psxg_identity_comparable=int(comparable.sum()),
            psxg_identity_difference_over_015=int((comparable & residual.gt(0.15)).sum())))
        for row in joined.to_dict('records'):
            flags = []
            if row['_merge'] != 'both':
                flags.append('unpaired_basic_advanced')
            if pd.isna(row.get('psxg')):
                flags.append('missing_psxg')
            minutes = row.get('minutes')
            nineties = row.get('nineties_advanced')
            if pd.notna(minutes) and pd.notna(nineties) and abs(minutes / 90 - nineties) > 0.07:
                flags.append('keeper_minutes_vs_advanced_90s_disagree')
            if row.get('Pos_basic') != 'GK':
                flags.append('nominal_non_gk_keeper_record')
            wdl = [row.get(k) for k in ['wins', 'draws', 'losses']]
            if all(pd.notna(v) for v in wdl) and pd.notna(row.get('appearances')) and sum(wdl) > row['appearances']:
                flags.append('wdl_exceeds_appearances')
            if all(pd.notna(row.get(k)) for k in ['psxg', 'ga_advanced', 'og', 'psxg_delta']):
                if abs(row['psxg'] - (row['ga_advanced'] - row['og']) - row['psxg_delta']) > 0.15:
                    flags.append('reported_psxg_residual_arithmetic_review')
            year = int(row['Season_End_Year'])
            season = f'{year-1}-{str(year)[2:]}'
            player = row.get('Player_basic', row.get('Player'))
            match_key = (row['Comp'], season, normalize(row['Squad']), normalize(player))
            possible = index.get(match_key, [])
            candidates.append(dict(source=source, league=row['Comp'], season=season, squad=row['Squad'],
                player=player, candidate_records=possible,
                status='unverified_unique_name_club_candidate' if len(possible)==1 else ('ambiguous' if possible else 'no_exact_normalized_candidate')))
            if flags:
                issues.append(dict(source=source, league=row['Comp'], season=season, squad=row['Squad'],
                    player=player, url=row.get('Url'), minutes=minutes,
                    advanced_nineties=nineties, psxg=row.get('psxg'),
                    goals_against=row.get('ga_advanced'), own_goals=row.get('og'),
                    reported_psxg_delta=row.get('psxg_delta'), flags=flags))
        for (year, league, squad), cell in basic.groupby(['Season_End_Year', 'Comp', 'Squad']):
            club_minutes.append(dict(source=source, season=f'{year-1}-{str(year)[2:]}', league=league,
                squad=squad, keeper_minutes=float(cell.minutes.sum()), missing_minutes=int(cell.minutes.isna().sum())))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(pairs).to_csv(OUT / 'pair_reconciliation.csv', index=False)
    pd.DataFrame(club_minutes).to_csv(OUT / 'club_keeper_minutes.csv', index=False)
    def save(name, value):
        # pandas may expose NaNs; serialize them as null, not non-standard JSON.
        clean = json.loads(pd.Series([value]).to_json(orient='values'))[0]
        (OUT / name).write_text(json.dumps(clean, indent=2), encoding='utf-8')
    save('keeper_field_review.json', issues)
    save('keeper_identity_candidates.json', candidates)
    save('reconciliation_run.json', dict(source_fingerprints=fingerprints, pairs=pairs,
        issue_records=len(issues), identity_candidates=len(candidates),
        unique_unverified_candidates=sum(r['status']=='unverified_unique_name_club_candidate' for r in candidates),
        arithmetic_check='PSxG - (GA - OG) compared to reported residual; diagnostic only, not a formula adoption',
        rate_check_tolerance=0.07, statistics_merged=False, identities_confirmed=False))
    # Same-season overlap uses provisional name/club/birth-year candidates only.
    newer = load_csv('nextgen_advanced_goalkeeping_2023-2024.csv', True)
    older = next(iter(pyreadr.read_r(str(RAW / 'release_big5_player_keepers_adv.rds')).values()))
    older = older.loc[older.Season_End_Year.eq(2024)].rename(columns={'PSxG_Expected': 'psxg', 'GA_Goals': 'ga', 'OG_Goals': 'og', 'Mins_Per_90': 'nineties'})
    for frame in [newer, older]:
        frame['name_key'] = frame.Player.map(normalize)
        frame['club_key'] = frame.Squad.map(normalize)
        frame['birth_key'] = pd.to_numeric(frame.Born, errors='coerce')
    overlap_key = ['Comp', 'name_key', 'club_key', 'birth_key']
    overlap = older.merge(newer, on=overlap_key, how='outer', suffixes=('_release', '_newer'), indicator=True, validate='one_to_one')
    overlap_report = []
    for metric in ['psxg', 'ga', 'og', 'nineties']:
        left, right = overlap[metric + '_release'], overlap[metric + '_newer']
        comparable = left.notna() & right.notna()
        difference = (left - right).abs()
        overlap_report.append(dict(metric=metric, comparable_records=int(comparable.sum()),
            equal_within_001=int((comparable & difference.le(0.01)).sum()),
            different_over_001=int((comparable & difference.gt(0.01)).sum()),
            max_absolute_difference=float(difference.max())))
    save('overlap_2023_24.json', dict(key_status='unverified_name_club_birth_year_candidates',
        release_rows=len(older), newer_rows=len(newer),
        linked_candidates=int(overlap._merge.eq('both').sum()),
        release_only=int(overlap._merge.eq('left_only').sum()), newer_only=int(overlap._merge.eq('right_only').sum()),
        metrics=overlap_report))
    overlap.to_csv(OUT / 'overlap_2023_24_review.csv', index=False)
    print('Reconciled four candidate pairs; review records:', len(issues))


if __name__ == '__main__':
    main()
