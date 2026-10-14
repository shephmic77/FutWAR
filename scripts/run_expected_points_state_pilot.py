"""Match-state expected-points pilot. Event changes are not player WAR/causal effects."""
import csv
import json
import os
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

os.environ.setdefault('OMP_NUM_THREADS', '4')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import log_loss
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from joblib import dump

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_wyscout_research import LEAGUES, archive_rows, verify
from run_event_value_pilot import event_vector, scoring_team, split_for, FEATURES

SOURCE = ROOT / 'data/raw/wyscout_research/2026-10-10'
OUT = ROOT / 'reports/expected_points_pilot'
LABELS = [0, 1, 3]
STATE_FEATURES = ['league_code', 'seconds', 'period', 'score_difference', 'total_goals',
                  'team_home', 'prior_points_difference', 'prior_goal_difference']
ALL_FEATURES = [*FEATURES, *[name for name in STATE_FEATURES if name not in FEATURES]]
CATEGORICAL = ['event_type', 'subevent_type', 'period', 'previous_type',
               'second_previous_type', 'league_code']
SMOOTH_NUMERIC = ['remaining_minutes', 'score_difference', 'score_x_remaining',
                  'score_difference_sq', 'total_goals', 'team_home',
                  'prior_points_difference', 'prior_goal_difference']
SMOOTH_FEATURES = ['league_code', *SMOOTH_NUMERIC]


def add_smooth_features(frame):
    result = frame.copy()
    result['remaining_minutes'] = (90 - (result['period'] - 1) * 45 - result['seconds'] / 60).clip(0, 90)
    result['score_x_remaining'] = result['score_difference'] * result['remaining_minutes'] / 90
    result['score_difference_sq'] = result['score_difference'] ** 2
    return result


def make_smooth_state_model():
    transformer = ColumnTransformer([
        ('league', OneHotEncoder(handle_unknown='ignore'), ['league_code']),
        ('numeric', StandardScaler(), SMOOTH_NUMERIC)
    ])
    return Pipeline([('features', transformer),
                     ('outcome', LogisticRegression(C=1.0, max_iter=500, solver='lbfgs'))])


def expected_points(probabilities, classes):
    mapping = dict(zip(classes, probabilities))
    return float(3 * mapping.get(3, 0.0) + mapping.get(1, 0.0))


def outcome_points(team, score_by_team):
    values = list(score_by_team.values())
    own = score_by_team[team]
    other = sum(values) - own
    return 3 if own > other else 1 if own == other else 0


def before_vector(after):
    values = list(after)
    # The pre-action state knows the ball's start location and clock, but not the
    # action's type, destination or accuracy. Zero is a reserved pre-action code.
    values[0] = 0
    values[1] = 0
    values[4] = values[2]
    values[5] = values[3]
    values[6] = np.nan
    values[7] = np.nan
    return values


def add_context(vector, league_code, event, score_before, score_after, team_home,
                prior_points_difference, prior_goal_difference):
    result = dict(zip(FEATURES, vector))
    result.update(league_code=league_code,
                 seconds=float(event['eventSec']),
                 period=1 if event['matchPeriod'] == '1H' else 2,
                 score_difference=float(score_after[0]),
                 total_goals=float(score_after[1]),
                 team_home=float(team_home),
                 prior_points_difference=float(prior_points_difference),
                 prior_goal_difference=float(prior_goal_difference))
    return result


def manual_log_loss(actual, probabilities, classes):
    return float(log_loss(actual, probabilities, labels=classes))


