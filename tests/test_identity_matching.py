import sys
import unittest
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_player_identity_source import identity_candidates,name_key
from prepare_identity_pilot import validate_link


class IdentityTests(unittest.TestCase):
    def test_normalization_preserves_full_name_tokens(self):
        self.assertEqual(name_key(' Aarón  Martín '),'aaron martin')
        self.assertNotEqual(name_key('Aaron Martin'),name_key('Martin'))

    def test_current_club_does_not_establish_historical_membership(self):
        row=dict(player='Player',born_='2000',league='L',season='S',team='Club')
        p=dict(player_id='1',current_club_id='10')
        index={(name_key('Player'),'2000'):[p]}
        self.assertEqual(identity_candidates(row,index,set(),{('L','Club'):'10'})[1],
                         'no_supported_exact_name_candidate')

    def test_same_name_birth_year_multiple_players_stay_ambiguous(self):
        row=dict(player='Player',born_='2000',league='L',season='S',team='Club')
        index={('player','2000'):[dict(player_id='1'),dict(player_id='2')]}
        membership={(pid,'10','L','S') for pid in ['1','2']}
        self.assertEqual(identity_candidates(row,index,membership,{('L','Club'):'10'})[1],'ambiguous_candidates')

    def test_missing_birth_year_never_assigns_id(self):
        self.assertEqual(identity_candidates(dict(born_=''),{},set(),{})[1],'missing_birth_year')

    def test_review_rejects_wrong_birth_date_or_candidate(self):
        local=dict(player='Player',born_='2000')
        candidate=dict(status='unique_candidate_with_historical_appearance',candidate_provider_ids='1')
        review=dict(name='Player',date_of_birth='2000-01-01',provider_player_id='1',source_urls=['https://example.org'])
        profile=dict(name='Player',date_of_birth='2000-01-02')
        with self.assertRaises(ValueError):validate_link(local,candidate,review,profile)


if __name__=='__main__':unittest.main()
