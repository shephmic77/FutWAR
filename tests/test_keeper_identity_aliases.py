import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_staged_keeper_identities import reviewed_alias_key


class KeeperAliasTests(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((ROOT / 'data/keeper_identity_aliases.json').read_text(encoding='utf-8'))['rules']
        self.record = dict(league='Ligue 1', season='2021-22', team_name='Lille',
                           player_name='Leonardo César Jardim', birth_year=1995)

    def test_alias_is_restricted_to_reviewed_context(self):
        self.assertIsNotNone(reviewed_alias_key(self.record, self.rules)[0])
        for field, value in [('birth_year', 1974), ('team_name', 'Monaco'),
                             ('season', '2024-25'), ('league', 'Premier League')]:
            changed = {**self.record, field: value}
            self.assertEqual(reviewed_alias_key(changed, self.rules), (None, None))

    def test_conflicting_alias_rules_fail(self):
        with self.assertRaises(ValueError):
            reviewed_alias_key(self.record, self.rules + [self.rules[2]])


if __name__ == '__main__':
    unittest.main()
