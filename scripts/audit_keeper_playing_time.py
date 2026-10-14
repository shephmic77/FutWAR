"""Compare four conflicting keeper seasons with immutable match appearances."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from reconcile_keeper_candidates import normalize

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('Yohann Pelé', 1982, 6270, 244, 'FR1', 2017),
    ('Francesco Rossi', 1991, 126634, 800, 'IT1', 2018),
    ('Will Norris', 1993, 285033, 543, 'GB1', 2018),
    ('Zion Suzuki', 2002, 432298, 130, 'IT1', 2024),
]


def main():
    manifest_path = ROOT / 'data/player_identity_source_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    selected = {}
    fingerprints = {}
    for item in manifest['files']:
        if item['filename'] in ['players.csv.gz', 'games.csv.gz', 'appearances.csv.gz']:
            path = ROOT / item['path']
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item['sha256']:
                raise ValueError('Publisher source changed')
            fingerprints[item['path']] = digest
            selected[item['filename']] = pd.read_csv(path)
    players = selected['players.csv.gz']
    games = selected['games.csv.gz']
    appearances = selected['appearances.csv.gz']
    audit_path = ROOT / 'reports/keeper_archive/staged_identity_candidates.csv'
    fingerprints[audit_path.relative_to(ROOT).as_posix()] = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    candidates = pd.read_csv(audit_path)
    summary, fixtures = [], []
    for name, born, player_id, club_id, competition, year in CASES:
        profile = players.loc[players.player_id.eq(player_id)]
        if len(profile) != 1 or normalize(profile.iloc[0]['name']) != normalize(name):
            raise ValueError('Unexpected candidate player identity')
        if pd.to_datetime(profile.iloc[0].date_of_birth).year != born:
            raise ValueError('Candidate birth year conflict')
        season = f'{year}-{str(year+1)[2:]}'
        candidate = candidates.loc[candidates.player_name.eq(name) & candidates.season.eq(season)]
        if len(candidate) != 1 or candidate.iloc[0].birth_year != born:
            raise ValueError('Missing or ambiguous local candidate')
        scope = games.loc[games.season.eq(year) & games.competition_id.eq(competition)]
        cell = appearances.loc[appearances.player_id.eq(player_id)
                               & appearances.player_club_id.eq(club_id)]
        cell = cell.merge(scope[['game_id', 'date', 'url']], on='game_id',
                          suffixes=('_appearance', '_fixture'), validate='many_to_one')
        if cell.game_id.duplicated().any() or cell.minutes_played.isna().any():
            raise ValueError('Duplicate fixture or missing minutes')
        if not cell.competition_id.eq(competition).all():
            raise ValueError('Competition mismatch')
        for fixture in cell.to_dict('records'):
            fixtures.append(dict(player_name=name, season=season, player_id=player_id,
                club_id=club_id, game_id=fixture['game_id'], date=fixture['date_fixture'],
                reported_minutes=fixture['minutes_played'], fixture_url=fixture['url'],
                status='publisher_appearance_candidate_not_official_minute_adjudication'))
        row = candidate.iloc[0]
        summary.append(dict(player_name=name, season=season, publisher_appearances=len(cell),
            publisher_minutes=int(cell.minutes_played.sum()),
            keeper_appearances=row.keeper_appearances, keeper_minutes=row.keeper_minutes,
            local_appearances=row.local_appearances, local_minutes=row.local_total_minutes,
            measurements_corrected=False))
    output = ROOT / 'reports/keeper_archive'
    pd.DataFrame(fixtures).to_csv(output / 'playing_time_fixture_review.csv', index=False)
    pd.DataFrame(summary).to_csv(output / 'playing_time_season_review.csv', index=False)
    (output / 'playing_time_lineage.json').write_text(json.dumps({
        'input_sha256': fingerprints,
        'cases': CASES,
        'interpretation': 'Corroborating publisher candidates only; no exact minute convention or keeper exposure adopted.',
    }, indent=2), encoding='utf-8')
    for path, digest in fingerprints.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Input modified during audit')
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == '__main__':
    main()
