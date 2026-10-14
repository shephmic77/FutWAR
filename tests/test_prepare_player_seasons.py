import unittest
from scripts.prepare_player_seasons import collapse_group, apply_reviewed_enrichments
import json
from pathlib import Path


class CorrectionTests(unittest.TestCase):
    def test_keeps_zero_and_unambiguous_values_without_imputation(self):
        rows = [{'Goals': '0', 'Passes': '', 'Unknown': '', 'Subs_unSub': '0'},
                {'Goals': '0', 'Passes': '11', 'Unknown': '', 'Subs_unSub': '1'}]
        result = collapse_group(rows)
        self.assertEqual(result, {'Goals': '0', 'Passes': '11', 'Unknown': '', 'Subs_unSub': ''})
        self.assertEqual(rows[0]['Subs_unSub'], '0')

    def test_new_conflict_is_rejected(self):
        rows = [{'Goals': '0', 'Subs_unSub': '0'}, {'Goals': '1', 'Subs_unSub': '1'}]
        with self.assertRaises(ValueError):
            collapse_group(rows)

    def test_changed_expected_conflict_is_rejected(self):
        with self.assertRaises(ValueError):
            collapse_group([{'Subs_unSub': '0'}, {'Subs_unSub': '0'}])


class EnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads(Path('data/reviewed_enrichments.json').read_text(encoding='utf-8-sig'))

    def test_position_fill_has_evidence(self):
        row = dict(zip(['league','season','team','player'], self.rules['position_enrichment']['key']))
        row['pos_'] = ''
        flags, notes = apply_reviewed_enrichments(row, [], self.rules)
        self.assertEqual(row['pos_'], 'DF')
        self.assertIn('externally_sourced_broad_position', flags)
        self.assertTrue(notes[0]['source_url'])

    def test_existing_position_cannot_be_overwritten(self):
        row = dict(zip(['league','season','team','player'], self.rules['position_enrichment']['key']))
        row['pos_'] = 'MF'
        with self.assertRaises(ValueError):
            apply_reviewed_enrichments(row, [], self.rules)

    def test_exposure_disagreement_is_only_flagged(self):
        row = dict(zip(['league','season','team','player'], self.rules['appearance_discrepancy']['key']))
        row.update(pos_='MF', minutes='1', npxg='')
        before = row.copy()
        flags, notes = apply_reviewed_enrichments(row, [], self.rules)
        self.assertEqual(row, before)
        self.assertIn('external_appearance_minutes_discrepancy', flags)
