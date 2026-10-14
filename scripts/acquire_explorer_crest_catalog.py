"""Archive publisher-committed crest images; no Commons retries or proxies."""
import csv,gzip,hashlib,json,time,unicodedata,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
REPO='luukhopman/football-logos'
FOLDERS={'England - Premier League':'Premier League','Spain - LaLiga':'La Liga','Italy - Serie A':'Serie A','Germany - Bundesliga':'Bundesliga','France - Ligue 1':'Ligue 1'}
def key(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c)).replace('ø','o').replace('ł','l')
def fetch(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'FutWAR private research crest audit'}),timeout=30).read()
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():
  if p.read_bytes()!=b:raise ValueError('Immutable source differs: '+str(p))
 else:p.write_bytes(b)
def main():
 folder=ROOT/'data/raw/explorer_crest_catalog/2026-10-10';treepath=folder/'tree.json'
 if not treepath.exists():save(treepath,fetch(f'https://api.github.com/repos/{REPO}/git/trees/master?recursive=1'))
 tree=json.loads(treepath.read_text(encoding='utf-8'));sha=tree['sha'];assert not tree.get('truncated')
 aliases={}
 for fn in ['wikipedia_club_aliases.json','identity_club_aliases.json','club_aliases.json']:
  for league,mapping in json.loads((ROOT/'data'/fn).read_text(encoding='utf-8')).items():aliases.setdefault(league,{}).update(mapping)
 source=json.loads((ROOT/'reports/explorer/data.json').read_text(encoding='utf-8'));teams={(r['league'],r['team']) for r in source['records']}
 names={t:{t[1]} for t in teams}
 explicit={'Heidenheim':'1.FC Heidenheim 1846','Bordeaux':'G. Bordeaux','Norwich City':'Norwich','Bologna':'Bologna FC 1909','Roma':'AS Roma'}
 for team in names:
  if team[1] in explicit:names[team].add(explicit[team[1]])
 with gzip.open(ROOT/'data/raw/transfermarkt_publisher/2026-10-10/clubs.csv.gz','rt',encoding='utf-8') as h:
  for c in csv.DictReader(h):
   league={'GB1':'Premier League','ES1':'La Liga','IT1':'Serie A','L1':'Bundesliga','FR1':'Ligue 1'}.get(c['domestic_competition_id']);team=aliases.get(league,{}).get(c['name'],c['name'])
   if (league,team) in names:names[league,team].add(c['name'])
 candidates={}
 for item in tree['tree']:
  path=item['path'];parts=path.split('/')
  if not path.endswith('.png'):continue
  league=next((l for f,l in FOLDERS.items() if f in parts),None)
  if not league:continue
  stem=Path(path).stem
  for team,choices in names.items():
   if team[0]==league and key(stem) in {key(n) for n in choices}:
    candidates.setdefault(team,[]).append(path)
 assets=[];coverage=[]
 for n,team in enumerate(sorted(teams),1):
  paths=candidates.get(team,[])
  if not paths:coverage.append(dict(league=team[0],team=team[1],status='catalog_name_unresolved'));continue
  path=sorted(paths,key=lambda x:(not x.startswith('logos/'),x),reverse=False)[0]
  u=f'https://raw.githubusercontent.com/{REPO}/{sha}/'+urllib.parse.quote(path,safe='/')
  local=folder/'images'/f'{hashlib.sha256(path.encode()).hexdigest()[:12]}.png'
  if not local.exists():save(local,fetch(u));time.sleep(.25)
  raw=local.read_bytes();assert raw.startswith(b'\x89PNG\r\n\x1a\n')
  assets.append(dict(kind='club',label=team[1],league=team[0],path=local.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),source_page=f'https://github.com/{REPO}/blob/{sha}/'+urllib.parse.quote(path,safe='/'),source_url=u,artist='Club artwork; catalog publisher luukhopman',license='No repository license located; underlying club rights retained; private research only',historical_accuracy='Illustrative archived club crest; exact selected-season edition not guaranteed',retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
  coverage.append(dict(league=team[0],team=team[1],status='archived',source_path=path))
  if n%25==0:print(f'Checked {n}/{len(teams)} clubs; {len(assets)} images archived',flush=True)
 manifest=dict(repository=REPO,commit=sha,tree_sha256=hashlib.sha256(treepath.read_bytes()).hexdigest(),assets=assets,coverage=coverage)
 (ROOT/'data/explorer_crest_catalog.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Archived {len(assets)}/{len(teams)} source-club crests; unmatched names saved.',flush=True)
 print(json.dumps([r for r in coverage if r['status']!='archived'],ensure_ascii=True),flush=True)
if __name__=='__main__':main()
