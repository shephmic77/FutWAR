"""Export a private browser-local prototype from audited descriptive cohorts."""
import json
import base64
import hashlib
import mimetypes
import shutil
from pathlib import Path

import pandas as pd
from analysis_tracks import load_cohorts
from explore_player_metrics import load_inputs, METRICS as OUTFIELD
from explore_keeper_metrics import METRICS as KEEPER, LABELS as KEEPER_LABELS

ROOT = Path(__file__).resolve().parents[1]


def build():
    outfield, keeper, accounting, lineage = load_cohorts()
    _, _, teams, _ = load_inputs(ROOT)
    if teams.duplicated(['league', 'season', 'team']).any():
        raise ValueError('Ambiguous team context')
    team_lookup = {(r['league'], r['season'], r['team']): r for r in teams.to_dict('records')}
    rows = []
    labels = {'goals_per90': 'Goals / 90', 'assists_per90': 'Assists / 90',
        'non_penalty_goals_per90': 'Non-penalty goals / 90', 'npxg_per90': 'npxG / 90',
        'xa_per90': 'xA / 90', 'xag_per90': 'xAG / 90',
        'progressive_passes_per90': 'Progressive passes / 90',
        'progressive_carries_per90': 'Progressive carries / 90',
        'tackles_per90': 'Tackles / 90', 'interceptions_per90': 'Interceptions / 90',
        **dict(zip(KEEPER, KEEPER_LABELS))}
    for frame, domain, metrics in [(outfield, 'Outfield', ['goals_per90', 'assists_per90', *[m+'_per90' for m in OUTFIELD]]),
                                    (keeper, 'GK', KEEPER)]:
        grouped = frame.groupby(['league', 'season', 'analysis_position', 'source_variant'])
        medians = grouped[metrics].transform('median')
        sizes = grouped['record_id'].transform('size')
        for index, row in frame.iterrows():
            warnings = ['Cross-provider identity unverified; this is one source club-season record.']
            if domain == 'GK':
                warnings.append('Keeper metric model versions remain unconfirmed.')
                for field in ['unresolved_quality_flags', 'exposure_correction_warnings', 'psxg_correction_warnings']:
                    warnings.extend(json.loads(row[field]))
            else:
                warnings.append('Nominal position is broad; specific historical main position is not established.')
            rows.append({'id': row.record_id, 'name': row.player_name, 'team': row.team_name,
                'league': row.league, 'season': row.season, 'domain': domain,
                'position': row.analysis_position, 'main_position': None,
                'minutes': row.keeper_minutes if domain == 'GK' else row.minutes,
                'source': row.source_variant, 'warnings': warnings,
                'metrics': {m: row[m] for m in metrics},
                'peer_medians': {m: medians.at[index, m] for m in metrics}, 'peer_count': int(sizes.at[index]),
                'team_context': team_lookup.get((row.league, row.season, row.team_name)),
                'source_links': [row.basic_source_url, row.advanced_source_url] if domain == 'GK' else
                    ['https://www.kaggle.com/datasets/emrey3lmaz/top-5-league-football-player-stats-2017-2025']})
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate profile record key')
    # pandas serialization converts missing numeric data to null, never zero or NaN tokens.
    clean_rows = json.loads(pd.DataFrame(rows).to_json(orient='records', force_ascii=False))
    payload = {'records': clean_rows, 'labels': labels, 'lineage': lineage,
               'accounting': accounting.to_dict('records'), 'cutoff_minutes': 900,
               'identity_merge': False, 'main_position_rule': 'most total evidenced position minutes'}
    payload['images'] = []
    manifest_path = ROOT / 'data/profile_image_manifest.json'
    if manifest_path.exists():
        assets = json.loads(manifest_path.read_bytes())['assets']
        current = {(a['kind'], a['label']): a for a in assets}
        for asset in current.values():
            path = ROOT / asset['path']
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != asset['sha256']:
                raise ValueError('Profile image source changed')
            mime = mimetypes.guess_type(path.name)[0]
            payload['images'].append({**asset, 'data_url': 'data:' + mime + ';base64,' + base64.b64encode(content).decode('ascii')})
    folder = ROOT / 'reports/player_profile'
    folder.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / 'profile').iterdir():
        if source.is_file():
            shutil.copy2(source, folder / source.name)
    (folder / 'data.json').write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    html = (ROOT / 'profile/index.html').read_text(encoding='utf-8')
    css = (ROOT / 'profile/style.css').read_text(encoding='utf-8')
    javascript = (ROOT / 'profile/app.js').read_text(encoding='utf-8')
    # Escape markup delimiters in embedded data; source names cannot terminate a script tag.
    embedded = json.dumps(payload, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c')
    html = html.replace('<link rel="stylesheet" href="style.css">', '<style>' + css + '</style>')
    html = html.replace('<script src="app.js"></script>',
        '<script type="application/json" id="profile-data">' + embedded + '</script><script>' + javascript + '</script>')
    (folder / 'FutWAR_Player_Explorer.html').write_text(html, encoding='utf-8')
    print(f'Built local profile: {len(rows)} records; {len(teams)} team contexts; no identity merge.')


if __name__ == '__main__':
    build()
