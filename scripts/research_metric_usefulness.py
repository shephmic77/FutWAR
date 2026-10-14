"""Descriptive metric overlap and team-context diagnostics, never player value."""
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis_tracks import load_cohorts, OUTFIELD_METRICS, KEEPER_METRICS

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'reports/metric_usefulness'
POSITIONS={'GK','RB','RWB','CB','LB','LWB','CM','CDM','CAM','LM','RM','ST','LW','RW'}
ALIASES={'DM':'CDM','AM':'CAM','CF':'ST','SS':'ST'}
CONTEXT=['team_goals_against_per_match','team_goals_for_per_match']
EXTRA={'blocks_per90':'Blocks_Blocks','recoveries_per90':'Performance_Recov',
       'aerial_duels_won_per90':'Aerial Duels_Won','aerial_duels_lost_per90':'Aerial Duels_Lost',
       'key_passes_per90':'KP_','progressive_receptions_per90':'Receiving_PrgR',
       'passes_into_box_per90':'PPA_','dispossessions_per90':'Carries_Dis',
       'miscontrols_per90':'Carries_Mis','errors_per90':'Err_'}


def specific_role(value):
    value=ALIASES.get(value,value)
    return value if value in POSITIONS else None


def count_rate(value,minutes):
    count=float(str(value).replace(',','.')) if value not in ('',None) else np.nan
    if count<0:raise ValueError('Negative additional count')
    return 90*count/minutes if minutes>0 else np.nan


def association(frame,left,right):
    pair=frame[[left,right]].replace([np.inf,-np.inf],np.nan).dropna()
    if len(pair)<3:return len(pair),np.nan,'fewer_than_three_pairs'
    if pair[left].nunique()<2 or pair[right].nunique()<2:
        return len(pair),np.nan,'constant_pair'
    return len(pair),pair.corr(method='spearman').iloc[0,1],'descriptive_only'


def attach_context(outfield,keeper,records):
    """Use existing record keys; verify metadata and expose candidate GK joins."""
    by_id={r['id']:r for r in records}
    keeper_map={}
    for r in records:
        if r.get('keeper'):
            kid=r['keeper']['id']
            if kid in keeper_map:raise ValueError('Repeated keeper overlay key')
            keeper_map[kid]=r
    frames=[]
    for domain,original in [('Outfield',outfield),('GK',keeper)]:
        frame=original.copy()
        additions=[]
        for row in frame.to_dict('records'):
            r=by_id.get(row['record_id']) if domain=='Outfield' else keeper_map.get(row['keeper_record_id'])
            if r and domain=='Outfield':
                expected=(row['player_name'],row['team_name'],row['league'],row['season'])
                actual=(r['name'],r['team'],r['league'],r['season'])
                if expected!=actual:raise ValueError('Original record metadata mismatch')
            if r and (r['league'],r['season'])!=(row['league'],row['season']):
                raise ValueError('Keeper candidate context mismatch')
            t=r.get('team_context') if r else None
            role='GK' if domain=='GK' else specific_role(r.get('display_role') if r else None)
            added=dict(role=role or 'Unavailable',domain=domain,
                context_team=t['team'] if t else None,
                team_goals_against_per_match=t['goals_against']/t['played'] if t and t['played']>0 else np.nan,
                team_goals_for_per_match=t['goals_for']/t['played'] if t and t['played']>0 else np.nan,
                context_link='original_record' if domain=='Outfield' and t else 'existing_keeper_candidate' if t else 'unavailable')
            if domain=='Outfield':
                for metric,column in EXTRA.items():
                    value=r['source_stats'].get(column,'') if r else ''
                    added[metric]=count_rate(value,row['minutes'])
            additions.append(added)
        frame=frame.reset_index(drop=True).join(pd.DataFrame(additions))
        if domain=='GK':frame.loc[frame.has_psxg_warning,'psxg_per90']=np.nan
        frames.append(frame)
    return frames


