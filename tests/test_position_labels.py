import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from position_labels import summarize_positions


def evidence(counts):
    rows = []
    for position, count in counts.items():
        for _ in range(count):
            rows.append(dict(match_id=str(len(rows) + 1), position=position))
    return rows


class PositionLabelTests(unittest.TestCase):
    def test_both_inclusive_boundaries(self):
        result = summarize_positions(evidence({'LB': 45, 'LWB': 5}), 50)
        self.assertEqual(result['main_position'], 'LB')
        self.assertEqual(result['secondary_positions'], ['LWB'])

    def test_five_games_but_less_than_ten_percent(self):
        result = summarize_positions(evidence({'LB': 46, 'LWB': 5}), 51)
        self.assertEqual(result['secondary_positions'], [])

    def test_less_than_five_even_with_high_share(self):
        result = summarize_positions(evidence({'LB': 16, 'CB': 4}), 20)
        self.assertEqual(result['secondary_positions'], [])

    def test_missing_positions_do_not_inflate_denominator_share(self):
        result = summarize_positions(evidence({'LB': 10, 'LWB': 5}), 60)
        self.assertEqual(result['unknown_position_appearances'], 45)
        self.assertEqual(result['qualifying_observed_positions'], ['LB'])
        self.assertIsNone(result['main_position'])
        self.assertEqual(result['secondary_positions'], [])

    def test_duplicate_match_and_broad_label_rejected(self):
        with self.assertRaises(ValueError):
            summarize_positions([{'match_id': '1', 'position': 'LB'}] * 2, 2)
        with self.assertRaises(ValueError):
            summarize_positions([{'match_id': '1', 'position': 'DF'}], 1)

    def test_ties_and_zero_appearances(self):
        result = summarize_positions(evidence({'LB': 5, 'LWB': 5}), 10)
        self.assertIsNone(result['main_position'])
        self.assertEqual(result['tied_main_positions'], ['LB', 'LWB'])
        self.assertEqual(summarize_positions([], 0)['status'], 'no_appearances')


if __name__ == '__main__':
    unittest.main()
