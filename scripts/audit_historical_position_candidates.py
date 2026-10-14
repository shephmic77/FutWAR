"""Create historical-label review candidates; textual labels are not verified roles."""
import hashlib
import json
from collections import Counter

import pandas as pd

from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CODES={'GB1':'Premier League','ES1':'La Liga','IT1':'Serie A','L1':'Bundesliga','FR1':'Ligue 1'}


def main():
    files={}
    for name in ['player_identity_source_manifest.json','position_source_manifest.json']:
        manifest=json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
        for item in manifest['files']:
            if item['filename'] in ['games.csv.gz','appearances.csv.gz','game_lineups.csv.gz']:
                path=ROOT/item['path']
                if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
                    raise ValueError('Position candidate source changed')
                files[item['filename']]=item
    def load(name,columns):
        return pd.read_csv(ROOT/files[name]['path'],usecols=columns)
    games=load('games.csv.gz',['game_id','competition_id','season'])
    games=games.loc[games.competition_id.isin(CODES)&games.season.between(2017,2024)].copy()
    games['league']=games.competition_id.map(CODES)
    games['season_label']=games.season.map(lambda year:f'{year}-{str(year+1)[-2:]}')
    appearances=load('appearances.csv.gz',['game_id','player_id','player_club_id','player_name'])
    appearances=appearances.merge(games[['game_id','league','season_label']],on='game_id',validate='many_to_one')
    lineups=load('game_lineups.csv.gz',['game_id','player_id','club_id','type','position'])
    lineups=lineups.loc[lineups.game_id.isin(games.game_id)].rename(columns={'club_id':'player_club_id'})
    keys=['game_id','player_id','player_club_id']
    if appearances.duplicated(keys).any() or lineups.duplicated(keys).any():
        raise ValueError('Ambiguous appearance/lineup keys')
    linked=appearances.merge(lineups,on=keys,how='left',validate='one_to_one',indicator=True)
    records=[]
    for (player_id,league,season),cell in linked.groupby(['player_id','league','season_label']):
        counts=Counter(cell.position.dropna())
        records.append(dict(provider_namespace='transfermarkt_publisher',provider_player_id=int(player_id),
            player_name=cell.player_name.iloc[0],league=league,season=season,
            appearance_records=len(cell),club_stints=cell.player_club_id.nunique(),
            matched_labels=int(cell.position.notna().sum()),unlinked_or_missing_labels=int(cell.position.isna().sum()),
            distinct_text_labels=len(counts),text_label_counts=json.dumps(dict(sorted(counts.items())),ensure_ascii=False),
            lineup_type_counts=json.dumps(dict(Counter(cell.type.dropna())),ensure_ascii=False),
            role_evidence_status='unverified_position_text_not_played_role',seasonal_position_labels_finalized=False))
    candidates=pd.DataFrame(records)
    review=candidates.loc[candidates.distinct_text_labels.gt(1)].sort_values(
        ['distinct_text_labels','appearance_records'],ascending=False)
    output=ROOT/'reports/position_source'
    output.mkdir(parents=True,exist_ok=True)
    candidates.to_csv(output/'historical_label_candidates.csv',index=False)
    review.to_csv(output/'historical_label_variation_review.csv',index=False)
    coverage=[]
    for (league,season),cell in linked.groupby(['league','season_label']):
        coverage.append(dict(league=league,season=season,appearances=len(cell),
            populated_labels=int(cell.position.notna().sum()),unlinked_or_missing=int(cell.position.isna().sum()),
            verified_specific_roles=0,status='textual_candidates_only; roles_not_verified'))
    pd.DataFrame(coverage).to_csv(output/'historical_role_readiness.csv',index=False)
    summary=dict(input_sha256={item['path']:item['sha256'] for item in files.values()},
        target_matches=len(games),appearance_records=len(linked),league_season_cells=len(coverage),
        player_league_season_candidates=len(candidates),multiple_text_label_candidates=len(review),
        observed_position_texts=sorted(linked.position.dropna().unique()),
        lineup_types=linked.type.value_counts().to_dict(),
        wingback_labels_observed=bool(linked.position.fillna('').str.contains('wing.?back',case=False,regex=True).any()),
        user_position_rule_applied=False,positions_changed=False)
    (output/'historical_candidate_lineage.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    for path,digest in summary['input_sha256'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Input modified during historical candidate audit')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['input_sha256','observed_position_texts']},indent=2))


if __name__=='__main__':
    main()
