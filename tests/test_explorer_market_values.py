import unittest
from scripts.build_explorer_dataset import select_valuation, number


class June30ValuationTests(unittest.TestCase):
    def test_no_future_estimate_used(self):
        history=[{'date':'2018-06-07','eur':80000000},{'date':'2018-07-01','eur':120000000}]
        self.assertEqual(select_valuation(history,'2017-18')['eur'],80000000)

    def test_cutoff_date_included_and_zero_preserved(self):
        selected=select_valuation([{'date':'2018-06-30','eur':0}],'2017-18')
        self.assertEqual(selected['eur'],0)
        self.assertEqual(selected['cutoff'],'2018-06-30')

    def test_previous_season_and_latest_profile_are_not_backfilled(self):
        history=[{'date':'2017-06-30','eur':1000000},{'date':'2026-05-01','eur':10000000}]
        self.assertIsNone(select_valuation(history,'2017-18'))

    def test_missing_values_do_not_become_zero(self):
        self.assertIsNone(number(''))
        self.assertEqual(number('0'),0)
        with self.assertRaises(ValueError):number('NaN')


if __name__=='__main__':unittest.main()
