"""Audit keeper-to-player record candidates without changing either dataset."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from reconcile_keeper_candidates import normalize

ROOT = Path(__file__).resolve().parents[1]


def birth_year(value):
    number = pd.to_numeric(value, errors='coerce')
    return None if pd.isna(number) else int(number)


def candidate_key(league, season, team, player, born):
    return league, season, normalize(team), normalize(player), birth_year(born)


def reviewed_alias_key(keeper, rules):
    matches = []
    for rule_number, rule in enumerate(rules, start=1):
        if keeper['league'] != rule['league'] or keeper['season'] not in rule['seasons']:
            continue
        if keeper['team_name'] != rule['team_from']:
            continue
        name, born = keeper['player_name'], birth_year(keeper['birth_year'])
        if 'players' in rule:
            if name not in rule['players'] or born != rule['players'][name]:
                continue
            target_name = name
        else:
            if name != rule['player_from'] or born != rule['birth_year']:
                continue
            target_name = rule['player_to']
        matches.append((candidate_key(keeper['league'], keeper['season'],
                                     rule['team_to'], target_name, born), rule_number))
    if len(matches) > 1:
        raise ValueError('Overlapping reviewed alias rules')
    return matches[0] if matches else (None, None)


def main():
    paths = {
        'keepers': ROOT / 'data/processed/keeper_archives/keeper_seasons.csv',
        'players': ROOT / 'data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv',
        'exploration': ROOT / 'data/processed/exploration/player_team_seasons.csv',
        'aliases': ROOT / 'data/keeper_identity_aliases.json',
    }
    hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()}
    keepers = pd.read_csv(paths['keepers'])
    players = pd.read_csv(paths['players'], sep=';', decimal=',')
    exploration = pd.read_csv(paths['exploration'])
    rules = json.loads(paths['aliases'].read_text(encoding='utf-8'))['rules']
    # Record numbers are valid only after checking the entire existing snapshot alignment.
    expected = pd.DataFrame({
        'output_record': range(1, len(players) + 1),
        'league': players.league, 'season': players.season,
        'team_name': players.team, 'player_name': players.player,
    })
    columns = list(expected.columns)
    if not expected.equals(exploration[columns].reset_index(drop=True)):
        raise ValueError('Player rows do not align with exploration record numbers')
    index = {}
    for record, row in enumerate(players.to_dict('records'), start=1):
        key = candidate_key(row['league'], row['season'], row['team'], row['player'], row['born_'])
        if key[-1] is not None:
            index.setdefault(key, []).append((record, row))
    rows = []
    for keeper in keepers.to_dict('records'):
        key = candidate_key(keeper['league'], keeper['season'], keeper['team_name'],
                            keeper['player_name'], keeper['birth_year'])
        candidates = index.get(key, []) if key[-1] is not None else []
        alias_rule = None
        if not candidates:
            alias_key, alias_rule = reviewed_alias_key(keeper, rules)
            candidates = index.get(alias_key, [])
        status = ('unique_field_agreement' if len(candidates) == 1 else
                  'ambiguous_field_agreement' if candidates else 'no_exact_candidate')
        if alias_rule and len(candidates) == 1:
            status = 'reviewed_alias_unique_candidate'
        local = candidates[0][1] if len(candidates) == 1 else {}
        local_minutes = pd.to_numeric(local.get('Playing Time_Min'), errors='coerce')
        local_appearances = pd.to_numeric(local.get('Playing Time_MP'), errors='coerce')
        rows.append({
            'keeper_record_id': keeper['keeper_record_id'],
            'league': keeper['league'], 'season': keeper['season'],
            'team_name': keeper['team_name'], 'player_name': keeper['player_name'],
            'birth_year': keeper['birth_year'], 'candidate_status': status,
            'candidate_count': len(candidates),
            'alias_rule': alias_rule,
            'candidate_output_records': json.dumps([record for record, _ in candidates]),
            'identity_verified': False,
            'keeper_minutes': keeper['keeper_minutes'], 'local_total_minutes': local_minutes,
            'minutes_difference': keeper['keeper_minutes'] - local_minutes,
            'keeper_appearances': keeper['appearances'], 'local_appearances': local_appearances,
            'appearances_difference': keeper['appearances'] - local_appearances,
            'keeper_nominal_position': keeper['nominal_position'],
            'local_nominal_position': local.get('pos_'), 'quality_flags': keeper['quality_flags'],
        })
    result = pd.DataFrame(rows)
    if len(result) != len(keepers) or result.keeper_record_id.duplicated().any():
        raise ValueError('Identity audit lost or duplicated a keeper record')
    output = ROOT / 'reports/keeper_archive'
    output.mkdir(parents=True, exist_ok=True)
    result.to_csv(output / 'staged_identity_candidates.csv', index=False)
    result.loc[result.quality_flags.ne('[]')].to_csv(output / 'flagged_identity_review.csv', index=False)
    summary = {
        'input_sha256': hashes, 'records': len(result),
        'candidate_counts': result.candidate_status.value_counts().to_dict(),
        'flagged_records': int(result.quality_flags.ne('[]').sum()),
        'scope': 'Field agreement only; common upstream possible; no verified identities or stat merge.',
    }
    (output / 'staged_identity_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    if hashes != {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()}:
        raise ValueError('An input changed during the audit')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
