import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analysis_tracks import position_summary,overlap_summary,OUTFIELD_METRICS,KEEPER_METRICS


class AnalysisTrackTests(unittest.TestCase):
    def cohorts(self):
        outfield=[]
        for league in ['A','B']:
            for n in range(3):
                row=dict(league=league,season='2024-25',analysis_position='FW',source_variant='original')
                row.update({m+'_per90':float(n) for m in ['goals','assists',*OUTFIELD_METRICS]})
                row['assists_per90']=float(n if league=='A' else 2-n)
                outfield.append(row)
        keeper=[]
        for n in range(3):
            row=dict(league='A',season='2024-25',analysis_position='GK',source_variant='release',has_psxg_warning=n==0)
            row.update({m:float(n) for m in KEEPER_METRICS})
            keeper.append(row)
        return pd.DataFrame(outfield),pd.DataFrame(keeper)

    def test_position_description_contains_gk_without_shared_score(self):
        outfield,keeper=self.cohorts()
        result=position_summary(outfield,keeper)
        self.assertEqual(set(result.position),{'FW','GK'})
        self.assertEqual(result[result.position.eq('GK')].available_values.tolist(),[3]*len(KEEPER_METRICS))
        self.assertNotIn('score',result.columns)

    def test_overlap_preserves_league_context_and_source_warning_exclusion(self):
        outfield,keeper=self.cohorts()
        result=overlap_summary(outfield,keeper)
        pair=result[result.left_metric.eq('goals_per90')&result.right_metric.eq('assists_per90')]
        self.assertEqual(pair.set_index('league').spearman.to_dict(),{'A':1.,'B':-1.})
        psxg=result[result.position.eq('GK')&(result.left_metric.eq('psxg_per90')|result.right_metric.eq('psxg_per90'))]
        self.assertTrue(psxg.paired_records.eq(2).all())
        self.assertTrue(psxg.spearman.isna().all())
        self.assertEqual(keeper.psxg_per90.tolist(),[0.,1.,2.])


if __name__=='__main__':
    unittest.main()
