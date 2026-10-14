import unittest
from scripts.prepare_match_supplement import validate_supplements


class SupplementTests(unittest.TestCase):
    def setUp(self):
        self.row = {'league':'La Liga','season':'2024-25','match_date':'2025-05-25',
            'home_label':'A','away_label':'B','home_goals':0,'away_goals':0,
            'source_url':'https://example.org/official-result','verified_on':'2026-10-10'}
        self.key = ('La Liga','2024-25','2025-05-25','A','B')

    def test_verified_zero_zero_is_a_result(self):
        validate_supplements([self.row],{self.key})

    def test_duplicate_supplement_is_rejected(self):
        with self.assertRaises(ValueError): validate_supplements([self.row,self.row],{self.key})

    def test_existing_or_cancelled_fixture_cannot_be_filled(self):
        with self.assertRaises(ValueError): validate_supplements([self.row],set())

    def test_missing_fixture_or_missing_evidence_is_rejected(self):
        with self.assertRaises(ValueError): validate_supplements([],{self.key})
        with self.assertRaises(ValueError): validate_supplements([{**self.row,'source_url':''}],{self.key})

    def test_invalid_goal_types_are_rejected(self):
        for value in (-1,True,'1',1.5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_supplements([{**self.row,'home_goals':value}],{self.key})

    def test_corrupted_accented_club_label_is_rejected(self):
        correct = 'Real Betis Balompi\u00e9'
        corrupted = 'Real Betis Balompi\u00c3\u00a9'
        expected = {('La Liga','2024-25','2025-05-25',correct,'B')}
        validate_supplements([{**self.row,'home_label':correct}],expected)
        with self.assertRaises(ValueError):
            validate_supplements([{**self.row,'home_label':corrupted}],expected)
