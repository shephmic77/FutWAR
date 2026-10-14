import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_position_boundaries import clock_seconds, inspect_boundaries


class PositionBoundaryTests(unittest.TestCase):
    def sample(self):
        event = {'id': 'entry', 'type': {'name': 'Substitution'}, 'team': {'id': 1},
                 'period': 2, 'minute': 46, 'second': 10,
                 'substitution': {'replacement': {'id': 20}}}
        spell = {'position_id': 6, 'position': 'Left Back', 'from': '46:10',
                 'from_period': 2, 'to': None, 'to_period': None,
                 'start_reason': 'Substitution - On (Tactical)', 'end_reason': 'Final Whistle'}
        lineups = [{'team_id': 1, 'lineup': [{'player_id': 20, 'player_name': 'Test', 'positions': [spell]}]}]
        return event, spell, lineups

    def test_matching_clock_in_wrong_period_is_unresolved(self):
        event, spell, lineups = self.sample()
        spell['from_period'] = 1
        self.assertEqual(inspect_boundaries([event], lineups, 1)[0]['status'], 'unresolved_event_boundary')

    def test_nearby_time_does_not_silently_correct_boundary(self):
        event, spell, lineups = self.sample()
        event['second'] = 11
        row = inspect_boundaries([event], lineups, 1)[0]
        self.assertEqual(row['status'], 'unresolved_event_boundary')
        self.assertEqual(row['nearest_same_period_delta_seconds'], 1)
        self.assertEqual(spell['from'], '46:10')

    def test_final_whistle_stays_null_with_last_period_context(self):
        event, spell, lineups = self.sample()
        ends = [{'id': str(period), 'type': {'name': 'Half End'}, 'team': {'id': 1},
                 'period': period, 'minute': minute, 'second': 0} for period, minute in [(1, 48), (2, 95)]]
        row = inspect_boundaries([event] + ends, lineups, 1)[1]
        self.assertEqual(row['status'], 'open_final_whistle_with_event_context')
        self.assertEqual(row['matching_event_ids'], '["2"]')
        self.assertIsNone(spell['to'])

    def test_stoppage_minutes_and_invalid_seconds(self):
        self.assertEqual(clock_seconds('95:30'), 5730)
        with self.assertRaises(ValueError):
            clock_seconds('45:60')
