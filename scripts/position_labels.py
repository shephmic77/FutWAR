"""User-approved position frequency rule; requires historical match-position evidence."""
from collections import Counter
from math import isfinite


def main_position_by_time(position_seconds, *, complete_coverage, unresolved_spells=0):
    """Select from audited seasonal totals; caller verifies identity and scope.

    Coverage includes every domestic appearance, not just the downloaded sample.
    This function does not select a secondary-role or minimum-time rule.
    """
    if not isinstance(complete_coverage, bool):
        raise ValueError('Coverage must be explicitly True or False')
    if not isinstance(unresolved_spells, int) or unresolved_spells < 0:
        raise ValueError('Unresolved spell count must be nonnegative')
    for position, seconds in position_seconds.items():
        if not isinstance(position, str) or not position.strip() or position.strip() in {'DF', 'MF', 'FW'} or ',' in position:
            raise ValueError('A specific position is required')
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not isfinite(seconds) or seconds < 0:
            raise ValueError('Position seconds must be finite and nonnegative')
    result = {'main_position': None, 'method': 'most_total_position_seconds',
              'finalized': False, 'position_seconds': dict(position_seconds)}
    if not complete_coverage or unresolved_spells:
        result['status'] = 'incomplete_or_unresolved_evidence'
    elif not position_seconds or max(position_seconds.values()) == 0:
        result['status'] = 'no_positive_position_time'
    else:
        maximum = max(position_seconds.values())
        leaders = sorted(p for p, seconds in position_seconds.items() if seconds == maximum)
        if len(leaders) > 1:
            result.update(status='tied_main_position; review_required', tied_main_positions=leaders)
        else:
            result.update(main_position=leaders[0], finalized=True, status='complete_position_time')
    return result


def summarize_positions(appearances, total_appearances):
    """Summarize one player's season from one evidenced position per appearance.

    Inputs are match_id/position mappings, with None for unknown positions.
    The caller must verify identity, season/competition scope and position evidence.
    Missing appearance rows also count as unknown. No broad-label conversion occurs.
    Legacy frequency-based main candidates are not final seasonal assignments;
    standard analysis must use main_position_by_time after time/coverage validation.
    """
    if not isinstance(total_appearances, int) or total_appearances < 0:
        raise ValueError('Total appearances must be a nonnegative integer')
    rows = list(appearances)
    ids = [row['match_id'] for row in rows]
    if any(not match_id for match_id in ids) or len(set(ids)) != len(ids):
        raise ValueError('Each appearance requires a unique match identifier')
    if len(rows) > total_appearances:
        raise ValueError('Evidence exceeds total appearances')
    counts = Counter()
    for row in rows:
        position = row['position']
        if position is not None:
            if not isinstance(position, str) or not position.strip():
                raise ValueError('Use None for unknown positions')
            if position.strip() in {'DF', 'MF', 'FW'} or ',' in position:
                raise ValueError('Broad or combined source labels are not specific match positions')
            counts[position.strip()] += 1
    unknown = total_appearances - sum(counts.values())
    qualifying = sorted(p for p, n in counts.items()
                        if n >= 5 and 10 * n >= total_appearances)
    result = dict(total_appearances=total_appearances, position_counts=dict(sorted(counts.items())),
                  main_position_method='legacy_appearance_frequency_candidate', main_position_finalized=False,
                  unknown_position_appearances=unknown, main_position=None,
                  secondary_positions=[], qualifying_observed_positions=qualifying,
                  secondary_min_appearances=5, secondary_min_share=0.10)
    if not total_appearances:
        result['status'] = 'no_appearances'
    elif unknown:
        result['status'] = 'incomplete_position_coverage; labels_not_finalized'
    else:
        maximum = max(counts.values())
        leaders = sorted(p for p, n in counts.items() if n == maximum)
        if len(leaders) != 1:
            result.update(status='tied_main_position; review_required', tied_main_positions=leaders)
        else:
            result.update(status='complete_match_position_counts', main_position=leaders[0],
                          secondary_positions=[p for p in qualifying if p != leaders[0]])
    return result
