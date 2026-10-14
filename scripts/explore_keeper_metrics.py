"""Descriptive goalkeeper domains with explicit exposure, missingness and warnings."""
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'reports/keeper_exploration'
METRICS = ['shots_on_target_against_per90', 'saves_per90', 'psxg_per90',
           'reported_residual_per90', 'pass_attempts_per90', 'crosses_faced_per90',
           'crosses_stopped_share', 'sweeper_actions_per90']
LABELS = ['Shots on target faced / 90', 'Saves / 90', 'PSxG / 90 (difficulty faced)',
          'Reported PSxG residual / 90', 'Pass attempts / 90 (definitions vary)',
          'Crosses faced / 90', 'Crosses stopped / crosses faced', 'Outside-box actions / 90']


def load_inputs():
    path = ROOT/'data/processed/keeper_archives/keeper_seasons_analysis.csv'
    lineage = json.loads(path.with_name('psxg_correction_lineage.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != lineage['output_sha256']:
        raise ValueError('Keeper analysis snapshot differs from corrected lineage')
    frame = pd.read_csv(path)
    if len(frame) != 1662 or frame.keeper_record_id.duplicated().any():
        raise ValueError('Unexpected keeper row scope')
    if frame.groupby(['league','season']).ngroups != 40:
        raise ValueError('Missing league-season cells')
    return frame, digest


def prepare(frame, minimum_minutes=900):
    if minimum_minutes <= 0:
        raise ValueError('Positive descriptive cutoff required')
    frame = frame.copy()
    frame['eligible'] = frame.nominal_position.eq('GK') & frame.keeper_minutes.ge(minimum_minutes)
    frame['has_diagnostic_flag'] = frame.unresolved_quality_flags.ne('[]')
    frame['has_exposure_warning'] = frame.exposure_correction_warnings.ne('[]')
    frame['has_psxg_warning'] = frame.psxg_correction_warnings.ne('[]')
    frame['psxg_measurement_source'] = frame.source_variant
    for ix, value in frame.psxg_correction_provenance.dropna().items():
        if value:
            frame.loc[ix, 'psxg_measurement_source'] = json.loads(value)['source_variant'] + '_approved_fill'
    flags = frame.unresolved_quality_flags.map(json.loads)
    arithmetic_bad = flags.map(lambda values: 'reported_psxg_residual_arithmetic_review' in values)
    pairs = dict(shots_on_target_against_per90='shots_on_target_against', saves_per90='saves',
        psxg_per90='psxg', reported_residual_per90='reported_psxg_delta',
        pass_attempts_per90='pass_attempts', crosses_faced_per90='crosses_faced',
        sweeper_actions_per90='sweeper_actions')
    valid_minutes = frame.keeper_minutes.where(frame.keeper_minutes.gt(0))
    for metric, source in pairs.items():
        frame[metric] = 90 * frame[source] / valid_minutes
    frame.loc[arithmetic_bad, 'reported_residual_per90'] = np.nan
    valid_crosses = frame.crosses_faced.gt(0) & frame.crosses_stopped.ge(0) & frame.crosses_stopped.le(frame.crosses_faced)
    frame['crosses_stopped_share'] = frame.crosses_stopped.div(frame.crosses_faced).where(valid_crosses)
    # A missing value never becomes zero. Source/scope warnings remain visible.
    return frame


def reports(frame, digest):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    exclusions, coverage, distributions = [], [], []
    for (league, season), group in frame.groupby(['league','season']):
        cohort = group.loc[group.eligible]
        exclusions.append(dict(league=league, season=season, all_records=len(group),
            non_gk_records=int(group.nominal_position.ne('GK').sum()),
            missing_minutes=int(group.keeper_minutes.isna().sum()),
            gk_below_900=int((group.nominal_position.eq('GK') & group.keeper_minutes.lt(900)).sum()),
            eligible_records=len(cohort), excluded_records=int((~group.eligible).sum()),
            eligible_with_diagnostic_flag=int(cohort.has_diagnostic_flag.sum()),
            eligible_with_exposure_warning=int(cohort.has_exposure_warning.sum()),
            eligible_with_psxg_warning=int(cohort.has_psxg_warning.sum())))
        for metric in METRICS:
            values = cohort[metric].dropna()
            coverage.append(dict(league=league, season=season, metric=metric,
                eligible_records=len(cohort), usable_values=len(values), unavailable_values=int(cohort[metric].isna().sum())))
        for (source, psxg_source), subgroup in cohort.groupby(['source_variant','psxg_measurement_source']):
            for metric in METRICS:
                values = subgroup[metric].dropna()
                distributions.append(dict(league=league, season=season, source_variant=source,
                    psxg_measurement_source=psxg_source, metric=metric, records=len(values),
                    median=values.median(), q25=values.quantile(.25), q75=values.quantile(.75)))
    exclusions, coverage, distributions = map(pd.DataFrame, [exclusions, coverage, distributions])
    exclusions.to_csv(OUTPUT/'exclusions.csv', index=False)
    coverage.to_csv(OUTPUT/'metric_coverage.csv', index=False)
    distributions.to_csv(OUTPUT/'distributions_by_source.csv', index=False)
    frame.to_csv(OUTPUT/'record_metrics_and_warnings.csv', index=False)
    summary = dict(input_sha256=digest, all_records=len(frame), eligible_records=int(frame.eligible.sum()),
        excluded_records=int((~frame.eligible).sum()), cells=len(exclusions), cutoff_minutes=900,
        eligible_missing_psxg=int((frame.eligible & frame.psxg.isna()).sum()),
        eligible_arithmetic_residual_exclusions=int((frame.eligible & frame.reported_psxg_delta.notna()
            & frame.reported_residual_per90.isna()).sum()),
        eligible_exposure_warning_records=int((frame.eligible & frame.has_exposure_warning).sum()),
        eligible_psxg_warning_records=int((frame.eligible & frame.has_psxg_warning).sum()),
        metric_versions_confirmed=False, war_calculated=False)
    (OUTPUT/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return exclusions, coverage, distributions, summary


def plot_domains(frame):
    cohort = frame.loc[frame.eligible]
    fig, axes = plt.subplots(4,2,figsize=(14,17))
    for ax, metric, label in zip(axes.flat, METRICS, LABELS):
        groups, names = [], []
        source_column = 'psxg_measurement_source' if metric == 'psxg_per90' else 'source_variant'
        for (season, source), group in cohort.groupby(['season', source_column]):
            values = group[metric].dropna()
            if len(values):
                groups.append(values.to_numpy())
                names.append(f'{season}\n{source.replace("worldfootballR_", "")}')
        if groups:
            ax.boxplot(groups, tick_labels=names, showfliers=True)
        ax.tick_params(axis='x', labelrotation=70, labelsize=7)
        ax.set_title(label)
        ax.grid(axis='y', alpha=.2)
    fig.suptitle('Descriptive keeper distributions: nominal GK, 900+ reported minutes\n'
        'Player–club–season records; source versions unconfirmed; no league-strength or WAR inference', fontsize=13)
    fig.tight_layout(rect=(0,0,1,.96))
    fig.savefig(OUTPUT/'keeper_domains.png', dpi=150)
    plt.close(fig)
    return OUTPUT/'keeper_domains.png'
