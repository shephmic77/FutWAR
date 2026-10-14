"""Resolve additional portrait candidates without altering statistical identities.

Require a unique spelling-normalized full name, birth year and historical
club/league/season appearance. No fuzzy or partial-name matching.
"""
import csv
import gzip
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CODES={'GB1':'Premier League','ES1':'La Liga','IT1':'Serie A','L1':'Bundesliga','FR1':'Ligue 1'}

def spelling(name):
    text=name.casefold().translate(str.maketrans({'ø':'o','ł':'l','đ':'d','ð':'d','þ':'th','æ':'ae','œ':'oe','’':"'"}))
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',text) if not unicodedata.combining(c)).split())

def main():
    manifest=json.loads((ROOT/'data/player_identity_source_manifest.json').read_text(encoding='utf-8'))
    files={f['filename']:f for f in manifest['files']}
    def rows(name):
        item=files[name+'.csv.gz'];p=ROOT/item['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Source changed: '+name)
        with gzip.open(p,'rt',encoding='utf-8-sig',newline='') as h:
            yield from csv.DictReader(h)
    records=json.loads((ROOT/'reports/explorer/data.json').read_text(encoding='utf-8'))['records']
    unresolved=[r for r in records if not r['provider_player_id']]
    index=defaultdict(list)
    for p in rows('players'):
        index[spelling(p['name']),p['date_of_birth'][:4]].append(p)
    aliases={}
    for name in ['wikipedia_club_aliases.json','identity_club_aliases.json','club_aliases.json']:
        for league,mapping in json.loads((ROOT/'data'/name).read_text(encoding='utf-8')).items():
            aliases.setdefault(league,{}).update(mapping)
    clubs={}
    for c in rows('clubs'):
        league=CODES.get(c['domestic_competition_id'])
        if league:clubs[league,aliases.get(league,{}).get(c['name'],c['name'])]=c['club_id']
    wanted={p['player_id'] for r in unresolved for p in index[spelling(r['name']),str(r['details']['birth_year'])]}
    games={g['game_id']:(CODES[g['competition_id']],g['season']+'-'+str(int(g['season'])+1)[-2:])
           for g in rows('games') if g['competition_id'] in CODES and g['season'] in {str(y) for y in range(2017,2025)}}
    memberships=set()
    for a in rows('appearances'):
        if a['player_id'] in wanted and a['game_id'] in games:
            league,season=games[a['game_id']]
            memberships.add((a['player_id'],a['player_club_id'],league,season))
    matches={};queue=[]
    for r in unresolved:
        birth=str(r['details']['birth_year']);cid=clubs.get((r['league'],r['team']))
        candidates=[p for p in index[spelling(r['name']),birth] if (p['player_id'],cid,r['league'],r['season']) in memberships]
        candidates=[p for p in candidates if p['image_url'].startswith('https://img.a.transfermarkt.technology/')]
        if len(candidates)==1:
            p=candidates[0]
            matches[r['id']]={'url':p['image_url'],'source_page':p['url'],'candidate_player_id':p['player_id'],
                'identity_status':'Portrait-only spelling-normalized full-name/birth-year/historical-appearance candidate; not independently verified.'}
        else:
            queue.append({'record_id':r['id'],'player':r['name'],'birth_year':birth,'league':r['league'],'season':r['season'],'team':r['team'],'reason':'No unique supported full-name candidate'})
    folder=ROOT/'reports/explorer'
    (folder/'additional_portraits.json').write_text(json.dumps({'records':matches,'source_hashes':{n:files[n+'.csv.gz']['sha256'] for n in ['players','games','clubs','appearances']},'unresolved_records':len(queue)},ensure_ascii=False,indent=2),encoding='utf-8')
    with (folder/'portrait_review_queue.csv').open('w',encoding='utf-8',newline='') as h:
        writer=csv.DictWriter(h,fieldnames=['record_id','player','birth_year','league','season','team','reason']);writer.writeheader();writer.writerows(queue)
    print(f'Additional portrait candidates: {len(matches)}; unresolved records: {len(queue)}. Statistical identities unchanged.')

if __name__=='__main__':main()
