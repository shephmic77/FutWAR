"""Prepare evidence and a correction proposal; never change raw or processed data."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

SOURCE = Path('data/raw/Top5_League_Players_2017to2024_dataset.csv')
OUTPUT = Path('reports')
KEY = ('ITA-Serie A', '1718', 'Milan', 'Emanuele Torrasi')
KEY_COLUMNS = ('league', 'season', 'team', 'player')


def investigate():
    before = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with SOURCE.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, delimiter=';')
        header = reader.fieldnames
        rows = list(reader)
    selected = [(i, r) for i, r in enumerate(rows, start=2)
                if tuple(r[c] for c in KEY_COLUMNS) == KEY]
    if not selected:
        raise ValueError('Expected key is absent; no proposal produced')
    partitions = defaultdict(list)
    disagreements = {}
    proposal = {}
    for column in header:
        states = list(dict.fromkeys(r[column] for _, r in selected))
        if len(states) > 1:
            partitions[tuple(states.index(r[column]) for _, r in selected)].append(column)
        known = list(dict.fromkeys(r[column] for _, r in selected if r[column].strip()))
        if len(known) > 1:
            disagreements[column] = known
            proposal[column] = ''
        else:
            proposal[column] = known[0] if known else ''
    signatures = list(partitions)
    combinations = Counter(tuple(s[i] for s in signatures) for i in range(len(selected)))
    binary = all(len(set(s)) == 2 for s in signatures)
    evidence = {
        'input_sha256': before, 'key': dict(zip(KEY_COLUMNS, KEY)),
        'records': len(selected), 'excess_records_if_collapsed': len(selected) - 1,
        'source_record_numbers_including_header': [i for i, _ in selected],
        'variation_blocks': [{'columns': cols, 'state_counts': dict(Counter(sig))}
                             for sig, cols in partitions.items()],
        'all_binary_blocks': binary, 'unique_state_combinations': len(combinations),
        'complete_binary_cartesian_pattern': binary and len(combinations) == 2 ** len(signatures)
                                            and all(n == 1 for n in combinations.values()),
        'actual_nonblank_disagreements': disagreements,
        'proposal_policy': 'Collapse this key to one row; retain unique nonblank values; blank actual conflicts; leave all other missing cells missing.',
        'external_value_validation': 'not_performed', 'decision': 'pending_user',
        'proposed_total_records': len(rows) - len(selected) + 1,
        'raw_data_modified': False,
    }
    OUTPUT.mkdir(exist_ok=True)
    (OUTPUT/'torrasi_investigation.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    with (OUTPUT/'torrasi_proposed_record.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=header, delimiter=';')
        writer.writeheader()
        writer.writerow(proposal)
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == before
    print(json.dumps({k: evidence[k] for k in ['records','unique_state_combinations',
          'complete_binary_cartesian_pattern','actual_nonblank_disagreements',
          'proposed_total_records','decision','raw_data_modified']}, indent=2))


if __name__ == '__main__':
    investigate()
