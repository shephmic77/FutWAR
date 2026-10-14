import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from apply_keeper_minute_corrections import apply_records


class KeeperCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(keeper_record_id='reviewed', player_name='Keeper', team_name='Club',
                        league='League', season='2018-19', keeper_minutes='',
                        quality_flags='["missing_or_nonpositive_keeper_minutes", "missing_psxg"]',
                        psxg='', basic_source_values='{"minutes":null}')
        self.correction = {**{k: self.row[k] for k in ['keeper_record_id', 'player_name', 'team_name', 'league', 'season']},
                           'field': 'keeper_minutes', 'original_value': '', 'approved_value': '1'}

    def test_fill_retains_original_and_other_issue(self):
        result = apply_records([self.row], [self.correction])[0]
        self.assertEqual(result['keeper_minutes'], '1')
        self.assertEqual(result['keeper_minutes_original'], '')
        self.assertEqual(self.row['keeper_minutes'], '')
        self.assertEqual(result['quality_flags'], self.row['quality_flags'])
        self.assertEqual(result['unresolved_quality_flags'], '["missing_psxg"]')
        self.assertEqual(result['basic_source_values'], self.row['basic_source_values'])

    def test_unexpected_values_context_and_targets_fail(self):
        for row in [{**self.row, 'keeper_minutes': '90'}, {**self.row, 'team_name': 'Other'}]:
            with self.assertRaises(ValueError):
                apply_records([row], [self.correction])
        with self.assertRaises(ValueError):
            apply_records([self.row], [self.correction, self.correction])
        with self.assertRaises(ValueError):
            apply_records([], [self.correction])

    def test_two_fields_on_same_record_preserve_separate_originals(self):
        row = {**self.row, 'keeper_minutes': '714.0', 'appearances': '9.0',
               'quality_flags': '["keeper_minutes_vs_advanced_90s_disagree"]'}
        minutes = {**self.correction, 'original_value': '714.0', 'approved_value': '738',
                   'resolved_flags': ['keeper_minutes_vs_advanced_90s_disagree'],
                   'warnings': ['advanced_metric_scope_not_confirmed']}
        appearances = {**self.correction, 'field': 'appearances',
                       'original_value': '9.0', 'approved_value': '10'}
        result = apply_records([row], [minutes, appearances])[0]
        self.assertEqual((result['keeper_minutes'], result['appearances']), ('738', '10'))
        self.assertEqual((result['keeper_minutes_original'], result['appearances_original']), ('714.0', '9.0'))
        self.assertEqual(result['unresolved_quality_flags'], '[]')
        self.assertIn('advanced_metric_scope_not_confirmed', result['exposure_correction_warnings'])
        self.assertEqual(row['appearances'], '9.0')

    def test_other_measurements_cannot_be_corrected(self):
        with self.assertRaises(ValueError):
            apply_records([self.row], [{**self.correction, 'field': 'psxg'}])


if __name__ == '__main__':
    unittest.main()
