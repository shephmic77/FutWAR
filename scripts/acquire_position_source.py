"""Archive the existing publisher's lineup export for a separate position audit."""
from pathlib import Path

import acquire_player_identity_source as publisher


if __name__ == '__main__':
    publisher.FILES = ['game_lineups.csv.gz']
    publisher.MANIFEST = Path('data/position_source_manifest.json')
    publisher.acquire()