def align_heldout_metadata(frame, ordered_sample_ids):
    metadata = (frame[frame.split.eq('test') & frame.state.eq('after')]
                .drop_duplicates('sample_id').set_index('sample_id'))
    aligned = metadata.reindex(ordered_sample_ids)
    if metadata.index.has_duplicates or aligned.event_type_name.isna().any():
        raise ValueError('Held-out metadata did not align one-to-one with paired states')
    return aligned


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    hashes = verify(manifest)
    rows = []
    audit = []
    invalid_position_points = 0
    form = defaultdict(lambda: {'matches': 0, 'points': 0, 'gf': 0, 'ga': 0})

    with zipfile.ZipFile(SOURCE / 'events.zip') as event_zip, zipfile.ZipFile(SOURCE / 'matches.zip') as match_zip:
        for league_code, (country, (league_id, league)) in enumerate(LEAGUES.items()):
            matches = list(archive_rows(match_zip, f'matches_{country}.json'))
            matches.sort(key=lambda match: (match['dateutc'], int(match['wyId'])))
            events_by_match = defaultdict(list)
            for event in archive_rows(event_zip, f'events_{country}.json'):
                events_by_match[int(event['matchId'])].append(event)

            for match in matches:
                match_id = int(match['wyId'])
                teams = tuple(int(team) for team in match['teamsData'])
                side_by_team = {int(team): item['side'] for team, item in match['teamsData'].items()}
                home_team = next(team for team, side in side_by_team.items() if side == 'home')
                source_scores = {int(team): int(item['score']) for team, item in match['teamsData'].items()}
                pre_form = {team: form[team].copy() for team in teams}
                date = match['dateutc'][:10]
                split = split_for(date)
                events = events_by_match.get(match_id, [])
                events = sorted(enumerate(events), key=lambda pair: (
                    {'1H': 1, '2H': 2}.get(pair[1]['matchPeriod'], 99), pair[1]['eventSec'], pair[0]))
                events = [event for _, event in events]

                reasons = []
                reconstructed = {team: 0 for team in teams}
                for event in events:
                    for point in event.get('positions', []):
                        x, y = point.get('x'), point.get('y')
                        if x is not None and y is not None and (not 0 <= x <= 100 or not 0 <= y <= 100):
                            invalid_position_points += 1
                    try:
                        scorer = scoring_team(event, teams)
                    except (KeyError, ValueError):
                        reasons.append('unknown_event_team')
                        continue
                    if scorer is not None:
                        reconstructed[scorer] += 1
                if reconstructed != source_scores:
                    reasons.append('goal_score_mismatch')
                if not events:
                    reasons.append('no_events')
                if any(event['matchPeriod'] not in ('1H', '2H') or event['eventSec'] < 0
                       for event in events):
                    reasons.append('period_or_time_invalid')
                audit.append(dict(league=league, match_id=match_id, date=date,
                                  source_score=json.dumps(source_scores),
                                  reconstructed_score=json.dumps(reconstructed),
                                  events=len(events), status='excluded' if reasons else 'included',
                                  reasons=';'.join(sorted(set(reasons)))))

                # Prior form uses only previously completed fixtures, including
                # the official result of any event-excluded earlier fixture.
                for team, opponent in ((teams[0], teams[1]), (teams[1], teams[0])):
                    record = form[team]
                    foe_record = form[opponent]
                    prior_points_diff = (record['points'] / record['matches'] if record['matches'] else 0) - (
                        foe_record['points'] / foe_record['matches'] if foe_record['matches'] else 0)
                    prior_gd_diff = (record['gf'] - record['ga']) / record['matches'] if record['matches'] else 0
                    prior_gd_diff -= (foe_record['gf'] - foe_record['ga']) / foe_record['matches'] if foe_record['matches'] else 0
                    match['_prior_context', team] = (prior_points_diff, prior_gd_diff)

                if not reasons:
                    score = {team: 0 for team in teams}
                    for index, event in enumerate(events):
                        team = int(event.get('teamId', -1))
                        if team not in teams:
                            continue
                        score_before = score[team] - score[teams[1] if team == teams[0] else teams[0]]
                        total_before = sum(score.values())
                        before_state = (score_before, total_before)
                        try:
                            scorer = scoring_team(event, teams)
                        except (KeyError, ValueError):
                            continue
                        if scorer is not None:
                            score[scorer] += 1
                        opponent = teams[1] if team == teams[0] else teams[0]
                        score_after = (score[team] - score[opponent], sum(score.values()))
                        if index % 3 != 0:
                            continue
                        vector = event_vector(events, index)
                        prior_points_diff, prior_gd_diff = match['_prior_context', team]
                        home = team == home_team
                        before = add_context(before_vector(vector), league_code, event,
                                             before_state, before_state, home,
                                             prior_points_diff, prior_gd_diff)
                        after = add_context(vector, league_code, event,
                                            before_state, score_after, home,
                                            prior_points_diff, prior_gd_diff)
                        target = outcome_points(team, source_scores)
                        common = dict(sample_id=f'{country}:{match_id}:{event.get("id")}',
                                      league=league, match_id=match_id, date=date, split=split,
                                      team_id=team, player_id=event.get('playerId'),
                                      event_id=event.get('id'), event_type_name=event.get('eventName'),
                                      subevent_name=event.get('subEventName'), outcome_points=target,
                                      scoring_event=scorer is not None)
                        rows.append(dict(**common, state='before', **before))
                        rows.append(dict(**common, state='after', **after))

                # Update rolling form only after the fixture, using its published score.
                home_score, away_score = source_scores[home_team], source_scores[next(t for t in teams if t != home_team)]
                for team, own, other in ((home_team, home_score, away_score),
                                         (next(t for t in teams if t != home_team), away_score, home_score)):
                    record = form[team]
                    record['matches'] += 1
                    record['gf'] += own
                    record['ga'] += other
                    record['points'] += 3 if own > other else 1 if own == other else 0
                match.pop(('_prior_context', teams[0]), None)
                match.pop(('_prior_context', teams[1]), None)
            del events_by_match

    pd.DataFrame(audit).to_csv(OUT / 'fixture_audit.csv', index=False)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError('No valid event states')
    frame['target'] = frame['outcome_points'].astype(int)
    frame = add_smooth_features(frame)
    state_only = [*STATE_FEATURES]
    full = ALL_FEATURES
    categorical = [name for name in CATEGORICAL]
    train_all = frame[frame.split == 'train']
    validation = frame[(frame.split == 'validation') & (frame.state == 'after')]
    test = frame[(frame.split == 'test') & (frame.state == 'after')]
    train_ids = train_all['sample_id'].drop_duplicates().sample(
        n=min(80000, train_all['sample_id'].nunique()), random_state=42)
    train = train_all[train_all['sample_id'].isin(train_ids)].sort_index()
    models = {}
    metrics = []
    test_probabilities = {}
    test_ep_predictions = None
    test_ep_actual = None
    train_prevalence = np.array([(train.target == label).mean() for label in LABELS])

    for name, columns in [('constant', None), ('state_only', state_only),
                          ('smooth_state', SMOOTH_FEATURES), ('event_context', full)]:
        if name == 'constant':
            models[name] = None
            for split_name, subset in [('validation', validation), ('test', test)]:
                aligned = np.tile(train_prevalence, (len(subset), 1))
                truth = subset.target.to_numpy()
                one_hot = np.column_stack([truth == label for label in LABELS]).astype(float)
                exp_points = aligned @ np.array(LABELS, dtype=float)
                for league in ['All five', *[value[1] for value in LEAGUES.values()]]:
                    mask = np.ones(len(subset), dtype=bool) if league == 'All five' else subset.league.to_numpy() == league
                    if not mask.any():
                        continue
                    pp, yy, oh = aligned[mask], truth[mask], one_hot[mask]
                    metrics.append(dict(model=name, split=split_name, league=league,
                                        states=int(mask.sum()), observed_mean_points=float(yy.mean()),
                                        predicted_mean_points=float(exp_points[mask].mean()),
                                        expected_points_rmse=float(np.sqrt(np.mean((exp_points[mask] - yy) ** 2))),
                                        multiclass_brier=float(np.mean(np.sum((pp - oh) ** 2, axis=1))),
                                        log_loss=manual_log_loss(yy, pp, LABELS)))
            continue
        if name == 'smooth_state':
            model = make_smooth_state_model()
        else:
            model = HistGradientBoostingClassifier(
                max_iter=80, max_leaf_nodes=15, l2_regularization=1,
                early_stopping=False, random_state=42,
                categorical_features=[column for column in categorical if column in columns])
        model.fit(train[columns], train.target)
        models[name] = model
        if name in ('state_only', 'smooth_state', 'event_context'):
            model_path = ROOT / 'data/processed/value_research' / f'expected_points_{name}.joblib'
            model_path.parent.mkdir(parents=True, exist_ok=True)
            dump({'model': model, 'features': list(columns), 'labels': LABELS}, model_path)
        for split_name, subset in [('validation', validation), ('test', test)]:
            probs = model.predict_proba(subset[columns])
            # Align each model's class order to the explicit point outcome set.
            aligned = np.zeros((len(subset), len(LABELS)), dtype=float)
            for j, label in enumerate(model.classes_):
                aligned[:, LABELS.index(int(label))] = probs[:, j]
            if split_name == 'test':
                test_probabilities[name] = aligned
            truth = subset.target.to_numpy()
            one_hot = np.column_stack([truth == label for label in LABELS]).astype(float)
            exp_points = aligned @ np.array(LABELS, dtype=float)
            if name == 'event_context' and split_name == 'test':
                test_ep_predictions = exp_points
                test_ep_actual = truth.copy()
            for league in ['All five', *[value[1] for value in LEAGUES.values()]]:
                mask = np.ones(len(subset), dtype=bool) if league == 'All five' else subset.league.to_numpy() == league
                if not mask.any():
                    continue
                pp, yy = aligned[mask], truth[mask]
                oh = one_hot[mask]
                metrics.append(dict(model=name, split=split_name, league=league,
                                    states=int(mask.sum()), observed_mean_points=float(yy.mean()),
                                    predicted_mean_points=float(exp_points[mask].mean()),
                                    expected_points_rmse=float(np.sqrt(np.mean((exp_points[mask] - yy) ** 2))),
                                    multiclass_brier=float(np.mean(np.sum((pp - oh) ** 2, axis=1))),
                                    log_loss=manual_log_loss(yy, pp, LABELS)))

    # Event-level before/after delta: it describes modelled state change only.
    test_pairs = frame[frame.split.eq('test')].pivot(index='sample_id', columns='state', values=ALL_FEATURES)
    # pivot sorts sample IDs; reindex metadata to the same order before pairing
    # predictions with source events.
    meta = align_heldout_metadata(frame, test_pairs.index)
    model = models['event_context']
    pre_probs = model.predict_proba(test_pairs.xs('before', axis=1, level=1)[full])
    post_probs = model.predict_proba(test_pairs.xs('after', axis=1, level=1)[full])
    aligned_pre = np.zeros((len(test_pairs), len(LABELS)), dtype=float)
    aligned_post = np.zeros_like(aligned_pre)
    for j, label in enumerate(model.classes_):
        k = LABELS.index(int(label))
        aligned_pre[:, k] = pre_probs[:, j]
        aligned_post[:, k] = post_probs[:, j]
    point_values = np.array(LABELS, dtype=float)
    ep_before = aligned_pre @ point_values
    ep_after = aligned_post @ point_values
    deltas = meta[['league', 'match_id', 'date', 'player_id', 'event_type_name',
                   'subevent_name', 'outcome_points', 'scoring_event']].copy()
    deltas['expected_points_before'] = ep_before
    deltas['expected_points_after'] = ep_after
    deltas['state_change_expected_points'] = ep_after - ep_before
    state_model = models['state_only']
    state_before_features = test_pairs.xs('before', axis=1, level=1)[state_only]
    state_after_features = test_pairs.xs('after', axis=1, level=1)[state_only]
    state_pre_raw = state_model.predict_proba(state_before_features)
    state_post_raw = state_model.predict_proba(state_after_features)
    state_pre = np.zeros((len(test_pairs), len(LABELS)), dtype=float)
    state_post = np.zeros_like(state_pre)
    for j, label in enumerate(state_model.classes_):
        k = LABELS.index(int(label))
        state_pre[:, k] = state_pre_raw[:, j]
        state_post[:, k] = state_post_raw[:, j]
    state_ep_before = state_pre @ point_values
    state_ep_after = state_post @ point_values
    deltas['state_only_ep_before'] = state_ep_before
    deltas['state_only_ep_after'] = state_ep_after
    deltas['state_only_change'] = state_ep_after - state_ep_before
    smooth_model = models['smooth_state']
    smooth_before = add_smooth_features(test_pairs.xs('before', axis=1, level=1))[SMOOTH_FEATURES]
    smooth_after = add_smooth_features(test_pairs.xs('after', axis=1, level=1))[SMOOTH_FEATURES]
    smooth_pre_raw = smooth_model.predict_proba(smooth_before)
    smooth_post_raw = smooth_model.predict_proba(smooth_after)
    smooth_pre = np.zeros((len(test_pairs), len(LABELS)), dtype=float)
    smooth_post = np.zeros_like(smooth_pre)
    for j, label in enumerate(smooth_model.classes_):
        k = LABELS.index(int(label))
        smooth_pre[:, k] = smooth_pre_raw[:, j]
        smooth_post[:, k] = smooth_post_raw[:, j]
    smooth_ep_before = smooth_pre @ point_values
    smooth_ep_after = smooth_post @ point_values
    deltas['smooth_state_ep_before'] = smooth_ep_before
    deltas['smooth_state_ep_after'] = smooth_ep_after
    deltas['smooth_state_change'] = smooth_ep_after - smooth_ep_before
    deltas['goal_shot'] = deltas.event_type_name.eq('Shot') & deltas.scoring_event.astype(bool)
    deltas.reset_index().to_csv(OUT / 'heldout_event_state_changes.csv', index=False, float_format='%.6f')

    comparison_rows = []
    for cohort, mask in [('all sampled events', np.ones(len(deltas), dtype=bool)),
                         ('all shots', deltas.event_type_name.eq('Shot').to_numpy()),
                         ('goal-tagged shots', deltas.goal_shot.to_numpy())]:
        for model_name, values in [('score/time/form', deltas.state_only_change),
                                   ('smooth score-state', deltas.smooth_state_change),
                                   ('event context', deltas.state_change_expected_points)]:
            selected = values[mask]
            comparison_rows.append(dict(cohort=cohort, model=model_name, events=len(selected),
                mean_change=float(selected.mean()), median_change=float(selected.median()),
                positive_change_pct=float(selected.gt(0).mean() * 100),
                exact_zero_pct=float(selected.eq(0).mean() * 100)))
    pd.DataFrame(comparison_rows).to_csv(OUT / 'paired_state_model_sanity.csv', index=False,
                                         float_format='%.6f')

    by_type = deltas.groupby(['event_type_name', 'subevent_name'], dropna=False).agg(
        sampled_events=('state_change_expected_points', 'size'),
        mean_change=('state_change_expected_points', 'mean'),
        median_change=('state_change_expected_points', 'median'),
        q25=('state_change_expected_points', lambda values: values.quantile(.25)),
        q75=('state_change_expected_points', lambda values: values.quantile(.75))).reset_index()
    by_type.to_csv(OUT / 'heldout_state_changes_by_event_type.csv', index=False, float_format='%.6f')

    metrics_frame = pd.DataFrame(metrics)
    metrics_frame.to_csv(OUT / 'prediction_metrics.csv', index=False, float_format='%.6f')
    overall = metrics_frame[(metrics_frame.split == 'test') & (metrics_frame.league == 'All five')]

    # Expected-points calibration over held-out post-action states.
    calibration = pd.DataFrame({'predicted': test_ep_predictions, 'observed': test_ep_actual})
    calibration['decile'] = pd.qcut(calibration['predicted'], q=10, labels=False, duplicates='drop')
    calibration = calibration.groupby('decile', observed=True).agg(
        states=('observed', 'size'), predicted_mean=('predicted', 'mean'),
        observed_mean=('observed', 'mean'), observed_sd=('observed', 'std')).reset_index()
    calibration.to_csv(OUT / 'heldout_expected_points_calibration.csv', index=False, float_format='%.6f')
    fig, ax = plt.subplots(figsize=(7, 6))
    low = min(calibration.predicted_mean.min(), calibration.observed_mean.min())
    high = max(calibration.predicted_mean.max(), calibration.observed_mean.max())
    ax.plot([low, high], [low, high], linestyle='--', color='#81786f', label='Perfect calibration')
    ax.plot(calibration.predicted_mean, calibration.observed_mean, marker='o',
            color='#16877f', label='Event-context model')
    for row in calibration.itertuples():
        ax.annotate(f'n={row.states:,}', (row.predicted_mean, row.observed_mean),
                    xytext=(4, 4), textcoords='offset points', fontsize=8)
    ax.set(xlabel='Mean predicted match points', ylabel='Observed match points',
           title='Held-out expected-points calibration · March–May 2018')
    ax.grid(alpha=.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / 'heldout_expected_points_calibration.png', dpi=170)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, metric, label in [(axes[0], 'expected_points_rmse', 'Expected-points RMSE'),
                              (axes[1], 'multiclass_brier', 'Three-class Brier score')]:
        group = metrics_frame[(metrics_frame.split == 'test') & (metrics_frame.league != 'All five')]
        model_order = ['constant', 'state_only', 'smooth_state', 'event_context']
        piv = group.pivot(index='league', columns='model', values=metric).reindex(
            index=[v[1] for v in LEAGUES.values()], columns=model_order)
        piv.columns = ['Constant outcome', 'Score/time/form trees', 'Smooth score-state', 'Event context']
        piv.plot(kind='bar', ax=ax, color=['#c9ab96', '#647b9a', '#a87954', '#188d86'], rot=25)
        ax.set_title(label)
        ax.set_ylabel('Lower is better')
        ax.set_xlabel('League · held-out test matches')
        ax.grid(axis='y', alpha=.2)
        ax.legend(frameon=False)
    fig.suptitle('Expected-points match-state model · March–May 2018 holdout', y=.99)
    fig.text(.5, .01, 'State-only uses score/time/form; event-context adds action type and location. No player credit is assigned.', ha='center', fontsize=9)
    fig.tight_layout(rect=(0, .05, 1, .94))
    fig.savefig(OUT / 'heldout_match_state_metrics.png', dpi=170)
    plt.close(fig)

    # Distribution view retains every observed event type, and shows quartiles.
    by_type = by_type.sort_values('median_change')
    fig, ax = plt.subplots(figsize=(11, max(6, .28 * len(by_type))))
    y = np.arange(len(by_type))
    lower = by_type['median_change'] - by_type['q25']
    upper = by_type['q75'] - by_type['median_change']
    ax.errorbar(by_type['median_change'], y, xerr=np.vstack([lower, upper]), fmt='o',
                color='#16877f', ecolor='#c9ab96', capsize=2, markersize=4)
    ax.axvline(0, color='#645a53', linestyle='--', linewidth=1)
    ax.set_yticks(y, [f"{r.event_type_name} / {r.subevent_name} (n={r.sampled_events:,})" for r in by_type.itertuples()])
    ax.set_xlabel('Median predicted team expected-points state change · IQR')
    ax.set_title('Exploratory event-state changes · held-out March–May 2018')
    ax.grid(axis='x', alpha=.2)
    fig.tight_layout()
    fig.savefig(OUT / 'heldout_state_changes_by_event_type.png', dpi=170)
    plt.close(fig)

    (OUT / 'run.json').write_text(json.dumps({
        'source_hashes': hashes,
        'eligible_fixture_count': sum(row['status'] == 'included' for row in audit),
        'excluded_fixtures': [row for row in audit if row['status'] == 'excluded'],
        'state_rows_before_after': len(frame),
        'sampled_action_pairs': len(deltas),
        'training_state_rows': len(train),
        'training_action_pairs': int(train['sample_id'].nunique()),
        'validation_after_states': len(validation),
        'test_after_states': len(test),
        'split': {'train': 'before 2018-01-01', 'validation': '2018-01-01 through 2018-02-28', 'test': '2018-03-01 onward'},
        'features': {'state_only': state_only, 'smooth_state': SMOOTH_FEATURES,
                     'event_context': full, 'player_identity_not_a_feature': True},
        'target': 'Final match league points for the event team (0, 1, 3)',
        'training_sample': 'fixed-seed sample of up to 80000 action pairs; both pre-action and post-action states are included',
        'event_change_definition': 'Predicted EP from the pre-action state to the post-action state using the event-context model; event-level descriptive value only.',
        'invalid_coordinate_points': invalid_position_points,
        'coordinate_policy': 'Out-of-pitch coordinate pairs counted and set missing in derived model features; raw source unchanged.',
        'limitations': ['One season and 5 of 40 league-season cells', 'No player credit assigned', 'Not causal impact or WAR', 'Ten-event state predictor was not reused as match result probability', 'Action-state values remain sensitive to event sequence, event attribution and score/time context', 'No verified specific historical positions or keeper/outfield calibration', 'Overlapping states within fixtures are dependent', 'No team-budget replacement pool', 'Pre-match form is prior-season-sample points and goal-difference per match; early records default to neutral zero']
    }, indent=2), encoding='utf-8')
    print('Finished:', len(audit), 'fixtures;', sum(row['status'] == 'excluded' for row in audit),
          'excluded;', train['sample_id'].nunique(), 'training pairs /', len(train),
          'state rows;', len(test), 'test states;', len(deltas), 'held-out action pairs')
    print(overall[['model', 'expected_points_rmse', 'multiclass_brier', 'log_loss']].to_string(index=False))


if __name__ == '__main__':
    main()