def overlap(frame,metrics):
    results=[]
    known=frame.loc[frame.role.ne('Unavailable')]
    for key,cell in known.groupby(['league','season','role','source_variant']):
        matrix=cell[metrics].corr(method='spearman')
        present=cell[metrics].notna().astype(int)
        pairs=present.T.dot(present)
        for left,right in itertools.combinations(metrics,2):
            n=int(pairs.at[left,right]);rho=matrix.at[left,right]
            status='fewer_than_three_pairs' if n<3 else 'constant_pair' if pd.isna(rho) else 'descriptive_only'
            if n<3:rho=np.nan
            results.append(dict(zip(['league','season','role','source_variant'],key),
                domain=cell.domain.iloc[0],left_metric=left,right_metric=right,
                paired_records=n,spearman=rho,status=status))
    return pd.DataFrame(results)


def team_aggregates(frame,metrics):
    """One club-role-source observation, exposure-weighted compatible metrics."""
    rows=[]
    valid=frame.loc[frame.role.ne('Unavailable')&frame.context_team.notna()]
    for key,cell in valid.groupby(['league','season','role','source_variant','context_team']):
        row=dict(zip(['league','season','role','source_variant','team'],key),
                 included_records=len(cell),domain=cell.domain.iloc[0])
        mins=cell['minutes'] if row['domain']=='Outfield' else cell['keeper_minutes']
        for flag in ['has_diagnostic_flag','has_exposure_warning','has_psxg_warning']:
            row[flag+'_records']=int(cell[flag].sum()) if flag in cell else 0
        for context in CONTEXT:
            if cell[context].nunique()!=1:raise ValueError('Conflicting club context')
            row[context]=cell[context].iloc[0]
        for metric in metrics:
            ok=cell[metric].notna()&mins.gt(0)
            row[metric]=np.average(cell.loc[ok,metric],weights=mins[ok]) if ok.any() else np.nan
            row[metric+'_records']=int(ok.sum())
            row[metric+'_minutes']=float(mins[ok].sum())
        rows.append(row)
    return pd.DataFrame(rows)


def team_associations(teams,metrics):
    rows=[]
    for key,cell in teams.groupby(['league','season','role','source_variant']):
        for metric,context in itertools.product(metrics,CONTEXT):
            n,rho,status=association(cell,metric,context)
            rows.append(dict(zip(['league','season','role','source_variant'],key),
                domain=cell.domain.iloc[0],metric=metric,context=context,paired_clubs=n,
                spearman=rho,status=status,unit='one club-role-source observation'))
    return pd.DataFrame(rows)


def show_examples(overlaps,context):
    sample=overlaps.loc[overlaps.league.eq('Premier League')&overlaps.season.eq('2024-25')]
    choices=[('ST','goals_per90','non_penalty_goals_per90'),('CM','xa_per90','xag_per90'),
             ('GK','shots_on_target_against_per90','saves_per90'),
             ('CB','tackles_per90','interceptions_per90'),('CM','progressive_passes_per90','goals_per90')]
    lines=[]
    for role,left,right in choices:
        hit=sample.loc[sample.role.eq(role)&(((sample.left_metric==left)&(sample.right_metric==right))|((sample.left_metric==right)&(sample.right_metric==left)))]
        for row in hit.to_dict('records'):
            lines.append(f"| {role} | {left} / {right} | {row['paired_records']} | {row['spearman']:.3f} |")
    team_sample=context.loc[context.league.eq('Premier League')&context.season.eq('2024-25')&context.context.eq(CONTEXT[0])]
    team_lines=[]
    for role,metric in [('CB','tackles_per90'),('CB','interceptions_per90'),('GK','saves_per90')]:
        for row in team_sample.loc[team_sample.role.eq(role)&team_sample.metric.eq(metric)].to_dict('records'):
            team_lines.append(f"| {role} | {metric} | {row['paired_clubs']} | {row['spearman']:.3f} |")
    return lines,team_lines


