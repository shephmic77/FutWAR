"""Copy audited SQL views into a hashed local snapshot for exploratory notebooks."""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

from export_initial_eda import psql


def main():
    queries = {
        'player_team_seasons.csv': 'SELECT * FROM futwar.player_season_eda ORDER BY source_sha256,output_record;',
        'season_exposure.csv': 'SELECT * FROM futwar.season_exposure_eda ORDER BY league,season;',
        'team_results.csv': 'SELECT * FROM futwar.team_results_baseline ORDER BY league,season,team;',
    }
    output = Path('data/processed/exploration')
    output.mkdir(parents=True, exist_ok=True)
    files = []
    for filename, query in queries.items():
        result = psql('--csv', '-c', query)
        rows = list(csv.DictReader(io.StringIO(result)))
        payload = result.encode('utf-8')
        (output / filename).write_bytes(payload)
        files.append(dict(filename=filename, records=len(rows), query=query,
                          sha256=hashlib.sha256(payload).hexdigest()))
    expected = {'player_team_seasons.csv':22418, 'season_exposure.csv':40, 'team_results.csv':780}
    if any(f['records'] != expected[f['filename']] for f in files):
        raise ValueError('Snapshot counts differ from the audited scope; investigate before exploration')
    metadata = dict(exported_at_utc=datetime.now(timezone.utc).isoformat(),
                    source='Local PostgreSQL audited views; no new transformations or filters',
                    row_grain='Player-team-season record; identities are not aggregated',
                    scope='Big Five leagues, 2017-18 through 2024-25', files=files)
    (output / 'snapshot.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps({f['filename']:f['records'] for f in files}, indent=2))


if __name__ == '__main__':
    main()
