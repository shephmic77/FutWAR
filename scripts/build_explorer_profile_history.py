"""Build full project-period market/transfer context from hashed local archives."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
from build_explorer_dataset import select_valuation
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifest=json.loads((ROOT/'data/player_identity_source_manifest.json').read_text(encoding='utf-8'));files={f['filename']:f for f in manifest['files']}
 def rows(name):
  entry=files[name+'.csv.gz'];p=ROOT/entry['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256']
  with gzip.open(p,'rt',encoding='utf-8') as h:yield from csv.DictReader(h)
 records=json.loads((ROOT/'reports/explorer/data.json').read_text(encoding='utf-8'))['records'];wanted={r['provider_player_id'] for r in records if r['provider_player_id']}
 values=defaultdict(lambda:defaultdict(set))
 for v in rows('player_valuations'):
  if v['player_id'] not in wanted or v['date'][:10]>'2025-06-30':continue
  try:value=float(v['market_value_in_eur'])
  except ValueError:continue
  if math.isfinite(value) and value>=0:values[v['player_id']][v['date'][:10]].add(value)
 profiles={};issues=[]
 for pid,dates in values.items():
  history=[]
  for date,prices in sorted(dates.items()):
   if len(prices)!=1:issues.append({'player_id':pid,'date':date,'issue':'conflicting values'});continue
   history.append({'date':date,'eur':next(iter(prices))})
  annual=[]
  for year in range(2017,2025):
   season=f'{year}-{str(year+1)[-2:]}';v=select_valuation(history,season)
   if v:annual.append(dict(v,season=season,year=year+1))
  profiles[pid]={'valuation_history':history,'annual_values':annual,'transfers':[]}
 for t in rows('transfers'):
  date=t['transfer_date'][:10]
  if t['player_id'] in profiles and '2017-07-01'<=date<='2025-06-30':profiles[t['player_id']]['transfers'].append(dict(date=date,from_club=t['from_club_name'],to_club=t['to_club_name'],reported_fee=t['transfer_fee'],source='https://github.com/dcaribou/transfermarkt-datasets'))
 result={'profiles':profiles,'source_hashes':{n:files[n+'.csv.gz']['sha256'] for n in ['player_valuations','transfers']},'issues':issues,'policy':'Market/transfer context may predate Big Five statistical coverage; no statistics or identities overwritten; project-period annual June 30 cutoffs; original dates retained.'}
 (ROOT/'reports/explorer/profile_history.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
 print(f'Built context for {len(profiles)} candidate profiles; {sum(len(p["annual_values"]) for p in profiles.values())} annual values; {len(issues)} conflicting date tuples omitted.')
if __name__=='__main__':main()
