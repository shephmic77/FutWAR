import sys
import unittest
from pathlib import Path
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from research_metric_usefulness import association, specific_role, team_aggregates, attach_context, count_rate, overlap


class MetricUsefulnessTests(unittest.TestCase):
    def test_additional_rates_preserve_blank_and_zero(self):
        self.assertTrue(pd.isna(count_rate('',900)))
        self.assertEqual(count_rate('0',900),0)
        self.assertEqual(count_rate('12,5',900),1.25)
        with self.assertRaises(ValueError):count_rate('-1',900)

    def test_pairwise_missing_counts_in_cached_matrix(self):
        frame=pd.DataFrame(dict(league=['L']*4,season=['S']*4,role=['CM']*4,source_variant=['X']*4,domain=['Outfield']*4,a=[1,2,3,4],b=[4,None,2,1]))
        result=overlap(frame,['a','b']).iloc[0]
        self.assertEqual(result.paired_records,3)
        self.assertEqual(result.spearman,-1)

    def test_missing_pairs_not_zero_and_constant_undefined(self):
        n,rho,status=association(pd.DataFrame({'a':[1,2,None],'b':[2,3,4]}),'a','b')
        self.assertEqual(n,2)
        self.assertTrue(pd.isna(rho))
        self.assertEqual(status,'fewer_than_three_pairs')
        self.assertEqual(association(pd.DataFrame({'a':[1,1,1],'b':[1,2,3]}),'a','b')[2],'constant_pair')

    def test_teammates_are_one_club_observation_with_exposure_weights(self):
        frame=pd.DataFrame([
            dict(league='A',season='2024-25',role='CB',source_variant='original',context_team='Club',domain='Outfield',minutes=m,metric=v,team_goals_against_per_match=1,team_goals_for_per_match=2)
            for m,v in [(900,1),(2700,3)]])
        result=team_aggregates(frame,['metric'])
        self.assertEqual(len(result),1)
        self.assertEqual(result.metric.iloc[0],2.5)
        self.assertEqual(result.metric_minutes.iloc[0],3600)
        self.assertEqual(result.included_records.iloc[0],2)

    def test_conflicting_team_context_fails(self):
        frame=pd.DataFrame([
            dict(league='A',season='S',role='CB',source_variant='X',context_team='T',domain='Outfield',minutes=900,metric=1,team_goals_against_per_match=v,team_goals_for_per_match=2) for v in [1,2]])
        with self.assertRaises(ValueError):team_aggregates(frame,['metric'])

    def test_no_invented_specific_roles(self):
        self.assertIsNone(specific_role('MF,DF'))
        self.assertIsNone(specific_role(None))
        self.assertEqual(specific_role('DM'),'CDM')
        self.assertEqual(specific_role('RWB'),'RWB')

    def test_join_fails_wrong_metadata(self):
        outfield=pd.DataFrame([dict(record_id='original_player:1',player_name='Wrong',team_name='T',league='L',season='S')])
        record=dict(id='original_player:1',name='Correct',team='T',league='L',season='S')
        with self.assertRaises(ValueError):attach_context(outfield,pd.DataFrame(),[record])


if __name__=='__main__':unittest.main()
