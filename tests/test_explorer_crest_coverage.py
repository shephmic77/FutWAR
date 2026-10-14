"""Regression coverage for every observed club and league-season."""
import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class CrestCoverageChecks(unittest.TestCase):
    def test_every_observed_club_season_has_fingerprinted_asset(self):
        report=ROOT/'reports/explorer/club_crest_coverage.csv'
        datafile=ROOT/'reports/explorer/data.json'
        if not report.exists() or not datafile.exists():
            self.skipTest('Private explorer has not been built')
        records=json.loads(datafile.read_text(encoding='utf-8'))['records']
        expected={(r['league'],r['season'],r['team']) for r in records}
        with report.open(encoding='utf-8') as h:rows=list(csv.DictReader(h))
        self.assertEqual({(r['league'],r['season'],r['team']) for r in rows},expected)
        self.assertEqual(len(rows),len(expected))
        self.assertEqual(len({(r['league'],r['season']) for r in rows}),40)
        for row in rows:
            self.assertEqual(row['available'],'True',row)
            self.assertEqual(len(row['sha256']),64)
            self.assertTrue(row['source'].startswith('https://'))
        for name in ['explorer_crest_catalog.json','explorer_secondary_crests.json']:
            manifest=json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
            for asset in manifest['assets']:
                self.assertEqual(hashlib.sha256((ROOT/asset['path']).read_bytes()).hexdigest(),asset['sha256'])


if __name__=='__main__':unittest.main()
