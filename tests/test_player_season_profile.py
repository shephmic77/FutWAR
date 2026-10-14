"""Synthetic source-profile checks; fixtures never enter the research data folder."""
import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path
from scripts.profile_player_seasons import profile


class PlayerSeasonProfileTests(unittest.TestCase):
    def test_decimal_commas_and_conflicting_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'fixture.csv'
            columns = ['league', 'season', 'team', 'player', 'nation_', 'pos_',
                       'Playing Time_Min', 'Playing Time_MP', 'Playing Time_Starts',
                       'Playing Time_90s', '90s_', 'Performance_Gls', 'Standard_Gls',
                       'Performance_Ast', 'Ast_', 'Expected_xAG', 'xAG_',
                       'Progression_PrgP', 'PrgP_', 'Progression_PrgC', 'Carries_PrgC',
                       'Tackles_TklW', 'Performance_TklW', 'Int_', 'Performance_Int']
            row = dict.fromkeys(columns, '0')
            row.update(league='L', season='S', team='Club', player='Fixture', nation_='X',
                       pos_='MF', **{'Playing Time_Min': '90', 'Playing Time_MP': '1',
                       'Playing Time_Starts': '1', 'Playing Time_90s': '1,0', '90s_': '1,0',
                       'Expected_xAG': '0,3', 'xAG_': '0,3'})
            other = {**row, 'Expected_xAG': '0,4', 'xAG_': '0,4'}
            with source.open('w', encoding='utf-8', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, delimiter=';')
                writer.writeheader()
                writer.writerows([row, other])
            original = source.read_bytes()
            config = {'files': {source.name: {'delimiter': ';', 'decimal': ',',
                      'key_columns': ['league', 'season', 'team', 'player'],
                      'league_aliases': {'L': 'Premier League'}, 'season_aliases': {'S': '2017-18'}}}}
            with contextlib.redirect_stdout(io.StringIO()):
                result = profile(source, base / 'reports', config)
            self.assertEqual(result['numeric_parse_failures'], 0)
            self.assertEqual(result['numeric_constraint_violations'], {})
            self.assertEqual(result['conflicting_key_groups'][0]['rows'], 2)
            self.assertIn('Expected_xAG', result['conflicting_key_groups'][0]['conflicting_columns'])
            self.assertEqual(source.read_bytes(), original)
            with (base / 'reports' / 'candidate_stat_coverage.csv').open(newline='') as handle:
                reports = list(csv.DictReader(handle))
            self.assertEqual(next(r for r in reports if r['season'] == '2017-18' and r['league'] == 'Premier League' and r['column'] == 'Expected_xA')['availability'], 'column_absent')


if __name__ == '__main__':
    unittest.main()
