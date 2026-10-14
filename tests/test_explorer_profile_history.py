"""Check sourced supplemental context without inventing missing seasons."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProfileHistoryChecks(unittest.TestCase):
    def test_source_cutoffs_and_abdi_history(self):
        file = ROOT / 'reports/explorer/profile_history.json'
        if not file.exists():
            self.skipTest('Private derived history not built')
        data = json.loads(file.read_text(encoding='utf-8'))
        abdi = data['profiles']['211474']['annual_values']
        self.assertEqual([x['year'] for x in abdi], list(range(2018, 2026)))
        self.assertEqual(abdi[-1]['eur'], 3000000)
        for profile in data['profiles'].values():
            for value in profile['annual_values']:
                self.assertLessEqual(value['date'], value['cutoff'])
                self.assertGreaterEqual(value['date'], value['season'][:4] + '-07-01')
                self.assertIn(value['year'], range(2018, 2026))
        self.assertEqual(data['issues'], [])


if __name__ == '__main__':
    unittest.main()