def run():
    outfield,keeper,accounting,lineage=load_cohorts()
    source=ROOT/'reports/explorer/data.json'
    records=json.loads(source.read_text(encoding='utf-8'))['records']
    frames=attach_context(outfield,keeper,records)
    metrics=[['goals_per90','assists_per90',*[m+'_per90' for m in OUTFIELD_METRICS],*EXTRA],KEEPER_METRICS]
    overlaps=pd.concat([overlap(f,m) for f,m in zip(frames,metrics)],ignore_index=True)
    aggregates=[team_aggregates(f,[m for m in ms if m!='crosses_stopped_share']) for f,ms in zip(frames,metrics)]
    contexts=pd.concat([team_associations(t,[m for m in ms if m!='crosses_stopped_share']) for t,ms in zip(aggregates,metrics)],ignore_index=True)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    accounting.to_csv(OUTPUT/'cohort_accounting.csv',index=False)
    counts=pd.concat(frames,ignore_index=True).groupby(['domain','league','season','role','context_link'],dropna=False).size().rename('records').reset_index()
    counts.to_csv(OUTPUT/'role_and_context_coverage.csv',index=False)
    overlaps.to_csv(OUTPUT/'within_context_overlap.csv',index=False)
    coverage=[]
    for frame,ms in zip(frames,metrics):
        for key,cell in frame.groupby(['domain','league','season']):
            for m in ms:
                coverage.append(dict(zip(['domain','league','season'],key),metric=m,
                    source_field=EXTRA.get(m,'existing audited domain metric'),
                    included_records=len(cell),available_records=int(cell[m].notna().sum())))
    pd.DataFrame(coverage).to_csv(OUTPUT/'metric_coverage.csv',index=False)
    contexts.to_csv(OUTPUT/'team_context_associations.csv',index=False)
    pd.concat(aggregates,ignore_index=True).to_csv(OUTPUT/'club_role_metric_aggregates.csv',index=False)
    # Display distributions of cell correlations rather than pooling players from
    # different leagues/seasons into one correlation.
    summary=overlaps.groupby(['domain','left_metric','right_metric']).agg(
        available_cells=('spearman','count'),median_cell_rho=('spearman','median'),
        q25_cell_rho=('spearman',lambda s:s.quantile(.25)),q75_cell_rho=('spearman',lambda s:s.quantile(.75))).reset_index()
    summary.to_csv(OUTPUT/'overlap_cell_summary.csv',index=False)
    examples,team_examples=show_examples(overlaps,contexts)
    missing_roles=sum(f.role.eq('Unavailable').sum() for f in frames)
    missing_context=sum(f.context_team.isna().sum() for f in frames)
    lineage.update(explorer_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        outfield_records=len(frames[0]),keeper_records=len(frames[1]),
        missing_specific_profile_role=int(missing_roles),missing_team_context=int(missing_context),
        correlation_cells=len(overlaps),team_context_cells=len(contexts),formula_finalized=False,
        role_policy='Specific profile proxies, not verified seasonal position minutes; unknowns excluded and counted',
        team_policy='One club-role-source observation per cell; goal rates are outcome context, not direct opportunity denominators',
        psxg_policy='Older-source warned PSxG fills excluded from correlations; other metric-specific warnings retained',
        minimum_pairs=3,minimum_pairs_interpretation='Computability guard only; no reliability or model eligibility claim')
    lineage['additional_original_count_fields']=EXTRA
    (OUTPUT/'lineage.json').write_text(json.dumps(lineage,indent=2),encoding='utf-8')
    report=f'''# Metric usefulness: first diagnostic experiment

Scope: five leagues, eight seasons, 900+ reported-minute exploratory focus.
Included: {len(frames[0]):,} outfield and {len(frames[1]):,} keeper records; these are stints, not unique people.
Unknown specific profile roles: {missing_roles:,}; unavailable team context: {missing_context:,}.
Exclusions and source hashes are retained in the companion CSVs and lineage.

## What these measurements can tell us

Overlap means two measurements often move together within a particular context.
It does not establish how useful either is for player value, or dictate weights.
Low correlation does not prove an independently valuable contribution.

Premier League 2024–25 examples; specific outfield roles are profile proxies:

| Role | Metric pair | Paired records | Spearman |
|---|---|---:|---:|
{chr(10).join(examples)}

## Workload and team context

Keeper saves and shots faced use the same keeper exposure; their association
helps identify workload dependence. Saves are partly contained in shots faced,
so this association is partly mechanical, not proof of shot-stopping ability.
PSxG faced describes workload and shot difficulty, not a direct positive ability bonus.
Reported PSxG residual combines observed outcomes and model expectations; provider
definitions, arithmetic flags and unresolved model versions remain important.

The following club-level correlations use each club once within role/source,
not every teammate as independent evidence. Rates average compatible eligible
player stints with minutes as exposure. Clubs have equal weight in correlations.
Cross-stopping shares are omitted from these aggregates because they need crosses,
not minutes, as the denominator. None of these rates has been opportunity-adjusted.

| Role | Metric versus team goals conceded/match | Paired clubs | Spearman |
|---|---|---:|---:|
{chr(10).join(team_examples)}

Team goals conceded is an outcome-context proxy, not possession, opponent touches,
shots allowed during this player's actual minutes, or causal defensive difficulty.
These team-season figures include minutes when the player was absent. Shared
outcomes and player actions can influence each other. No team adjustment is fitted.

## Contributions beyond goals and assists

The experiment also includes original recorded blocks, recoveries, aerial duels
won/lost, key passes, progressive receptions, passes into the box, dispossessions,
miscontrols and errors. These rates are recomputed from counts and reported minutes;
coverage by every league-season is exported. Definition/version comparability is
not independently established. Recorded errors are a narrow provider category,
not a complete measure of bad decisions. Missing counts remain missing.

Progressive passes/carries, tackles/interceptions and keeper sweeping/cross stopping
describe additional recorded actions. They need location, pressure, possession
opportunity and subsequent state to establish contribution value. Avoid awarding
fixed bonuses for counts. Missing off-ball prevention is not zero contribution.
No demonstrated predictive usefulness, causal effect or incremental player value
is claimed from these descriptive correlations.

## What remains open

Specific profile labels can reflect another point in a career; they do not establish
historical main positions. Unknown roles are counted, not replaced with broad labels.
The three-pair guard only permits calculation. Small cells remain visibly small;
there are no significance claims, uncertainty intervals or selected features here.
Cells and seasons are dependent, so median cell correlations are descriptive only.
All COVID seasons remain. No WAR weights, replacement pool, league multiplier,
position bonus or final formula has been selected.

Next discussion: choose a bounded pilot with direct event/opportunity evidence,
or a clearly limited team-season prototype. Either requires held-out validation
before calling any measure useful for contribution estimation.
'''
    (OUTPUT/'results.md').write_text(report,encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
    for ax,(role,left,right,title) in zip(axes,[('GK','shots_on_target_against_per90','saves_per90','Keeper workload: Premier League 2024–25'),('CB','tackles_per90','interceptions_per90','Recorded defensive actions: CB profile proxies')]):
        f=frames[1] if role=='GK' else frames[0]
        cell=f.loc[f.league.eq('Premier League')&f.season.eq('2024-25')&f.role.eq(role)]
        ax.scatter(cell[left],cell[right],color='#2474b3',alpha=.75)
        n,rho,_=association(cell,left,right)
        ax.set(title=title+'\n'+f'n={n}, Spearman={rho:.3f}',xlabel=left.replace('_',' '),ylabel=right.replace('_',' '))
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Descriptive associations; no weights or player-value claims')
    fig.savefig(OUTPUT/'metric_diagnostics.png',dpi=160)
    plt.close(fig)
    print(report)
    return overlaps,contexts,lineage


if __name__=='__main__':run()
