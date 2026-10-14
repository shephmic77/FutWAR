import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_statsbomb_coverage import competition_rows, event_summary


def team(team_id, name):
    return {"id": team_id, "name": name}


def event(team_id, event_type, outcome=None, player_id=1):
    row = {"team": team(team_id, "club"), "player": {"id": player_id},
           "type": {"name": event_type}}
    if outcome is not None:
        row["shot"] = {"outcome": {"name": outcome}}
    return row


class StatsBombCoverageAuditTests(unittest.TestCase):
    def test_catalog_builds_all_forty_target_cells_without_inventing_listings(self):
        rows = competition_rows([{
            "competition_name": "Premier League", "competition_gender": "male",
            "competition_youth": False, "season_name": "2017/2018",
            "competition_id": 2, "season_id": 1,
        }])
        self.assertEqual(len(rows), 40)
        self.assertEqual(rows[0]["competition_id"], 2)
        self.assertIsNone(rows[1]["competition_id"])

    def test_goal_shots_reconcile_home_away_score(self):
        match = {"home_team": team(10, "Home"), "away_team": team(20, "Away"),
                 "home_score": 1, "away_score": 0}
        result = event_summary(match, [event(10, "Shot", "Goal"), event(20, "Pass")])
        self.assertTrue(result["score_total_reconciled"])
        self.assertTrue(result["score_by_team_reconciled"])
        self.assertEqual(result["goal_shot_events"], 1)

    def test_own_goal_is_flagged_for_review_and_not_team_reconciled(self):
        match = {"home_team": team(10, "Home"), "away_team": team(20, "Away"),
                 "home_score": 1, "away_score": 0}
        result = event_summary(match, [event(20, "Own Goal Against")])
        self.assertTrue(result["score_total_reconciled"])
        self.assertFalse(result["score_by_team_reconciled"])
        self.assertTrue(result["own_goal_review_needed"])

    def test_missing_event_fields_are_counted(self):
        result = event_summary({}, [{"type": {}, "player": None, "team": None}])
        self.assertEqual(result["events_missing_team"], 1)
        self.assertEqual(result["events_missing_player"], 1)
        self.assertEqual(result["events_missing_type"], 1)
        self.assertFalse(result["score_total_reconciled"])


if __name__ == "__main__":
    unittest.main()
