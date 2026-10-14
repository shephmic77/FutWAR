import sys,unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_event_value_pilot import scoring_team,horizon_labels,split_for,event_vector
from run_expected_points_state_pilot import align_heldout_metadata


def event(team=1,tags=(),period='1H',kind='Pass',seconds=0):
    return dict(teamId=team,tags=[dict(id=t) for t in tags],matchPeriod=period,eventName=kind,eventId=8,subEventId=85,eventSec=seconds,positions=[dict(x=50,y=50),dict(x=60,y=50)])


class PilotTests(unittest.TestCase):
    def test_paired_metadata_follows_sorted_sample_ids(self):
        frame = pd.DataFrame([
            dict(sample_id='z', split='test', state='after', event_type_name='Shot'),
            dict(sample_id='a', split='test', state='after', event_type_name='Pass'),
            dict(sample_id='z', split='test', state='before', event_type_name='Shot'),
        ])
        aligned = align_heldout_metadata(frame, ['a', 'z'])
        self.assertEqual(aligned.event_type_name.tolist(), ['Pass', 'Shot'])

    def test_goal_is_not_double_counted_on_keeper_record(self):
        self.assertEqual(scoring_team(event(tags=[101],kind='Shot'),(1,2)),1)
        self.assertIsNone(scoring_team(event(team=2,tags=[101],kind='Save attempt'),(1,2)))
        self.assertEqual(scoring_team(event(tags=[102]),(1,2)),2)

    def test_future_only_and_half_boundary(self):
        e=[event(tags=[101]),event(),event(team=2,tags=[101]),event(period='2H')]
        labels=horizon_labels(e,(1,2),horizon=2)
        self.assertEqual(labels[0],(0,1))
        self.assertIsNone(labels[1])
        self.assertIsNone(labels[-1])

    def test_history_does_not_borrow_from_second_half_or_future(self):
        e=[event(tags=[1801],seconds=2),event(period='2H',seconds=1)]
        import math
        self.assertTrue(math.isnan(event_vector(e,1)[10]))
        self.assertEqual(split_for('2017-12-31'),'train')
        self.assertEqual(split_for('2018-01-01'),'validation')
        self.assertEqual(split_for('2018-03-01'),'test')


if __name__=='__main__':unittest.main()
