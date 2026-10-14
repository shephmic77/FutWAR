import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from compare_action_credit_pilot import is_shot_ending, possession_proxies


def event(team, name, subevent=None, period='1H'):
    return {'teamId': team, 'eventName': name, 'subEventName': subevent,
            'matchPeriod': period}


class ActionCreditSequenceTests(unittest.TestCase):
    def test_team_change_and_shot_close_proxy(self):
        passes = event(1, 'Pass'), event(1, 'Duel')
        shot = event(1, 'Shot')
        opponent = event(2, 'Pass')
        sequences = list(possession_proxies([*passes, shot, opponent]))
        self.assertEqual(sequences, [[*passes, shot], [opponent]])
        self.assertTrue(is_shot_ending(sequences[0][-1]))
        self.assertFalse(is_shot_ending(sequences[1][-1]))

    def test_foul_and_restart_separate_proxies(self):
        first = event(1, 'Pass')
        foul = event(1, 'Foul')
        restart = event(1, 'Free Kick', 'Corner')
        shot = event(1, 'Shot')
        sequences = list(possession_proxies([first, foul, restart, shot]))
        self.assertEqual(sequences, [[first, foul], [restart, shot]])

    def test_period_change_separates_proxies(self):
        first = event(1, 'Pass', period='1H')
        second = event(1, 'Shot', period='2H')
        sequences = list(possession_proxies([first, second]))
        self.assertEqual(sequences, [[first], [second]])

    def test_penalty_free_kick_shot_counts_as_shot_ending(self):
        self.assertTrue(is_shot_ending(event(1, 'Free Kick', 'Penalty')))
        self.assertTrue(is_shot_ending(event(1, 'Free Kick', 'Free kick shot')))
        self.assertFalse(is_shot_ending(event(1, 'Free Kick', 'Corner')))


if __name__ == '__main__':
    unittest.main()
