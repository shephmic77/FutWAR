import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_position_minutes import appearance_intervals, elapsed, interval_totals, period_clock


class PositionMinuteTests(unittest.TestCase):
    def test_cross_half_time_includes_first_half_stoppage(self):
        ends = {1: 2880, 2: 2940}
        self.assertEqual(elapsed(2, 60 * 60, ends) - elapsed(1, 30 * 60, ends), 1980)
        self.assertEqual(elapsed(2, 45 * 60, ends), 2880)

    def test_temporary_absence_is_excluded(self):
        events = [{'index': 1, 'type': {'name': 'Starting XI'}, 'team': {'id': 1},
            'period': 1, 'minute': 0, 'second': 0,
            'tactics': {'lineup': [{'player': {'id': 2}}]}}]
        for index, kind, minute in [(2, 'Player Off', 20), (3, 'Player On', 22)]:
            events.append({'index': index, 'type': {'name': kind}, 'team': {'id': 1},
                           'player': {'id': 2}, 'period': 1, 'minute': minute, 'second': 0})
        intervals, flags = appearance_intervals(events, {1: 2880, 2: 2940})
        self.assertEqual(interval_totals(intervals[(1, 2)]), (5700, 0))
        self.assertEqual(flags, [])

    def test_nested_overlap_and_reversal(self):
        self.assertEqual(interval_totals([(0, 100), (20, 30), (40, 50)]), (120, 20))
        with self.assertRaises(ValueError):
            interval_totals([(5, 4)])

    def test_conflicting_period_ends_are_rejected(self):
        events = [{'period': period, 'minute': minute, 'second': second,
                   'type': {'name': 'Half End'}}
                  for period, minute, second in [(1, 48, 0), (1, 48, 1), (2, 94, 0)]]
        with self.assertRaises(ValueError):
            period_clock(events)
