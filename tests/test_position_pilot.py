import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_position_pilot import inspect_match


class PositionPilotTests(unittest.TestCase):
    def sample(self):
        events = [{'id': 'start', 'type': {'name': 'Starting XI'}, 'team': {'id': 1},
            'period': 1, 'minute': 0, 'second': 0, 'tactics': {'formation': 433,
            'lineup': [{'player': {'id': 10}, 'position': {'id': 6, 'name': 'Left Back'}}]}}]
        positions = [{'position_id': 6, 'position': 'Left Back'},
                     {'position_id': 8, 'position': 'Left Wing Back'}]
        lineups = [{'team_id': 1, 'lineup': [
            {'player_id': 10, 'player_name': 'Starter', 'positions': positions},
            {'player_id': 20, 'player_name': 'Unused bench', 'positions': []}]}]
        return events, lineups

    def test_spells_do_not_multiply_appearances_or_count_unused_bench(self):
        events, lineups = self.sample()
        summary, spells, players, _, flags = inspect_match(events, lineups, 1)
        self.assertEqual(summary['appearance_players'], 1)
        self.assertEqual(summary['unused_listed_players'], 1)
        self.assertEqual(summary['multi_position_appearances'], 1)
        self.assertEqual([s['position_id'] for s in spells], [6, 8])
        self.assertFalse(players[1]['appearance_evidenced'])
        self.assertEqual(flags, [])

    def test_missing_substitute_role_remains_flagged(self):
        events, lineups = self.sample()
        events.append({'id': 'sub', 'type': {'name': 'Substitution'}, 'team': {'id': 1},
                       'substitution': {'replacement': {'id': 20}}})
        summary, _, _, _, flags = inspect_match(events, lineups, 1)
        self.assertEqual(summary['appearance_players'], 2)
        self.assertEqual(summary['unused_listed_players'], 0)
        self.assertEqual(flags[0]['flag'], 'appearance_without_position_spells')

    def test_duplicate_events_rejected(self):
        events, lineups = self.sample()
        with self.assertRaises(ValueError):
            inspect_match(events + events, lineups, 1)
