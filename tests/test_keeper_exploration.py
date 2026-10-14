import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from explore_keeper_metrics import prepare


class KeeperExplorationTests(unittest.TestCase):
    def frame(self):
        row = dict(nominal_position='GK', keeper_minutes=900., unresolved_quality_flags='[]',
            exposure_correction_warnings='[]', psxg_correction_warnings='[]',
            source_variant='archive', psxg_correction_provenance='', shots_on_target_against=10.,
            saves=8., psxg=np.nan, reported_psxg_delta=1., pass_attempts=100.,
            crosses_faced=0., crosses_stopped=0., sweeper_actions=0.)
        return pd.DataFrame([row, {**row, 'keeper_minutes':899.}, {**row, 'keeper_minutes':np.nan},
            {**row, 'nominal_position':'DF'}, {**row, 'psxg':0.,
              'unresolved_quality_flags':'["reported_psxg_residual_arithmetic_review"]'}])

    def test_exposure_cutoff_and_missing_zero_handling(self):
        result = prepare(self.frame())
        self.assertEqual(result.eligible.tolist(), [True,False,False,False,True])
        self.assertTrue(pd.isna(result.loc[0,'psxg_per90']))
        self.assertEqual(result.loc[4,'psxg_per90'],0.)
        self.assertTrue(pd.isna(result.loc[2,'saves_per90']))
        self.assertTrue(result.crosses_stopped_share.isna().all())

    def test_residual_flag_does_not_discard_other_measurements(self):
        result = prepare(self.frame())
        self.assertTrue(pd.isna(result.loc[4,'reported_residual_per90']))
        self.assertEqual(result.loc[4,'saves_per90'],.8)
        self.assertEqual(result.loc[4,'unresolved_quality_flags'], '["reported_psxg_residual_arithmetic_review"]')


if __name__ == '__main__':
    unittest.main()
