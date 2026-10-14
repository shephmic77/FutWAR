"""Run and export the initial SQL EDA from the active Docker PostgreSQL database."""
import csv
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def psql(*arguments):
    completed = subprocess.run(['docker','compose','exec','-T','postgres','psql',
                                '-X','-U','futwar','-d','futwar','-v','ON_ERROR_STOP=1',*arguments],
                               capture_output=True, text=True, encoding='utf-8', check=True)
    return completed.stdout


def export():
    psql('-f','sql/005_exploration_views.sql')
    output = Path('reports/eda')
    output.mkdir(parents=True, exist_ok=True)
    tables = {'season_exposure': 'season_exposure_eda',
              'position_metrics': 'position_metric_eda', 'team_exposure': 'team_exposure_eda'}
    counts = {}
    for filename, view in tables.items():
        result = psql('--csv','-c',f'SELECT * FROM futwar.{view} ORDER BY league, season;')
        records = list(csv.DictReader(io.StringIO(result)))
        (output/f'{filename}.csv').write_text(result,encoding='utf-8',newline='')
        counts[filename] = len(records)
    (output/'run.json').write_text(json.dumps({'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'output_rows':counts,'source':'local PostgreSQL staging; approved source correction',
        'scope':'2017-18 through 2024-25; all seasons retained',
        'war_formula_applied':False},indent=2),encoding='utf-8')
    print(json.dumps(counts,indent=2))


if __name__ == '__main__':
    export()
