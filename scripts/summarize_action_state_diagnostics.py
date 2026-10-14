"""Summarize held-out expected-points action deltas by Wyscout event type.

Descriptive audit only; does not aggregate player value or create WAR inputs.
"""
import json
import sys
import zipfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/expected_points_pilot/heldout_event_state_changes.csv'
ARCHIVE = ROOT / 'data/raw/wyscout_research/2026-10-10'
OUT = ROOT / 'reports/expected_points_pilot'
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_wyscout_research import LEAGUES, archive_rows, verify


def main():
    frame = pd.read_csv(SOURCE)
    metric = 'state_change_expected_points'
    summary = frame.groupby('event_type_name', dropna=False).agg(
        events=(metric, 'size'),
        mean_change=(metric, 'mean'),
        median_change=(metric, 'median'),
        q10=(metric, lambda values: values.quantile(.10)),
        q90=(metric, lambda values: values.quantile(.90)),
        exact_zero=(metric, lambda values: (values == 0).mean()),
        near_zero=(metric, lambda values: (values.abs() < .005).mean()),
        zero_player_id=('player_id', lambda values: (values.fillna(0) == 0).sum()),
        distinct_nonzero_ids=('player_id', lambda values: values[values.fillna(0) != 0].nunique())
    ).reset_index().sort_values('events', ascending=False)
    summary.to_csv(OUT / 'action_state_by_event_type.csv', index=False, float_format='%.7f')

    # A necessary sanity check: link the sampled shots back to the immutable
    # source tags to see whether the model reacts to recorded goals.
    frame[['country', 'match_id', 'event_id']] = frame.sample_id.str.split(':', expand=True)
    frame['match_id'] = frame.match_id.astype(int)
    frame['event_id'] = frame.event_id.astype(int)
    manifest = json.loads((ROOT / 'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    verify(manifest)
    goal_rows = []
    with zipfile.ZipFile(ARCHIVE / 'events.zip') as event_zip:
        for country, (_, league) in LEAGUES.items():
            for event in archive_rows(event_zip, f'events_{country}.json'):
                tags = {tag['id'] for tag in event.get('tags', [])}
                if event.get('eventName') == 'Shot' and (101 in tags or 102 in tags):
                    goal_rows.append((country, int(event['matchId']), int(event['id']),
                                      'goal' if 101 in tags else 'own_goal'))
    goals = pd.DataFrame(goal_rows, columns=['country', 'match_id', 'event_id', 'goal_tag'])
    goal_sample = frame.merge(goals, on=['country', 'match_id', 'event_id'], how='inner')
    goal_summary = goal_sample.groupby(['goal_tag', 'league']).agg(
        sampled_goals=('event_id', 'size'),
        mean_before=('expected_points_before', 'mean'),
        mean_after=('expected_points_after', 'mean'),
        mean_change=(metric, 'mean'),
        median_change=(metric, 'median'),
        positive_change=(metric, lambda values: values.gt(0).mean())
    ).reset_index()
    goal_summary.to_csv(OUT / 'goal_event_sanity_check.csv', index=False, float_format='%.7f')

    display = summary.sort_values('mean_change')
    fig, ax = plt.subplots(figsize=(10, 6.5))
    y = range(len(display))
    lower = display.median_change - display.q10
    upper = display.q90 - display.median_change
    ax.errorbar(display.median_change, y, xerr=[lower, upper], fmt='o', color='#16877f',
                ecolor='#c9ab96', capsize=3, markersize=5)
    ax.axvline(0, linestyle='--', color='#5f5a55', linewidth=1)
    ax.set_yticks(list(y), [f"{name}  (n={count:,})" for name, count in
                            zip(display.event_type_name, display.events)])
    ax.set_xlabel('Median modeled EP change · whiskers show 10th–90th percentiles')
    ax.set_title('Held-out action-state changes by event type · 2017–18')
    ax.grid(axis='x', alpha=.2)
    fig.text(.5, .01, 'Each event is sampled (every third raw event); not player value or WAR. '
             'Interruption playerId=0 is a source sentinel, not a player link.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(OUT / 'action_state_by_event_type.png', dpi=170)
    plt.close(fig)

    print(summary.to_string(index=False, float_format=lambda value: f'{value:.5f}'))
    print('\nGoal-tagged shots by league:')
    print(goal_summary.to_string(index=False, float_format=lambda value: f'{value:.5f}'))
    print(f"Rows={len(frame):,}; median={frame[metric].median():.6f}; "
          f"mean={frame[metric].mean():.6f}; exact-zero={frame[metric].eq(0).mean():.1%}; "
          f"near-zero(|delta|<0.005)={frame[metric].abs().lt(.005).mean():.1%}; "
          f"playerId=0={(frame.player_id.fillna(0) == 0).sum():,}")


if __name__ == '__main__':
    main()
