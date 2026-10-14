"""Compare direct and equal-shared credit on held-out shot-ending sequences.

This is a sensitivity diagnostic, not WAR, causal player value, or Shapley value.
Sequence boundaries are conservative proxies derived from raw Wyscout events.
"""
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_wyscout_research import LEAGUES, archive_rows, verify
from run_event_value_pilot import event_vector, scoring_team, split_for
from run_expected_points_state_pilot import add_context, before_vector

SOURCE = ROOT / 'data/raw/wyscout_research/2026-10-10'
MODEL_PATH = ROOT / 'data/processed/value_research/expected_points_event_context.joblib'
AUDIT_PATH = ROOT / 'reports/expected_points_pilot/fixture_audit.csv'
OUT = ROOT / 'reports/action_credit_pilot'
POINTS = np.array([0.0, 1.0, 3.0])
RESTARTS = {'Throw in', 'Free Kick', 'Goal kick', 'Corner', 'Free kick cross',
            'Free kick shot', 'Penalty'}
SEQUENCE_ENDS = {'Shot', 'Foul', 'Interruption', 'Offside'}


def is_shot_ending(event):
    return (event.get('eventName') == 'Shot' or
            (event.get('eventName') == 'Free Kick' and
             event.get('subEventName') in {'Penalty', 'Free kick shot'}))


def possession_proxies(events):
    """Return ordered same-team event runs, ending on shots where applicable."""
    current = []
    previous = None
    for event in events:
        restart = event.get('eventName') == 'Free Kick' and event.get('subEventName') in RESTARTS
        boundary = bool(current) and (
            event.get('matchPeriod') != previous.get('matchPeriod') or
            event.get('teamId') != previous.get('teamId') or
            previous.get('eventName') in SEQUENCE_ENDS or restart)
        if boundary:
            yield current
            current = []
        current.append(event)
        previous = event
    if current:
        yield current


