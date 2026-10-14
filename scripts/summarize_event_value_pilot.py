"""Summarize the held-out event-danger pilot; not a player score or WAR."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / 'reports/event_value_pilot/prediction_metrics.csv'
OUT = ROOT / 'reports/event_value_pilot'


def main():
    frame = pd.read_csv(IN)
    test = frame.loc[frame.split.eq('test')].copy()
    rows = []
    for (target, league), cell in test.groupby(['target', 'league'], sort=False):
        base = cell.iloc[0]
        for metric in ['brier', 'log_loss']:
            baseline = float(base[f'constant_{metric}'])
            for model in ['location_context', 'event_history']:
                observed = float(cell.loc[cell.model.eq(model), metric].iloc[0])
                rows.append(dict(target=target, league=league, metric=metric,
                                 model=model, baseline=baseline, model_error=observed,
                                 error_reduction_pct=100 * (baseline-observed)/baseline,
                                 states=int(base.states)))
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / 'heldout_error_improvement.csv', index=False, float_format='%.6f')

    leagues = ['All five', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
    labels = ['All five', 'Premier\nLeague', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), sharex='col')
    palette = {'location_context': '#c7a990', 'event_history': '#148b86'}
    for row, target in enumerate(['score', 'concede']):
        for col, metric in enumerate(['brier', 'log_loss']):
            ax = axes[row, col]
            group = summary.loc[(summary.target.eq(target)) & summary.metric.eq(metric)]
            x = np.arange(len(leagues)); width = .34
            for j, model in enumerate(['location_context', 'event_history']):
                values = [float(group.loc[(group.league.eq(l)) & group.model.eq(model), 'error_reduction_pct'].iloc[0]) for l in leagues]
                ax.bar(x + (j-.5)*width, values, width, label=model.replace('_', ' '),
                       color=palette[model])
            ax.axhline(0, color='#5c514a', linewidth=.8)
            ax.set_title(f'{target.title()} prediction · {metric.replace("_", " ")} error')
            ax.set_ylabel('Error reduction vs constant-rate baseline (%)')
            ax.grid(axis='y', alpha=.2)
            if row == 1:
                ax.set_xticks(x, labels)
            if row == 0 and col == 0:
                ax.legend(frameon=False, ncol=2, loc='upper right')
    fig.suptitle('Held-out March–May 2018 event states · predictive diagnostic only', y=.99)
    fig.text(.5, .015, 'Positive bars indicate lower error. Event rows overlap within fixtures; this is not independent evidence per player.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, .96))
    fig.savefig(OUT / 'heldout_error_improvement.png', dpi=170)
    plt.close(fig)
    print(summary.query("league == 'All five'").to_string(index=False))


if __name__ == '__main__':
    main()
