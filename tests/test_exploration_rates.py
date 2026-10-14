import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from explore_player_metrics import weighted_rate,eligibility_masks


class ExplorationRateTests(unittest.TestCase):
    def test_missing_metric_exposure_is_not_in_denominator(self):
        values=pd.Series([10.,np.nan,0.]);minutes=pd.Series([900.,1800.,900.])
        self.assertAlmostEqual(weighted_rate(values,minutes),.5)

    def test_no_known_positive_exposure_is_missing_not_zero(self):
        self.assertTrue(np.isnan(weighted_rate(pd.Series([1.,np.nan]),pd.Series([0.,900.]))))

    def test_cutoff_boundary_and_goalkeeper_are_counted_separately(self):
        df=pd.DataFrame(dict(nominal_position=['DF','DF','MF,FW','GK',None],minutes=[899,900,1000,1500,1500]))
        outfield,eligible=eligibility_masks(df,900)
        self.assertEqual(outfield.tolist(),[True,True,True,False,False])
        self.assertEqual(eligible.tolist(),[False,True,True,False,False])


if __name__=='__main__':unittest.main()
