"""Archive catalog metadata for manual review of missing club identities."""
import json
from pathlib import Path
from acquire_explorer_crest_catalog import fetch, save, ROOT

folder=ROOT/'data/raw/explorer_secondary_crests/2026-10-10'
treepath=folder/'tree.json'
if not treepath.exists():save(treepath,fetch('https://api.github.com/repos/guardian/football-assets/git/trees/main?recursive=1'))
tree=json.loads(treepath.read_text());sha=tree['sha']
catalog=folder/'crests.json'
if not catalog.exists():save(catalog,fetch(f'https://raw.githubusercontent.com/guardian/football-assets/{sha}/source/crests/crests.json'))
names=json.loads(catalog.read_text(encoding='utf-8'))['crests']
terms=['duss','hann','nurn','eibar','hues','coru','amiens','caen','dijon','guing','nime','cardiff','hudder','stoke','swansea','brom','benev','brescia','chievo','crotone','spal']
for row in names:
    import unicodedata
    name=''.join(c for c in unicodedata.normalize('NFKD',row['team'].lower()) if not unicodedata.combining(c))
    if any(t in name for t in terms):
        paths=[r['path'] for r in tree['tree'] if Path(r['path']).name==row['filename']]
        print(json.dumps(dict(row,paths=paths)))
print('commit',sha)
