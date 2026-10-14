"""Synthetic temporary fixtures test audit behavior; these are not research data."""
import csv
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.audit_data import audit, LEAGUES, SEASONS


class AuditTests(unittest.TestCase):
    def run_fixture(self, content=None, config=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        raw = base / "raw"
        raw.mkdir()
        if content is not None:
            (raw / "fixture.csv").write_text(content, encoding="utf-8")
        before = hashlib.sha256((raw / "fixture.csv").read_bytes()).hexdigest() if content is not None else None
        result = audit(raw, base / "reports", config or {}, {})
        if before:
            self.assertEqual(before, hashlib.sha256((raw / "fixture.csv").read_bytes()).hexdigest())
        return result, base / "reports"

    def test_empty_input_does_not_claim_coverage(self):
        result, _ = self.run_fixture()
        self.assertEqual(len(result["coverage"]), len(LEAGUES) * len(SEASONS))
        self.assertTrue(all(c["status"] == "no_input_data" for c in result["coverage"]))

    def test_duplicates_missingness_aliases_and_bad_rows(self):
        result, output = self.run_fixture(
            "League,Season,Position,ID,Goals\nENG,22/23,DF,a,0\nENG,22/23,DF,a,0\nENG,22/23,DF,b,NA\nbad,row\n",
            {"columns": {"league": "League", "season": "Season", "position": "Position"},
             "league_aliases": {"ENG": "Premier League"}, "season_aliases": {"22/23": "2022-23"},
             "null_tokens": ["", "NA"], "key_columns": ["ID"]})
        summary = result["files"][0]
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["malformed_rows"], 1)
        self.assertEqual(summary["exact_duplicate_rows"], 1)
        self.assertEqual(summary["duplicate_key_rows"], 1)
        with (output / "column_quality.csv").open(newline="", encoding="utf-8") as handle:
            goals = next(row for row in csv.DictReader(handle) if row["column"] == "Goals")
        self.assertEqual(goals["missing"], "1")
        self.assertEqual(next(c for c in result["coverage"] if c["league"] == "Premier League" and c["season"] == "2022-23")["observed_rows"], 3)
        self.assertEqual(result["coverage"][0]["completeness"], "not_verified")

    def test_unmapped_coverage_remains_unknown(self):
        result, _ = self.run_fixture("League,Season\nENG,22/23\n")
        self.assertTrue(all(c["status"] == "unknown_mapping_or_read_error" for c in result["coverage"]))

    def test_invalid_header_and_bad_mapping_are_errors(self):
        for content, config in [("A,A\n1,2\n", {}), ("A,B\n1,2\n", {"columns": {"league": "Missing"}})]:
            with self.subTest(content=content):
                result, _ = self.run_fixture(content, config)
                self.assertEqual(result["files"][0]["status"], "error")

    def test_all_missing_metric_is_visible_in_group_report(self):
        _, output = self.run_fixture("League,Season,Metric\nPremier League,2022-23,\n",
                                     {"columns": {"league": "League", "season": "Season"}})
        with (output / "stat_availability.csv").open(newline="", encoding="utf-8") as handle:
            metric = next(row for row in csv.DictReader(handle) if row["column"] == "Metric")
        self.assertEqual(metric["availability"], "all_missing")
        self.assertEqual(metric["position"], "unknown")


if __name__ == "__main__":
    unittest.main()
