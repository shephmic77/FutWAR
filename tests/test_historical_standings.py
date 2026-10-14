import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_historical_standings import extract_table,resolve_points


class HistoricalStandingsTests(unittest.TestCase):
    def table(self, points='9', played='4'):
        return '<table><tr>'+''.join('<th>'+h+'</th>' for h in
            ['Pos','Team','Pld','W','D','L','GF','GA','GD','Pts'])+'</tr><tr>'+''.join(
            '<td>'+v+'</td>' for v in ['1','Club (C)<sup>[1]</sup>',played,'3','0','1','6','2','+4',points])+'</tr></table>'

    def test_deduction_preserved_without_recalculating_table_points(self):
        row=extract_table(self.table('7'),1)[0]
        self.assertEqual(row['official_points'],7)
        self.assertEqual(row['source_team_label'],'Club')

    def test_wrong_club_count_and_bad_accounting_rejected(self):
        with self.assertRaises(ValueError): extract_table(self.table(),2)
        with self.assertRaises(ValueError): extract_table(self.table(played='5'),1)

    def test_ambiguous_tables_rejected(self):
        with self.assertRaises(ValueError): extract_table(self.table()+self.table(),1)

    def test_unexplained_points_never_marked_verified(self):
        self.assertEqual(resolve_points(9,7,None),(7,'needs_explanation'))

    def test_reference_error_separate_from_match_points(self):
        review=dict(reference_points=7,reviewed_points=9,points_adjustment=0,
                    classification='secondary_reference_error',source_urls=['https://example.org'])
        self.assertEqual(resolve_points(9,7,review),(9,'secondary_reference_error'))
        with self.assertRaises(ValueError): resolve_points(10,7,review)


if __name__=='__main__': unittest.main()
