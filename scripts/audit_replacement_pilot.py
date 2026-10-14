"""Attach local playing records to factual candidate evidence, without estimating WAR."""
import csv
import argparse
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path


def load_evidence(path):
    payload = path.read_bytes()
    evidence = json.loads(payload)
    hashes = {path.name: hashlib.sha256(payload).hexdigest()}
    if 'parent_filename' in evidence:
        parent_path = path.parent / evidence['parent_filename']
        if parent_path.resolve().parent != path.parent.resolve():
            raise ValueError('Parent evidence must stay in the review folder')
        parent_bytes = parent_path.read_bytes()
        if hashlib.sha256(parent_bytes).hexdigest() != evidence['parent_sha256']:
            raise ValueError('Original evidence ledger changed')
        parent = json.loads(parent_bytes)
        if parent['snapshot_sha256'] != evidence['snapshot_sha256']:
            raise ValueError('Evidence versions reference different snapshots')
        evidence['candidates'] = parent['candidates'] + evidence['candidates']
        hashes[parent_path.name] = evidence['parent_sha256']
    return evidence, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expanded', action='store_true', help='Audit expanded evidence; preserve original pilot outputs')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    evidence_path = root / 'data/raw/replacement_reviews' / (
        'expanded_2026-10-10.json' if args.expanded else 'pilot_2026-10-10.json')
    evidence, evidence_hashes = load_evidence(evidence_path)
    snapshot_path = root / 'data/processed/exploration/player_team_seasons.csv'
    snapshot_bytes = snapshot_path.read_bytes()
    if hashlib.sha256(snapshot_bytes).hexdigest() != evidence['snapshot_sha256']:
        raise ValueError('Reviewed snapshot changed; review links before rerunning')
    with snapshot_path.open(encoding='utf-8', newline='') as handle:
        records = list(csv.DictReader(handle))
    output = []
    linked_keys = set()
    for candidate in evidence['candidates']:
        matches = [r for r in records if all(r[k] == candidate[k] for k in
                   ['player_name', 'team_name', 'league', 'season', 'output_record'])]
        if len(matches) != 1:
            raise ValueError(f"Candidate requires one reviewed local record: {candidate['player_name']}")
        if not candidate['source_urls']:
            raise ValueError('Candidate lacks official evidence URLs')
        record = matches[0]
        key = (record['source_sha256'], record['output_record'])
        if key in linked_keys:
            raise ValueError('Duplicate candidate record')
        linked_keys.add(key)
        row = {k: record[k] for k in ['source_sha256', 'output_record', 'player_name',
               'team_name', 'league', 'season', 'nominal_position', 'minutes', 'appearances', 'starts']}
        row.update({k: candidate[k] for k in ['acquisition_status', 'availability_status',
                    'injury_review_status', 'interpretation']})
        row.update(total_cost_status='unknown', replacement_level_status='not_established',
                   provider_identity_status='not_assigned_by_this_review',
                   sources=' | '.join(candidate['source_urls']),
                   below_notebook_900_minute_display=int(record['minutes']) < 900)
        if args.expanded:
            row.update(historical_position=candidate.get('historical_position', 'unknown'),
                       position_evidence_status=candidate.get('position_evidence_status', 'insufficient_historical_specific_position_evidence'),
                       match_position_coverage=candidate.get('match_position_coverage', 'not_audited'),
                       acquisition_evidence=candidate['acquisition_evidence'])
        output.append(row)
    folder = root / 'reports' / ('replacement_expanded' if args.expanded else 'replacement_pilot')
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'candidates.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    summary = dict(executed_at_utc=datetime.now(timezone.utc).isoformat(),
                   evidence_sha256=evidence_hashes[evidence_path.name],
                   snapshot_sha256=evidence['snapshot_sha256'],
                   candidates=len(output), leagues=sorted({r['league'] for r in output}),
                   selection=evidence['selection'], confirmed_replacement_players=0,
                   baseline_estimated=False, player_statistics_changed=False)
    if args.expanded:
        leagues = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']
        seasons = [f'{year}-{str(year + 1)[-2:]}' for year in range(2017, 2025)]
        positions = sorted({r['nominal_position'] for r in records})
        coverage = []
        for league, season, position in itertools.product(leagues, seasons, positions):
            source_group = [r for r in records if (r['league'], r['season'], r['nominal_position']) == (league, season, position)]
            candidate_group = [r for r in output if (r['league'], r['season'], r['nominal_position']) == (league, season, position)]
            coverage.append(dict(league=league, season=season, original_nominal_position=position,
                                 source_records=len(source_group), candidate_records=len(candidate_group),
                                 specific_position_known_candidates=sum(r['historical_position'] != 'unknown' for r in candidate_group),
                                 replacement_pool_verified=False))
        with (folder / 'coverage.csv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(coverage[0]))
            writer.writeheader()
            writer.writerows(coverage)
        summary.update(evidence_hashes=evidence_hashes, coverage_rows=len(coverage),
                       observed_candidate_league_seasons=len({(r['league'], r['season']) for r in output}),
                       historical_specific_position_unknown=sum(r['historical_position'] == 'unknown' for r in output),
                       position_frequency_rule_applied=False, goalkeeper_candidates=sum(r['nominal_position'] == 'GK' for r in output))
    (folder / 'run.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
