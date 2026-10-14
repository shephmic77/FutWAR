"""Audit research-release scope and schema; do not infer positions or keeper value."""
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'data/raw/wyscout_research/2026-10-10'
OUTPUT = ROOT / 'reports/wyscout_research'
LEAGUES = {'England': (364, 'Premier League'), 'Spain': (795, 'La Liga'),
           'Italy': (524, 'Serie A'), 'Germany': (426, 'Bundesliga'),
           'France': (412, 'Ligue 1')}


def verify(manifest):
    fingerprints = {}
    for entry in manifest['files']:
        payload = (ROOT / entry['path']).read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        if actual != entry['sha256'] or len(payload) != entry['bytes']:
            raise ValueError('Source file changed: ' + entry['path'])
        fingerprints[entry['path']] = actual
    for article in manifest['articles']:
        actual = hashlib.sha256((ROOT / article['metadata_path']).read_bytes()).hexdigest()
        if actual != article['metadata_sha256']:
            raise ValueError('Source metadata changed')
        fingerprints[article['metadata_path']] = actual
    return fingerprints


def archive_rows(archive, member):
    # Read known JSON members in place; never extract arbitrary ZIP paths.
    info = archive.getinfo(member)
    if info.file_size > 300_000_000:
        raise ValueError('Uncompressed member exceeds size guard')
    with archive.open(member) as handle:
        return json.load(handle)


def main():
    manifest = json.loads((ROOT / 'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    fingerprints = verify(manifest)
    players = json.loads((FOLDER / 'players.json').read_text(encoding='utf-8'))
    profiles = {p['wyId']: p for p in players}
    if len(profiles) != len(players):
        raise ValueError('Duplicate profile IDs')
    roles = Counter(json.dumps(p.get('role'), sort_keys=True) for p in players)
    results = []
    details = {}
    keeper_review = []
    with zipfile.ZipFile(FOLDER / 'matches.zip') as matches_zip, zipfile.ZipFile(FOLDER / 'events.zip') as events_zip:
        for country, (competition_id, league) in LEAGUES.items():
            matches = archive_rows(matches_zip, f'matches_{country}.json')
            match_ids = {m['wyId'] for m in matches}
            if len(match_ids) != len(matches) or any(m['competitionId'] != competition_id for m in matches):
                raise ValueError('Duplicate match IDs or unexpected competition')
            dates = [m['dateutc'][:10] for m in matches]
            if not all('2017-07-01' <= d <= '2018-06-30' for d in dates):
                raise ValueError('Match outside declared season')
            lineup_fields = Counter()
            lineup_rows = bench_rows = substitution_rows = missing_formations = 0
            starter_sizes = Counter()
            for match in matches:
                for team in match['teamsData'].values():
                    formation = team.get('formation')
                    if not isinstance(formation, dict):
                        missing_formations += 1
                        continue
                    starters = formation.get('lineup', [])
                    starter_sizes[len(starters)] += 1
                    lineup_rows += len(starters)
                    bench_rows += len(formation.get('bench', []))
                    substitutions = formation.get('substitutions')
                    if isinstance(substitutions, list):
                        substitution_rows += len(substitutions)
                    for row in starters + formation.get('bench', []):
                        lineup_fields.update(row.keys())
            events = archive_rows(events_zip, f'events_{country}.json')
            event_ids = set()
            event_matches = set()
            event_fields = Counter()
            names = Counter()
            keeper_names = Counter()
            keeper_tags = Counter()
            unknown_players = zero_players = duplicate_events = outside_matches = empty_positions = 0
            goalkeeper_action_records = goalkeeper_actions_non_gk_profile = 0
            for event in events:
                duplicate_events += event['id'] in event_ids
                event_ids.add(event['id'])
                event_matches.add(event['matchId'])
                outside_matches += event['matchId'] not in match_ids
                event_fields.update(event.keys())
                names[event['eventName']] += 1
                empty_positions += not event.get('positions')
                player_id = event['playerId']
                zero_players += player_id == 0
                unknown_players += player_id != 0 and player_id not in profiles
                profile = profiles.get(player_id, {})
                is_profile_gk = profile.get('role', {}).get('code2') == 'GK'
                if is_profile_gk:
                    keeper_names[event['eventName'] + ' / ' + event['subEventName']] += 1
                if event['eventId'] in (4, 9):
                    goalkeeper_action_records += 1
                    goalkeeper_actions_non_gk_profile += not is_profile_gk
                    keeper_tags.update(str(tag['id']) for tag in event.get('tags', []))
                    if not is_profile_gk:
                        keeper_review.append(dict(league=league, match_id=event['matchId'],
                            event_id=event['id'], player_id=player_id,
                            player_name=profile.get('shortName'), profile_role=profile.get('role'),
                            event_name=event['eventName'], subevent_name=event['subEventName'],
                            match_period=event['matchPeriod'], event_seconds=event['eventSec'],
                            status='unreviewed_role_or_event_conflict'))
            if duplicate_events or outside_matches:
                raise ValueError('Duplicate event IDs or unknown match links')
            advanced_fields = [k for k in event_fields if any(s in k.lower() for s in ('xg', 'expected', 'psxg'))]
            summary = dict(matches=len(matches), events=len(events), events_matches=len(event_matches),
                matches_without_events=len(match_ids - event_matches), teams=len({t for m in matches for t in m['teamsData']}),
                season_ids=sorted({m['seasonId'] for m in matches}), first_match=min(dates), last_match=max(dates),
                match_statuses=dict(Counter(m['status'] for m in matches)),
                lineup_records=lineup_rows, bench_records=bench_rows, substitution_records=substitution_rows,
                team_records_without_formation=missing_formations, starter_list_sizes=dict(starter_sizes),
                lineup_row_fields=dict(lineup_fields), event_fields=dict(event_fields),
                event_names=dict(names), profile_gk_event_names=dict(keeper_names),
                goalkeeper_action_records=goalkeeper_action_records,
                goalkeeper_actions_without_gk_profile=goalkeeper_actions_non_gk_profile,
                goalkeeper_action_tag_counts=dict(keeper_tags),
                duplicate_event_ids=duplicate_events, event_match_links_outside_archive=outside_matches,
                event_records_unknown_nonzero_player=unknown_players, event_records_player_zero=zero_players,
                event_records_empty_coordinates=empty_positions, identified_expected_goal_fields=advanced_fields)
            details[league] = summary
            results.append(dict(league=league, season='2017-18', match_records=len(matches),
                event_records=len(events), matches_without_events=summary['matches_without_events'],
                played_position_coverage='not_established', post_shot_xg_field='not_identified',
                keeper_outcome_validity='not_validated', status='structural_audit_only'))
            print(league + ': audited', flush=True)
            del events
    for year in range(2018, 2025):
        for _, league in LEAGUES.values():
            results.append(dict(league=league, season=f'{year}-{str(year + 1)[2:]}',
                match_records=0, event_records=0, matches_without_events='',
                played_position_coverage='absent_from_release', post_shot_xg_field='absent_from_release',
                keeper_outcome_validity='absent_from_release', status='absent_from_release'))
    if len(results) != 40:
        raise ValueError('Coverage accounting failed')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / 'coverage.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(sorted(results, key=lambda r: (r['season'], r['league'])))
    (OUTPUT / 'summary.json').write_text(json.dumps(dict(source_fingerprints=fingerprints,
        player_profiles=len(players), profile_role_vocabulary=dict(roles), leagues=details,
        position_rule_applied=False, statistics_merged=False), indent=2), encoding='utf-8')
    (OUTPUT / 'keeper_role_review.json').write_text(json.dumps(keeper_review, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
