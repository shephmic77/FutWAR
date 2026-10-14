"""Shared position descriptions and metric-overlap research; never a value score."""
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from explore_player_metrics import load_inputs, eligibility_masks, METRICS as OUTFIELD_METRICS
from explore_keeper_metrics import load_inputs as load_keepers, prepare, METRICS as KEEPER_METRICS

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'reports/analysis_tracks'


def load_cohorts():
    players, _, _, snapshot = load_inputs(ROOT)
    _, selected = eligibility_masks(players,900)
    outfield = players.loc[selected].copy()
    clean_path = ROOT/'data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv'
    clean_hash = hashlib.sha256(clean_path.read_bytes()).hexdigest()
    if clean_hash != '0f2ffe44ab175523ddcffaef71398356207ab4f81c7fbf6e7235b21e5d941297':
        raise ValueError('Clean player source differs from audited snapshot')
    clean = pd.read_csv(clean_path,sep=';',decimal=',')
    if len(clean) != len(players):
        raise ValueError('Player source row count changed')
    for column, source in [('league','league'),('season','season'),('team_name','team'),('player_name','player')]:
        if not players[column].reset_index(drop=True).equals(clean[source].reset_index(drop=True)):
            raise ValueError('Original player records do not align with exploration')
    if players.output_record.tolist() != list(range(1,len(players)+1)):
        raise ValueError('Unexpected original record numbering')
    # Two fields from the same verified original record, not a cross-provider join.
    for metric, source in [('goals','Performance_Gls'),('assists','Performance_Ast')]:
        outfield[metric] = pd.to_numeric(clean.loc[outfield.index,source],errors='raise')
    for metric in ['goals','assists',*OUTFIELD_METRICS]:
        outfield[metric+'_per90'] = 90*outfield[metric]/outfield.minutes
    outfield['record_id'] = outfield.output_record.map(lambda value:f'original_player:{value}')
    outfield['provider_namespace'] = 'original_player_csv'
    outfield['source_variant'] = 'original_player_csv'
    outfield['analysis_position'] = outfield.nominal_position
    keepers, keeper_hash = load_keepers()
    keeper_prepared = prepare(keepers)
    keeper = keeper_prepared.loc[keeper_prepared.eligible].copy()
    keeper['record_id'] = 'keeper_archive:'+keeper.keeper_record_id
    keeper['provider_namespace'] = 'keeper_archive'
    keeper['analysis_position'] = 'GK'
    counts = pd.DataFrame([
        dict(domain='Outfield',source_records=len(players),included_records=len(outfield),
             outside_domain_or_cutoff=len(players)-len(outfield),interpretation='Includes source GK rows outside outfield domain'),
        dict(domain='GK',source_records=len(keepers),included_records=len(keeper),
             outside_domain_or_cutoff=len(keepers)-len(keeper),interpretation='Keeper archive; emergency rows retained outside focus'),
    ])
    return outfield, keeper, counts, dict(outfield_snapshot=snapshot, clean_player_sha256=clean_hash,
        keeper_sha256=keeper_hash, cutoff=900, cross_provider_identity_merge=False,
        outfield_position_status='broad nominal labels; detailed historical roles unresolved',
        owner_direction='GK and outfield included in both position descriptions and overall-value research')


def position_summary(outfield, keeper):
    rows=[]
    domains=[(outfield,['goals_per90','assists_per90',*[m+'_per90' for m in OUTFIELD_METRICS]]),
             (keeper,KEEPER_METRICS)]
    for frame,metrics in domains:
        for (league,season,position,source),cell in frame.groupby(['league','season','analysis_position','source_variant']):
            for metric in metrics:
                values=cell[metric].dropna()
                rows.append(dict(league=league,season=season,position=position,source_variant=source,
                    metric=metric,included_records=len(cell),available_values=len(values),
                    missing_values=int(cell[metric].isna().sum()),median=values.median(),
                    q25=values.quantile(.25),q75=values.quantile(.75),
                    interpretation='Within-position description; no cross-position value scale'))
    return pd.DataFrame(rows)


def overlap_summary(outfield,keeper):
    rows=[]
    domains=[(outfield,['goals_per90','assists_per90',*[m+'_per90' for m in OUTFIELD_METRICS]]),
             (keeper.copy(),KEEPER_METRICS)]
    # Preserve approved fills in descriptions; do not mix old PSxG measurements into
    # pairwise source-cohort correlations. Other measurements stay available.
    domains[1][0].loc[domains[1][0].has_psxg_warning,'psxg_per90']=np.nan
    for frame,metrics in domains:
        for (league,season,position,source),cell in frame.groupby(['league','season','analysis_position','source_variant']):
            matrix=cell[metrics].corr(method='spearman')
            present=cell[metrics].notna().astype(int)
            pair_counts=present.T.dot(present)
            for left,right in itertools.combinations(metrics,2):
                paired=int(pair_counts.at[left,right])
                reason='available'
                value=matrix.at[left,right]
                if paired<3:
                    reason='fewer_than_three_pairs'
                    value=np.nan
                elif pd.isna(value):
                    reason='constant_or_undefined_pair'
                rows.append(dict(league=league,season=season,position=position,source_variant=source,
                    left_metric=left,right_metric=right,paired_records=paired,spearman=value,
                    status=reason,interpretation='Exploratory association; no weights, causality or replacement value'))
    return pd.DataFrame(rows)


def run():
    outfield,keeper,counts,lineage=load_cohorts()
    positions=position_summary(outfield,keeper)
    overlaps=overlap_summary(outfield,keeper)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    counts.to_csv(OUTPUT/'cohort_accounting.csv',index=False)
    positions.to_csv(OUTPUT/'position_metric_distributions.csv',index=False)
    overlaps.to_csv(OUTPUT/'within_context_metric_overlap.csv',index=False)
    roles=pd.concat([outfield[['league','season','analysis_position','record_id']],
                     keeper[['league','season','analysis_position','record_id']]],ignore_index=True)
    if roles.record_id.duplicated().any():
        raise ValueError('Duplicate analysis-domain record keys')
    role_counts=roles.groupby('analysis_position').size().rename('included_records').reset_index()
    role_counts.to_csv(OUTPUT/'position_counts.csv',index=False)
    lineage.update(included_outfield=len(outfield),included_keeper=len(keeper),
        analysis_domain_records=len(roles),position_labels=role_counts.analysis_position.tolist(),
        position_summary_rows=len(positions),overlap_rows=len(overlaps),formula_finalized=False)
    (OUTPUT/'lineage.json').write_text(json.dumps(lineage,indent=2),encoding='utf-8')
    return outfield,keeper,counts,positions,overlaps,role_counts


if __name__=='__main__':
    outputs=run()
    print(outputs[-1].to_string(index=False))
