"""Descriptive position metrics for the user-selected 900-minute cohort."""
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

METRICS = ['non_penalty_goals','npxg','xa','xag','progressive_passes',
           'progressive_carries','tackles','interceptions']
LABELS = dict(non_penalty_goals='Non-penalty goals',npxg='npxG',xa='xA',xag='xAG',
              progressive_passes='Progressive passes',progressive_carries='Progressive carries',
              tackles='Tackles',interceptions='Interceptions')


def load_inputs(root):
    folder = root / 'data/processed/exploration'
    snapshot = json.loads((folder/'snapshot.json').read_text(encoding='utf-8'))
    for source in snapshot['files']:
        if hashlib.sha256((folder/source['filename']).read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError('Exploration input fingerprint changed; re-export and review')
    players = pd.read_csv(folder/'player_team_seasons.csv')
    for column in ['minutes',*METRICS]:
        players[column] = pd.to_numeric(players[column],errors='raise')
    if players.duplicated(['source_sha256','output_record']).any():
        raise ValueError('Duplicate processed record keys')
    if (players['minutes'].dropna()<0).any() or (players[METRICS]<0).any().any():
        raise ValueError('Negative exposure or candidate metric; inspect before exploration')
    if len(players)!=22418 or players[['league','season']].drop_duplicates().shape[0]!=40:
        raise ValueError('Unexpected scope')
    return players,pd.read_csv(folder/'season_exposure.csv'),pd.read_csv(folder/'team_results.csv'),snapshot


def eligibility_masks(players,min_minutes=900):
    if min_minutes<=0:raise ValueError('Positive exploratory minutes cutoff required')
    known=players['nominal_position'].notna()
    goalkeeper=players['nominal_position'].fillna('').str.split(',').apply(lambda p:'GK' in p)
    outfield=known & ~goalkeeper
    return outfield,outfield & players['minutes'].ge(min_minutes)


def weighted_rate(values,minutes):
    valid=values.notna() & minutes.notna() & minutes.gt(0)
    denominator=minutes[valid].sum()
    return 90*values[valid].sum()/denominator if denominator>0 else np.nan


def exclusion_summary(players,min_minutes=900):
    outfield,eligible=eligibility_masks(players,min_minutes)
    rows=[]
    for (league,season),group in players.groupby(['league','season'],sort=True):
        ix=group.index
        rows.append(dict(league=league,season=season,all_records=len(group),
            unknown_position_records=int(group['nominal_position'].isna().sum()),
            goalkeeper_records=int((~outfield.loc[ix] & group['nominal_position'].notna()).sum()),
            outfield_records=int(outfield.loc[ix].sum()),eligible_records=int(eligible.loc[ix].sum()),
            outfield_below_cutoff=int((outfield.loc[ix] & group['minutes'].lt(min_minutes)).sum()),
            outfield_missing_minutes=int((outfield.loc[ix] & group['minutes'].isna()).sum()),
            eligible_minutes=group.loc[eligible.loc[ix],'minutes'].sum(),min_minutes=min_minutes))
    return pd.DataFrame(rows)


def metric_distributions(players,min_minutes=900):
    outfield,eligible=eligibility_masks(players,min_minutes)
    positions=sorted(players.loc[outfield,'nominal_position'].unique())
    rows=[]
    for league,season,position in itertools.product(sorted(players['league'].unique()),
            sorted(players['season'].unique()),positions):
        mask=players['league'].eq(league) & players['season'].eq(season) & players['nominal_position'].eq(position)
        all_group=players.loc[mask];group=players.loc[mask & eligible]
        for metric in METRICS:
            known=group[metric].notna();rates=90*group.loc[known,metric]/group.loc[known,'minutes']
            quantiles=rates.quantile([.05,.25,.5,.75,.95])
            rows.append(dict(league=league,season=season,nominal_position=position,metric=metric,
                all_position_records=len(all_group),eligible_records=len(group),
                eligible_metric_known_records=int(known.sum()),eligible_missing_metric_records=int((~known).sum()),
                eligible_missing_metric_pct=100*(~known).mean() if len(group) else np.nan,
                known_metric_minutes=group.loc[known,'minutes'].sum(),
                exposure_weighted_per90=weighted_rate(group[metric],group['minutes']),
                p05_per90=quantiles.loc[.05],p25_per90=quantiles.loc[.25],median_per90=quantiles.loc[.5],
                p75_per90=quantiles.loc[.75],p95_per90=quantiles.loc[.95],
                min_per90=rates.min(),max_per90=rates.max(),min_minutes=min_minutes))
    return pd.DataFrame(rows)


def exposure_context(exposure,teams):
    matches=teams.groupby(['league','season'],as_index=False)['played'].sum().rename(columns={'played':'team_games'})
    context=exposure.merge(matches,on=['league','season'],validate='one_to_one')
    context['player_minutes_per_team_game']=context['all_player_minutes']/context['team_games']
    return context


def render_figures(players,context,output,min_minutes=900):
    _,eligible=eligibility_masks(players,min_minutes)
    cohort=players.loc[eligible]
    positions=sorted(cohort['nominal_position'].unique())
    paths=[]
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,4,figsize=(18,10),layout='constrained')
    for metric,ax in zip(METRICS,axes.flat):
        groups=[(90*cohort.loc[cohort['nominal_position'].eq(p),metric]/
                 cohort.loc[cohort['nominal_position'].eq(p),'minutes']).dropna().to_numpy() for p in positions]
        ax.boxplot(groups,tick_labels=positions,showfliers=True,
                   flierprops={'markersize':2,'alpha':.25})
        ax.set_title(LABELS[metric]);ax.set_ylabel('Per 90 minutes');ax.tick_params(axis='x',rotation=60)
    fig.suptitle(f'Player-team-season distributions | {min_minutes}+ minutes | original position labels\n'
                 'Pooled leagues/seasons; dots are outliers; record counts are in the accompanying tables',fontsize=15)
    path=output/'position_distributions.png';fig.savefig(path,dpi=160);plt.close(fig);paths.append(path)
    for position in ['DF','MF','FW']:
        fig,axes=plt.subplots(2,4,figsize=(16,9),layout='constrained')
        part=cohort.loc[cohort['nominal_position'].eq(position)]
        for metric,ax in zip(METRICS,axes.flat):
            for league,group in part.groupby('league',sort=True):
                rates=group.groupby('season').apply(lambda g:weighted_rate(g[metric],g['minutes']),include_groups=False)
                ax.plot(rates.index,rates.values,marker='o',markersize=3,label=league)
            ax.set_title(LABELS[metric]);ax.set_ylabel('Exposure-weighted per 90');ax.tick_params(axis='x',rotation=60)
        handles,labels=axes.flat[0].get_legend_handles_labels()
        fig.legend(handles,labels,loc='outside lower center',ncol=5)
        fig.suptitle(f'{position} records | {min_minutes}+ minutes | descriptive season trends\n'
                     'Cohort membership changes each season; these rates do not establish league strength',fontsize=14)
        path=output/f'season_trends_{position}.png';fig.savefig(path,dpi=150);plt.close(fig);paths.append(path)
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    for league,group in context.groupby('league',sort=True):
        axes[0].plot(group['season'],group['player_minutes_per_team'],marker='o',label=league)
        axes[1].plot(group['season'],group['player_minutes_per_team_game'],marker='o',label=league)
    axes[0].set_title('All-player minutes per club');axes[1].set_title('All-player minutes per completed team-game')
    for ax in axes:ax.tick_params(axis='x',rotation=60);ax.set_ylabel('Minutes')
    fig.legend(*axes[0].get_legend_handles_labels(),loc='outside lower center',ncol=5)
    fig.suptitle('Schedule/exposure context | all records, including goalkeepers | no COVID exclusion',fontsize=14)
    path=output/'season_exposure_context.png';fig.savefig(path,dpi=150);plt.close(fig);paths.append(path)
    return paths


