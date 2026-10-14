"""Render an explicitly scoped first look from the executed analysis reports."""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from analysis_tracks import ROOT, OUTPUT


def main():
    positions=pd.read_csv(OUTPUT/'position_metric_distributions.csv')
    overlaps=pd.read_csv(OUTPUT/'within_context_metric_overlap.csv')
    keeper=pd.read_csv(ROOT/'reports/keeper_exploration/record_metrics_and_warnings.csv')
    lineage=json.loads((OUTPUT/'lineage.json').read_text(encoding='utf-8'))
    keeper_summary=json.loads((ROOT/'reports/keeper_exploration/summary.json').read_text(encoding='utf-8'))
    if keeper_summary['input_sha256']!=lineage['keeper_sha256']:
        raise ValueError('Keeper figure data and shared analysis use different snapshots')
    league,season='Premier League','2024-25'
    cell=positions.loc[positions.league.eq(league)&positions.season.eq(season)]
    order=['DF','MF','FW']
    labels=['DF (114 records)','MF (62 records)','FW (43 records)']
    colors=['#477bb1','#559970','#ce9250']
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for ax,metric,title in zip(axes.flat[:3],
        ['npxg_per90','progressive_passes_per90','tackles_per90'],
        ['Attacking: median npxG / 90','Progression: median progressive passes / 90',
         'Defensive activity: median tackles / 90']):
        rows=cell.loc[cell.position.isin(order)&cell.metric.eq(metric)].set_index('position').reindex(order)
        values=rows['median'].to_numpy()
        bars=ax.bar(labels,values,color=colors,width=.6)
        ax.bar_label(bars,labels=[f'{value:.3f}' for value in values],padding=3)
        ax.set_ylim(0,max(values)*1.25)
        ax.grid(axis='y',alpha=.2)
        ax.set_title(title)
        ax.set_axisbelow(True)
    group=keeper.loc[keeper.eligible&keeper.league.eq(league)&keeper.season.eq(season)]
    ax=axes[1,1]
    ax.scatter(group.shots_on_target_against_per90,group.saves_per90,color='#7b629c',alpha=.85)
    row=overlaps.loc[overlaps.league.eq(league)&overlaps.season.eq(season)&overlaps.position.eq('GK')
        &overlaps.left_metric.eq('shots_on_target_against_per90')&overlaps.right_metric.eq('saves_per90')]
    if len(row)!=1 or int(row.iloc[0].paired_records)!=len(group):
        raise ValueError('GK association differs from selected cohort')
    ax.set_title(f'GK: saves and opportunities (n={len(group)}, rank correlation={row.iloc[0].spearman:.3f})')
    ax.set_xlabel('Shots on target faced / 90')
    ax.set_ylabel('Saves / 90')
    ax.grid(alpha=.2)
    fig.suptitle('Premier League 2024–25: position descriptions including GK\n'
        '900+ reported minutes per club stint; broad positions are provisional',fontsize=14)
    fig.text(.5,.015,'Mixed outfield labels remain in the full report. Different panel units are not a shared value scale.\n'
        'Source versions remain unconfirmed; correlations do not choose weights or estimate player value.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.07,1,.92))
    target=OUTPUT/'first_results.png'
    fig.savefig(target,dpi=150)
    plt.close(fig)
    report='''# Executed analysis: first results

Both notebooks executed successfully. Full scope is Big Five leagues, 2017-18 through 2024-25. The shared analysis includes 11,889 outfield and 959 GK player-club-season records, at the approved 900+ reported-minute focus. These are not unique people or a replacement pool.

This first readable example uses Premier League 2024-25. DF/MF/FW are provisional broad source labels; mixed labels remain separately available in the full tables. No LB/RB/CB/wingback identities were fabricated.

| Position | Records | Median npxG/90 | Median progressive passes/90 | Median tackles/90 |
|---|---:|---:|---:|---:|
| DF | 114 | 0.043 | 3.318 | 1.629 |
| MF | 62 | 0.077 | 4.367 | 2.300 |
| FW | 43 | 0.358 | 2.145 | 0.912 |

GK has 26 included records: median shots on target faced/90 = 4.217, saves/90 = 2.838, PSxG faced/90 = 1.328, reported PSxG residual/90 = 0.029, crosses stopped/faced = 6.0%, and outside-box keeper actions/90 = 1.076. All are descriptive source measurements, with unconfirmed model versions. They are not equivalent units to outfield metrics or verified player effects on team points.

Within this league-season, goals and non-penalty goals have Spearman correlation 0.968 among FW (43 pairs); xA and xAG correlate at 0.905 among MF (62 pairs); shots faced and saves correlate at 0.921 among GK (26 pairs). Related metrics can overlap, and counts depend on opportunities. These associations do not determine weights, causal effects or a replacement baseline. Goal credit will not be suppressed just to balance positions.

Interpretation: different positions show different observed profiles. More tackles or saves are not automatically more valuable; opportunities, locations, teammates, opponents and tactical context need investigation. This is a reason to examine role-relevant contribution evidence, not to assign arbitrary bonuses.

No combined score or FutWAR formula was calculated. The original position and source warnings remain. The full notebook reports cover all positions, league-season cells and available pairs; this example does not change the research scope.

Reproduce after executing both notebooks from the project root in PowerShell:

```powershell
& 'C:\\Users\\mikey\\AppData\\Local\\Programs\\Python\\Python313\\python.exe' scripts/show_analysis_results.py
```
'''
    (OUTPUT/'first_results.md').write_text(report,encoding='utf-8')
    print(target)
    print(OUTPUT/'first_results.md')


if __name__=='__main__':
    main()
