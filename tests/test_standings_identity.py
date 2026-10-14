import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_standings_and_identity import compare_references, identity_profile


class StandingsTests(unittest.TestCase):
    def test_points_difference_is_visible_without_imputing_other_fields(self):
        baseline = [dict(league='L',season='2024-25',team='A',earned_match_points='12')]
        refs = [dict(league='L',season='2024-25',team='A',metrics={'earned_match_points':10},
                     source_url='https://example.org/table',evidence_status='reviewed_primary_reference')]
        comparisons, coverage = compare_references(baseline,refs)
        self.assertEqual(comparisons[0]['difference'],2)
        self.assertEqual(len(comparisons),1)
        self.assertIn('goals_for',coverage[0]['unchecked_metrics'])

    def test_unmatched_and_duplicate_references_are_rejected(self):
        row = dict(league='L',season='S',team='A',earned_match_points='12')
        ref = dict(row,metrics={'earned_match_points':12},source_url='https://example.org',evidence_status='reviewed')
        with self.assertRaises(ValueError):
            compare_references([row],[ref,ref])
        with self.assertRaises(ValueError):
            compare_references([row],[dict(ref,team='B')])

    def test_provisional_evidence_and_unreviewed_coverage_stay_visible(self):
        rows = [dict(league='L',season='S',team=t,earned_match_points='12') for t in ('A','B')]
        ref = dict(league='L',season='S',team='A',metrics={'earned_match_points':12},
                   source_url='https://example.org',evidence_status='provisional_season_header_conflict')
        comparisons, coverage = compare_references(rows,[ref])
        self.assertEqual(comparisons[0]['evidence_status'],'provisional_season_header_conflict')
        self.assertEqual(coverage[1]['evidence_status'],'unreviewed')

    def test_same_name_different_birth_years_are_not_merged(self):
        rows = [dict(player='Same Name',born_=year,nation_='X',league='L',team=team,season='S')
                for year,team in [('1990','A'),('1990','B'),('1995','C')]]
        summary,candidates = identity_profile(rows)
        self.assertEqual(summary['name_labels_with_multiple_known_birth_years'],1)
        self.assertEqual(summary['normalized_player_ids_created'],0)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]['status'],'possible_transfer_or_name_collision_unverified')


if __name__ == '__main__':
    unittest.main()
