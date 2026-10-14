import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_keeper_psxg_corrections import apply_records


class KeeperPSxGCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(keeper_record_id='reviewed', player_name='Keeper', team_name='Club',
            league='League', season='2022-23', psxg='', goals_against='0.0',
            unresolved_quality_flags='["missing_psxg", "another_issue"]',
            quality_flags='["missing_psxg", "another_issue"]', advanced_source_values='{"PSxG":null}',
            metric_version_status='not_confirmed')
        self.correction = {**{k: self.row[k] for k in ['keeper_record_id', 'player_name', 'team_name', 'league', 'season']},
            'field': 'psxg', 'original_value': '', 'approved_value': '0.0',
            'warnings': ['psxg_model_version_unconfirmed']}

    def test_observed_zero_retains_unknown_version_and_other_flags(self):
        result = apply_records([self.row], [self.correction])[0]
        self.assertEqual(result['psxg'], '0.0')
        self.assertEqual(result['psxg_original'], '')
        self.assertEqual(result['unresolved_quality_flags'], '["another_issue"]')
        for field in ['goals_against', 'quality_flags', 'advanced_source_values', 'metric_version_status']:
            self.assertEqual(result[field], self.row[field])
        self.assertIn('psxg_model_version_unconfirmed', result['psxg_correction_warnings'])
        self.assertEqual(self.row['psxg'], '')

    def test_populated_values_invalid_targets_and_values_fail(self):
        with self.assertRaises(ValueError):
            apply_records([{**self.row, 'psxg': '5.0'}], [self.correction])
        with self.assertRaises(ValueError):
            apply_records([{**self.row, 'team_name': 'Other'}], [self.correction])
        with self.assertRaises(ValueError):
            apply_records([self.row], [self.correction, self.correction])
        with self.assertRaises(ValueError):
            apply_records([], [self.correction])
        for value in ['-1.0', 'nan', 'inf']:
            with self.assertRaises(ValueError):
                apply_records([self.row], [{**self.correction, 'approved_value': value}])


if __name__ == '__main__':
    unittest.main()