def run(root,min_minutes=900):
    players,exposure,teams,snapshot=load_inputs(root)
    output=root/'reports/exploration';output.mkdir(parents=True,exist_ok=True)
    exclusions=exclusion_summary(players,min_minutes)
    distributions=metric_distributions(players,min_minutes)
    context=exposure_context(exposure,teams)
    for name,table in [('eligibility_counts',exclusions),('metric_distributions',distributions),('exposure_context',context)]:
        table.to_csv(output/(name+'.csv'),index=False)
    figures=render_figures(players,context,output,min_minutes)
    _,eligible=eligibility_masks(players,min_minutes)
    summary=dict(min_minutes=min_minutes,cutoff_authority='User selected 900+ minutes for exploratory displays; no model eligibility rule',
        all_records=len(players),eligible_outfield_records=int(eligible.sum()),
        excluded_records=int((~eligible).sum()),eligible_metric_missing_cells=int(players.loc[eligible,METRICS].isna().sum().sum()),
        position_labels=sorted(players.loc[eligible,'nominal_position'].unique()),distribution_rows=len(distributions),
        empty_group_metric_rows=int(distributions['eligible_records'].eq(0).sum()),
        snapshot=snapshot,war_formula_applied=False,identities_aggregated=False,covid_seasons_excluded=False,
        metric_definition_status='Source-total mappings retained; exact historical provider definitions still require confirmation')
    (output/'run.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return players,exclusions,distributions,context,figures,summary


if __name__=='__main__':
    result=run(Path(__file__).resolve().parents[1])
    print(json.dumps({k:v for k,v in result[-1].items() if k!='snapshot'},indent=2))
