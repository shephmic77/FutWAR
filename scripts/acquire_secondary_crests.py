"""Archive manually reviewed club matches from a pinned secondary catalog."""
import hashlib,json,time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from acquire_explorer_crest_catalog import ROOT,fetch,save

folder=ROOT/'data/raw/explorer_secondary_crests/2026-10-10'
tree=json.loads((folder/'tree.json').read_text(encoding='utf-8'));sha=tree['sha']
catalog=json.loads((folder/'crests.json').read_text(encoding='utf-8'))['crests']
matches={'Cardiff City':'Cardiff City','Chievo':'Chievo verona','Guingamp':'En Avant de Guingamp','Nürnberg':'FC Nurnberg','Hannover 96':'Hannover 96','Huddersfield':'Huddersfield Town','La Coruña':'RC Deportivo La Coruña','Stoke City':'Stoke City FC','Swansea City':'Swansea City AFC','West Brom':'West Bromwich Albion','Amiens':'Amiens','Caen':'Caen','Dijon':'Dijon','Eibar':'Eibar','Crotone':'Crotone','SPAL':'SPAL','Benevento':'Benevento'}
assets=[]
for team,name in matches.items():
 row=next(r for r in catalog if r['team']==name)
 path='source/crests/'+row['filename'];assert any(t['path']==path for t in tree['tree'])
 url=f'https://raw.githubusercontent.com/guardian/football-assets/{sha}/{path}'
 local=folder/'images'/row['filename']
 if not local.exists():save(local,fetch(url));time.sleep(.3)
 raw=local.read_bytes();assert raw.startswith(b'\x89PNG\r\n\x1a\n')
 assets.append(dict(kind='club',label=team,path=local.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),source_page=f'https://github.com/guardian/football-assets/blob/{sha}/{path}',source_url=url,artist='Club artwork; Guardian catalog',license='Underlying club artwork rights retained; private research only; redistribution not verified',historical_accuracy='Illustrative crest, exact seasonal edition not verified',catalog_team=name,retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
(ROOT/'data/explorer_secondary_crests.json').write_text(json.dumps(dict(commit=sha,assets=assets),ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Archived {len(assets)} reviewed secondary crests.')
# Inspect another public repository for the final four club names.
third=folder/'additional_tree.json'
if not third.exists():save(third,fetch('https://api.github.com/repos/JoseArroyave/football-logos/git/trees/main?recursive=1'))
t=json.loads(third.read_text(encoding='utf-8'))
for r in t['tree']:
 if any(n in r['path'].lower() for n in ['fortuna','duss','huesca','nimes','brescia']):print(r['path'])
print('Additional commit:',t['sha'])
final_matches={'Düsseldorf':'logos/germany/Fortuna_Düsseldorf.svg','Brescia':'logos/italy/Brescia.svg','Huesca':'logos/spain/Huesca.svg','Nîmes':'logos/france/Nîmes_Olympique.svg'}
for team,path in final_matches.items():
 assert any(r['path']==path for r in t['tree'])
 url=f'https://raw.githubusercontent.com/JoseArroyave/football-logos/{t["sha"]}/'+urllib.parse.quote(path,safe='/')
 local=folder/'images'/f'{hashlib.sha256(path.encode()).hexdigest()[:12]}.svg'
 if not local.exists():save(local,fetch(url));time.sleep(.3)
 raw=local.read_bytes();root=ET.fromstring(raw)
 assert root.tag.endswith('svg')
 for node in root.iter():
  assert not node.tag.endswith('script')
  assert not any(k.lower().startswith('on') for k in node.attrib)
  assert not any(('href' in k and v.startswith(('http:','https:','javascript:'))) for k,v in node.attrib.items())
 assets.append(dict(kind='club',label=team,path=local.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),source_page=f'https://github.com/JoseArroyave/football-logos/blob/{t["sha"]}/'+urllib.parse.quote(path,safe='/'),source_url=url,artist='Club artwork; JoseArroyave catalog',license='Catalog declares personal/commercial use; underlying club rights retained; private research only',historical_accuracy='Illustrative crest, exact selected-season edition not verified',retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
(ROOT/'data/explorer_secondary_crests.json').write_text(json.dumps(dict(commit=sha,additional_commit=t['sha'],assets=assets),ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Total secondary crests: {len(assets)}')
