import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from value_comparison_methods import action_probability_change,above_baseline,annual_commitment,accessible_baseline,expected_points,season_specific_total


class ComparisonMethodTests(unittest.TestCase):
    def test_period_uses_its_own_year_and_preserves_missing_baseline(self):
        rows=[dict(season=s,team='T',position='LB',comparison='league',minutes=900,value_per90=.3) for s in ['2023-24','2024-25']]
        baselines={('2023-24','T','LB','league'):.1,('2024-25','T','LB','league'):.2}
        self.assertAlmostEqual(season_specific_total(rows,baselines)['total'],3)
        del baselines[('2023-24','T','LB','league')]
        self.assertIsNone(season_specific_total(rows,baselines)['total'])
    def test_attack_and_prevention_share_sign(self):
        self.assertAlmostEqual(action_probability_change(.1,.2,.2,.1),.2)
        self.assertLess(action_probability_change(.2,.1,.1,.2),0)
        with self.assertRaises(ValueError):action_probability_change(2,0,0,0)

    def test_units_exposure_and_missing_guard(self):
        self.assertEqual(above_baseline(.2,.1,900)['total'],1)
        with self.assertRaises(ValueError):above_baseline(None,.1,900)
        with self.assertRaises(ValueError):above_baseline(.1,.1,-1)

    def test_free_transfer_still_has_wages(self):
        self.assertEqual(annual_commitment(0,2,100,10,0,20),130)
        with self.assertRaises(ValueError):annual_commitment(0,2,None,0,0,0)

    def test_budget_position_future_and_uncertainty_filters(self):
        def candidate(id,**changes):
            row=dict(id=id,positions=['LB'],availability_verified=True,information_date='2024-06-01',performance_reliability_reviewed=True,value_per90=.1,acceptance_weight=1,cost=dict(transfer_fee=0,contract_years=2,annual_gross_wages=100,annual_agent_cost=0,annual_loan_cost=0,annual_signing_cost=0))
            row.update(changes);return row
        rows=[candidate('ok'),candidate('wrong',positions=['RB']),candidate('future',information_date='2025-01-01'),candidate('unknown',performance_reliability_reviewed=False)]
        result=accessible_baseline(rows,'LB',100,'2024-07-01')
        self.assertEqual(result['baseline_per90'],.1)
        self.assertEqual(len(result['excluded_candidates']),3)
        self.assertIsNone(accessible_baseline(rows,'LB',99,'2024-07-01')['baseline_per90'])

    def test_points_not_universal_goal_multiplier(self):
        self.assertAlmostEqual(expected_points(.5,.2),1.7)
        with self.assertRaises(ValueError):expected_points(.7,.5)


if __name__=='__main__':unittest.main()