def aligned_probabilities(model, matrix, labels):
    raw = model.predict_proba(matrix)
    aligned = np.zeros((len(matrix), len(labels)), dtype=float)
    for column, label in enumerate(model.classes_):
        aligned[:, labels.index(int(label))] = raw[:, column]
    return aligned


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f'Model artifact missing; run {ROOT / "scripts/run_expected_points_state_pilot.py"}')
    manifest = json.loads((ROOT / 'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    hashes = verify(manifest)
    audit = pd.read_csv(AUDIT_PATH)
    valid_matches = set(audit.loc[audit.status.eq('included'), 'match_id'].astype(int))
    artifact = joblib.load(MODEL_PATH)
    model, features, labels = artifact['model'], artifact['features'], artifact['labels']
    players = json.loads((SOURCE / 'players.json').read_text(encoding='utf-8'))
    profile_ids = {int(player['wyId']) for player in players}

    sequence_rows = []
    pending_actions = []
    form = defaultdict(lambda: {'matches': 0, 'points': 0, 'gf': 0, 'ga': 0})
    test_fixture_count = 0
    with zipfile.ZipFile(SOURCE / 'events.zip') as event_zip, zipfile.ZipFile(SOURCE / 'matches.zip') as match_zip:
        for league_code, (country, (_, league)) in enumerate(LEAGUES.items()):
            matches = archive_rows(match_zip, f'matches_{country}.json')
            matches.sort(key=lambda match: (match['dateutc'], int(match['wyId'])))
            events_by_match = defaultdict(list)
            for event in archive_rows(event_zip, f'events_{country}.json'):
                events_by_match[int(event['matchId'])].append(event)

            for match in matches:
                match_id = int(match['wyId'])
                teams = tuple(int(team) for team in match['teamsData'])
                home_team = next(int(team) for team, item in match['teamsData'].items()
                                 if item['side'] == 'home')
                scores = {int(team): int(item['score']) for team, item in match['teamsData'].items()}
                date = match['dateutc'][:10]
                pre_form = {}
                for team, opponent in ((teams[0], teams[1]), (teams[1], teams[0])):
                    own, foe = form[team], form[opponent]
                    points_diff = own['points'] / own['matches'] if own['matches'] else 0
                    points_diff -= foe['points'] / foe['matches'] if foe['matches'] else 0
                    gd_diff = (own['gf'] - own['ga']) / own['matches'] if own['matches'] else 0
                    gd_diff -= (foe['gf'] - foe['ga']) / foe['matches'] if foe['matches'] else 0
                    pre_form[team] = (points_diff, gd_diff)

                raw = events_by_match.get(match_id, [])
                events = [event for _, event in sorted(enumerate(raw), key=lambda pair: (
                    {'1H': 1, '2H': 2}.get(pair[1].get('matchPeriod'), 99),
                    pair[1].get('eventSec', 0), pair[0]))]
                # Keep historical form chronology identical to the expected-points pilot.
                if split_for(date) == 'test' and match_id in valid_matches:
                    test_fixture_count += 1
                    score = {team: 0 for team in teams}
                    event_state = []
                    for index, event in enumerate(events):
                        team = int(event.get('teamId', -1))
                        if team not in teams:
                            continue
                        opponent = teams[1] if team == teams[0] else teams[0]
                        before = (score[team] - score[opponent], sum(score.values()))
                        scorer = scoring_team(event, teams)
                        if scorer is not None:
                            score[scorer] += 1
                        after = (score[team] - score[opponent], sum(score.values()))
                        event_state.append((before, after))

                    index_by_object = {id(event): index for index, event in enumerate(events)}
                    for sequence_number, sequence in enumerate(possession_proxies(events)):
                        ending_shot = is_shot_ending(sequence[-1])
                        if not ending_shot:
                            continue
                        ids = [int(event.get('playerId') or 0) for event in sequence]
                        distinct_ids = sorted({player_id for player_id in ids if player_id > 0})
                        missing_actor_actions = sum(player_id == 0 for player_id in ids)
                        complete_actor_sequence = missing_actor_actions == 0 and all(
                            player_id in profile_ids for player_id in ids)
                        sequence_key = f'{country}:{match_id}:{sequence_number}'
                        sequence_rows.append(dict(sequence_id=sequence_key, league=league,
                            match_id=match_id, date=date, events=len(sequence),
                            actors=len(distinct_ids), missing_actor_actions=missing_actor_actions,
                            all_actor_ids_in_profile=all(int(event.get('playerId') or 0) in profile_ids
                                                          for event in sequence),
                            eligible_complete_actor_sequence=complete_actor_sequence,
                            sequence_delta_ep=np.nan))
                        if complete_actor_sequence:
                            for event in sequence:
                                index = index_by_object[id(event)]
                                team = int(event['teamId'])
                                prior_points, prior_gd = pre_form[team]
                                pre_state, post_state = event_state[index]
                                vector = event_vector(events, index)
                                before_features = add_context(before_vector(vector), league_code,
                                    event, pre_state, pre_state, team == home_team, prior_points, prior_gd)
                                after_features = add_context(vector, league_code, event,
                                    pre_state, post_state, team == home_team, prior_points, prior_gd)
                                pending_actions.append(dict(sequence_id=sequence_key,
                                    player_id=int(event['playerId']), league=league,
                                    event_name=event.get('eventName'), subevent_name=event.get('subEventName'),
                                    participant_count=len(distinct_ids), before=before_features,
                                    after=after_features))

                # Match the model runner: prior form uses every previously completed
                # fixture's published score, even where its event stream was excluded.
                home_score = scores[home_team]
                away = next(team for team in teams if team != home_team)
                away_score = scores[away]
                for team, own, other in ((home_team, home_score, away_score),
                                         (away, away_score, home_score)):
                    record = form[team]
                    record['matches'] += 1
                    record['gf'] += own
                    record['ga'] += other
                    record['points'] += 3 if own > other else 1 if own == other else 0
            del events_by_match

    sequences = pd.DataFrame(sequence_rows)
    if sequences.empty or not pending_actions:
        raise ValueError('No shot-ending sequences or complete actor sequences found in held-out matches')
    # Batch pre/post inference: the event model is expensive per call, but fast on
    # a matrix. Both credit methods receive exactly the same action deltas.
    before_matrix = pd.DataFrame([row['before'] for row in pending_actions])[features]
    after_matrix = pd.DataFrame([row['after'] for row in pending_actions])[features]
    before_probs = aligned_probabilities(model, before_matrix, labels)
    after_probs = aligned_probabilities(model, after_matrix, labels)
    action_rows = []
    for row, pre, post in zip(pending_actions, before_probs, after_probs):
        action_rows.append(dict(sequence_id=row['sequence_id'], player_id=row['player_id'],
            league=row['league'], event_name=row['event_name'], subevent_name=row['subevent_name'],
            delta_ep=float((post - pre) @ POINTS), participant_count=row['participant_count']))
    actions = pd.DataFrame(action_rows)
    seq_delta = actions.groupby('sequence_id').delta_ep.sum()
    sequences['sequence_delta_ep'] = sequences.sequence_id.map(seq_delta)
    eligible = sequences[sequences.eligible_complete_actor_sequence].copy()
    # Sequence-to-player direct credit sums action changes. Shared credit allocates
    # that identical sequence total equally across distinct participants.
    actions = actions.merge(eligible[['sequence_id', 'sequence_delta_ep']], on='sequence_id',
                            validate='many_to_one')
    participant_sets = actions.groupby('sequence_id').player_id.agg(lambda values: sorted(set(values)))
    participant_counts = participant_sets.map(len).rename('distinct_participants')
    actions = actions.merge(participant_counts, left_on='sequence_id', right_index=True,
                            validate='many_to_one')
    actions['shared_equal_ep'] = actions.sequence_delta_ep / actions.distinct_participants
    direct = actions.groupby('player_id').agg(
        direct_ep=('delta_ep', 'sum'), actions=('delta_ep', 'size'),
        sequences=('sequence_id', 'nunique'), leagues=('league', 'nunique')).reset_index()
    shared = actions.drop_duplicates(['sequence_id', 'player_id']).groupby('player_id').agg(
        shared_equal_ep=('shared_equal_ep', 'sum')).reset_index()
    players_out = direct.merge(shared, on='player_id', validate='one_to_one')
    players_out['direct_rank'] = players_out.direct_ep.rank(ascending=False, method='min').astype(int)
    players_out['shared_rank'] = players_out.shared_equal_ep.rank(ascending=False, method='min').astype(int)
    players_out['rank_change_shared_minus_direct'] = players_out.shared_rank - players_out.direct_rank
    players_out.to_csv(OUT / 'player_credit_comparison.csv', index=False, float_format='%.7f')
    sequences.to_csv(OUT / 'shot_sequence_audit.csv', index=False, float_format='%.7f')
    actions.to_csv(OUT / 'eligible_action_credit.csv', index=False, float_format='%.7f')

    # Credit is conservatively compared at anonymous source-player-ID level;
    # do not imply cross-provider identity or player-season WAR.
    complete_totals = eligible.sequence_delta_ep.sum()
    direct_total = players_out.direct_ep.sum()
    shared_total = players_out.shared_equal_ep.sum()
    rank_rows = []
    for threshold in (1, 5, 10, 25):
        cohort = players_out[players_out.sequences >= threshold]
        rho = spearmanr(cohort.direct_ep, cohort.shared_equal_ep).statistic if len(cohort) >= 3 else np.nan
        rank_rows.append(dict(minimum_sequences=threshold, players=len(cohort),
                              spearman_credit_rho=float(rho) if pd.notna(rho) else None,
                              median_absolute_rank_change=float(cohort.rank_change_shared_minus_direct.abs().median())
                              if len(cohort) else None))
    pd.DataFrame(rank_rows).to_csv(OUT / 'rank_sensitivity.csv', index=False)

    fig, ax = plt.subplots(figsize=(8, 7))
    colors = {'Premier League': '#7653b5', 'La Liga': '#ce7b43', 'Serie A': '#4284b9',
              'Bundesliga': '#c84e61', 'Ligue 1': '#25877d'}
    player_league = actions.groupby('player_id').apply(
        lambda frame: frame.groupby('league').delta_ep.sum().abs().idxmax(), include_groups=False)
    plot = players_out.merge(player_league.rename('dominant_credit_league'), on='player_id')
    for league, group in plot.groupby('dominant_credit_league'):
        ax.scatter(group.direct_ep, group.shared_equal_ep, s=25, alpha=.7,
                   color=colors.get(league, '#777777'), label=league)
    low = min(plot.direct_ep.min(), plot.shared_equal_ep.min())
    high = max(plot.direct_ep.max(), plot.shared_equal_ep.max())
    ax.plot([low, high], [low, high], '--', color='#5e5953', linewidth=1, label='Equal credit')
    ax.set(xlabel='Direct actor credit · summed modelled EP change',
           ylabel='Equal participant split · summed modelled EP change',
           title='Same held-out shot-ending sequences · one-season pilot')
    ax.grid(alpha=.2)
    ax.legend(frameon=False, fontsize=8)
    fig.text(.5, .01, 'Anonymous Wyscout IDs; complete-actor sequences only. Equal split is a benchmark, not Shapley or WAR.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(OUT / 'direct_vs_shared_credit.png', dpi=170)
    plt.close(fig)

    summary = {
        'scope': '2017-18 held-out test matches, March through May 2018, five leagues',
        'credit_methods': ['direct action state-change to recorded actor',
                           'shot-ending sequence summed state change split equally across distinct recorded actors'],
        'not_war': True, 'equal_split_is_not_shapley': True,
        'sequence_boundaries': 'period change, team change, after Shot/Foul/Interruption/Offside, before restart Free Kick subtype',
        'heldout_fixture_count': test_fixture_count,
        'shot_ending_proxy_sequences': int(len(sequences)),
        'complete_actor_sequences': int(len(eligible)),
        'excluded_incomplete_actor_sequences': int((~sequences.eligible_complete_actor_sequence).sum()),
        'complete_actor_coverage_pct': float(100 * eligible.shape[0] / sequences.shape[0]),
        'complete_actor_sequence_events': int(actions.shape[0]),
        'distinct_source_player_ids': int(players_out.player_id.nunique()),
        'distinct_participant_counts': {str(k): int(v) for k, v in
            eligible.actors.value_counts().sort_index().items()},
        'direct_total_ep': float(direct_total), 'shared_total_ep': float(shared_total),
        'sequence_total_ep': float(complete_totals),
        'direct_conservation_error': float(direct_total - complete_totals),
        'shared_conservation_error': float(shared_total - complete_totals),
        'rank_sensitivity': rank_rows,
        'limits': ['single season and one chronological test window',
                   'modelled expected-points differences are not causal effects',
                   'raw-event possession boundaries are proxies, not validated possessions',
                   'attacking shot-ending sequences omit most defensive and goalkeeper contribution',
                   'source IDs are not reconciled to the multi-season player-season dataset',
                   'equal participant split is not a cooperative-game Shapley estimate']
    }
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
