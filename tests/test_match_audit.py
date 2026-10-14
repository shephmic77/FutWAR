import unittest
from scripts.audit_match_results import inspect_matches


class MatchAuditTests(unittest.TestCase):
    def row(self, score=None, date='2020-03-01', home='A', away='B'):
        return {'date':date,'team1':home,'team2':away,'score':{'ft':score} if score is not None else {}}

    def test_unplayed_fixture_is_not_a_zero_zero_result(self):
        completed, teams, issues, duplicates=inspect_matches([self.row([0,0]),self.row()])
        self.assertEqual(len(completed),1)
        self.assertIn(('no_fulltime_score',2),issues)
        self.assertEqual(duplicates,1)

    def test_invalid_numeric_scores_are_rejected(self):
        completed,_,issues,_=inspect_matches([self.row([-1,0]),self.row([True,0]),self.row(['1',0])])
        self.assertEqual(completed,[])
        self.assertEqual(len(issues),3)

    def test_invalid_date_and_same_club_are_flagged(self):
        completed,_,issues,_=inspect_matches([self.row([1,0],date='bad'),self.row([1,0],home='A',away='A')])
        self.assertIn(('invalid_or_missing_date',1),issues)
        self.assertIn(('invalid_teams',2),issues)
        self.assertEqual(len(completed),1)

    def test_home_and_away_are_distinct_fixtures(self):
        completed,teams,issues,duplicates=inspect_matches([self.row([1,0]),self.row([0,1],home='B',away='A')])
        self.assertEqual(len(completed),2)
        self.assertEqual(teams,{'A','B'})
        self.assertEqual(issues,[])
        self.assertEqual(duplicates,0)
