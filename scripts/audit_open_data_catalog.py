"""Audit catalog presence across all target cells; do not claim match completeness."""
import hashlib
import json
from pathlib import Path

from audit_standings_and_identity import write_csv


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'data/open_data_catalog_manifest.json').read_text(encoding='utf-8'))
    for source in manifest['files']:
        if hashlib.sha256((root / source['path']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Catalog/specification fingerprint changed')
    catalog = json.loads((root / 'data/raw/statsbomb_open/2026-10-10/data/competitions.json').read_text(encoding='utf-8'))
    names = {'Premier League': 'Premier League', 'La Liga': 'La Liga', 'Serie A': 'Serie A',
             'Bundesliga': '1. Bundesliga', 'Ligue 1': 'Ligue 1'}
    rows = []
    for league, source_name in names.items():
        for year in range(2017, 2025):
            matches = [r for r in catalog if r['competition_name'] == source_name
                       and r['competition_gender'] == 'male' and not r['competition_youth']
                       and r['season_name'] == f'{year}/{year + 1}']
            if len(matches) > 1:
                raise ValueError('Ambiguous catalog entry')
            record = matches[0] if matches else {}
            rows.append(dict(league=league, season=f'{year}-{str(year + 1)[-2:]}',
                             catalog_listed=bool(matches), competition_id=record.get('competition_id', ''),
                             season_id=record.get('season_id', ''),
                             match_completeness='not_audited', played_position_coverage='not_audited',
                             goalkeeper_metric_coverage='not_audited'))
    folder = root / 'reports/position_source'
    folder.mkdir(parents=True, exist_ok=True)
    write_csv(folder / 'open_data_catalog_coverage.csv', rows)
    print(json.dumps(dict(target_cells=len(rows), catalog_listed=sum(r['catalog_listed'] for r in rows),
                          commit=manifest['commit'], match_events_downloaded=False), indent=2))


if __name__ == '__main__':
    main()
