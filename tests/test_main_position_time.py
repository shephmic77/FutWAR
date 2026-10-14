import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from position_labels import main_position_by_time


class MainPositionTimeTests(unittest.TestCase):
    def test_total_time_selects_one_role(self):
        result = main_position_by_time({'LB': 5400, 'LWB': 9000}, complete_coverage=True)
        self.assertEqual(result['main_position'], 'LWB')
        self.assertTrue(result['finalized'])

    def test_missing_coverage_unresolved_and_ties_withhold(self):
        for complete, unresolved in [(False, 0), (True, 1)]:
            self.assertIsNone(main_position_by_time({'LB': 5400}, complete_coverage=complete,
                                                   unresolved_spells=unresolved)['main_position'])
        self.assertFalse(main_position_by_time({'LB': 50, 'RB': 50}, complete_coverage=True)['finalized'])
        self.assertFalse(main_position_by_time({'GK': 0}, complete_coverage=True)['finalized'])

    def test_invalid_evidence_rejected(self):
        for totals in [{'DF': 50}, {'LB': -1}, {'LB': float('nan')}]:
            with self.assertRaises(ValueError):
                main_position_by_time(totals, complete_coverage=True)
