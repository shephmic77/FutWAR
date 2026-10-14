"""Compare transcribed primary references and inspect player identity evidence."""
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from export_initial_eda import psql

METRICS = ('played', 'wins', 'draws', 'losses', 'goals_for', 'goals_against', 'earned_match_points')


def compare_references(baseline, references):
    """Missing reference metrics remain unchecked; ambiguous evidence stays provisional."""
    lookup = {(r['league'], r['season'], r['team']): r for r in baseline}
    if len(lookup) != len(baseline):
        raise ValueError('Duplicate baseline club-season')
    seen, results = set(), []
    for ref in references:
        key = (ref['league'], ref['season'], ref['team'])
        if key in seen or key not in lookup:
            raise ValueError(f'Duplicate or unmatched reference: {key}')
        seen.add(key)
        if not ref['source_url'].startswith('https://') or not ref['metrics']:
            raise ValueError('Reference needs source evidence and metrics')
        for metric, value in ref['metrics'].items():
            if metric not in METRICS or type(value) is not int or value < 0:
                raise ValueError(f'Invalid reference metric: {metric}')
            actual = int(lookup[key][metric])
            results.append(dict(league=key[0], season=key[1], team=key[2], metric=metric,
                                calculated=actual, reference=value, difference=actual-value,
                                evidence_status=ref['evidence_status'], source_url=ref['source_url']))
    coverage = []
    refs = {(r['league'], r['season'], r['team']): r for r in references}
    for key in sorted(lookup):
        ref = refs.get(key)
        checked = list(ref['metrics']) if ref else []
        coverage.append(dict(league=key[0], season=key[1], team=key[2],
                             evidence_status=ref['evidence_status'] if ref else 'unreviewed',
                             checked_metrics='|'.join(checked),
                             unchecked_metrics='|'.join(m for m in METRICS if m not in checked)))
    return results, coverage


def identity_profile(rows):
    """Name and birth-year groups are candidates, never assigned player IDs."""
    groups = defaultdict(list)
    for number, row in enumerate(rows, start=1):
        groups[row['player'], row['born_']].append((number, row))
    candidates = []
    for (name, born), group in sorted(groups.items()):
        seasons = defaultdict(list)
        for number, row in group:
            seasons[row['season']].append((number, row))
        for season, records in sorted(seasons.items()):
            clubs = sorted({(r['league'], r['team']) for _, r in records})
            if len(clubs) > 1:
                candidates.append(dict(player_label=name, birth_year_label=born, season=season,
                    output_records='|'.join(str(n) for n, _ in records),
                    club_contexts=json.dumps(clubs, ensure_ascii=False),
                    status='possible_transfer_or_name_collision_unverified'))
    births_by_name = defaultdict(set)
    for row in rows:
        if row['born_']:
            births_by_name[row['player']].add(row['born_'])
    summary = dict(records=len(rows), name_birth_year_groups=len(groups),
                   missing_birth_year_records=sum(not r['born_'] for r in rows),
                   missing_nationality_records=sum(not r['nation_'] for r in rows),
                   name_labels_with_multiple_known_birth_years=sum(len(v)>1 for v in births_by_name.values()),
                   multiple_club_same_season_candidate_groups=len(candidates),
                   normalized_player_ids_created=0,
                   limitation='Names, birth year and nationality are identity evidence, not stable IDs. '
                   'Multiple-club groups may be transfers or collisions; no dates, fees or moves are inferred.')
    return summary, candidates


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    path = Path('data/raw/standings_references/2024-25_primary_transcription.json')
    content = path.read_bytes()
    evidence = json.loads(content.decode('utf-8'))
    source_sha = hashlib.sha256(content).hexdigest()
    baseline = list(csv.DictReader(io.StringIO(psql('--csv', '-c',
        'SELECT * FROM futwar.team_results_baseline ORDER BY league,season,team;'))))
    comparisons, coverage = compare_references(baseline, evidence['records'])
    matches = list(csv.DictReader(io.StringIO(psql('--csv', '-c',
        'SELECT * FROM futwar.normalized_match_results;'))))
    for event in evidence['administrative_events']:
        found = [m for m in matches if all(m[k] == event[k] for k in
                 ('league','season','match_date','home_team','away_team'))]
        if len(found) != 1 or (int(found[0]['home_goals']), int(found[0]['away_goals'])) != (
                event['awarded_home_goals'], event['awarded_away_goals']):
            raise ValueError('Administrative fixture missing or source score no longer matches award')
    player_path = Path('data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv')
    with player_path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter=';')
        headers = reader.fieldnames
        players = list(reader)
    identity, candidates = identity_profile(players)
    identity['available_identity_columns'] = [h for h in headers if h in
        ('player','born_','age_','nation_','league','season','team')]
    identity['provider_id_or_url_columns'] = [h for h in headers if h.lower() in
        ('player_id','player_url','playerid','url','href')]
    report = Path('reports/standings_identity')
    write_csv(report/'standings_comparisons.csv', comparisons)
    write_csv(report/'standings_coverage.csv', coverage)
    write_csv(report/'possible_transfers.csv', candidates,
              ['player_label','birth_year_label','season','output_records','club_contexts','status'])
    exports = Path('data/processed/postgres')
    reference_rows = [dict(source_sha256=source_sha, league=r['league'], season=r['season'],
        team=r['team'],source_team_label=r['source_team_label'],metrics=json.dumps(r['metrics']),
        source_url=r['source_url'],reviewed_at=r['reviewed_at'],
        evidence_status=r['evidence_status'],evidence_method=r['evidence_method']) for r in evidence['records']]
    write_csv(exports/'standings_references.csv',reference_rows)
    write_csv(exports/'administrative_results.csv', [dict(source_sha256=source_sha, **r)
              for r in evidence['administrative_events']])
    summary = dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),
        reference_file=str(path), reference_sha256=source_sha,
        processed_player_sha256=hashlib.sha256(player_path.read_bytes()).hexdigest(),
        reference_club_seasons=len(evidence['records']), compared_metric_cells=len(comparisons),
        mismatched_metric_cells=sum(r['difference'] != 0 for r in comparisons),
        provisional_reference_club_seasons=sum(r['evidence_status'].startswith('provisional')
            for r in evidence['records']), total_club_seasons=len(coverage),
        unreviewed_club_seasons=sum(r['evidence_status']=='unreviewed' for r in coverage),
        administrative_events=len(evidence['administrative_events']), player_identity=identity,
        terms=evidence['terms'], research_decisions_changed=False)
    (report/'run.json').write_text(json.dumps(summary, indent=2,ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
