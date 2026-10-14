"""Acquire public Football-Data season CSVs unchanged, and audit all 40 cells."""
import csv,hashlib,io,json,time,urllib.request
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CODES={'E0':'Premier League','SP1':'La Liga','I1':'Serie A','D1':'Bundesliga','F1':'Ligue 1'}
FIELDS=['FTHG','FTAG','HS','AS','HST','AST','HC','AC','HF','AF','HY','AY','HR','AR']


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'FutWAR private academic research; source attribution retained'})
    with urllib.request.urlopen(request,timeout=40) as response:return response.read()


def audit_rows(rows):
    rows=[r for r in rows if r.get('HomeTeam') and r.get('AwayTeam')]
    keys=[(r['Date'],r['HomeTeam'],r['AwayTeam']) for r in rows]
    invalid=[]
    for i,row in enumerate(rows,1):
        for field in FIELDS:
            value=row.get(field,'')
            if value not in ('',None):
                try:
                    if float(value)<0:invalid.append((i,field,'negative'))
                except ValueError:invalid.append((i,field,'not_numeric'))
    return rows,dict(records=len(rows),clubs=len({r[t] for r in rows for t in ['HomeTeam','AwayTeam']}),
                     duplicate_fixture_keys=sum(v-1 for v in Counter(keys).values()),invalid_values=invalid)


def main():
    folder=ROOT/'data/raw/football_data_match_context/2026-10-10'
    folder.mkdir(parents=True,exist_ok=True)
    files=[];coverage=[];audits=[]
    for name,url in [('notes.txt','https://www.football-data.co.uk/notes.txt'),('source_page.html','https://www.football-data.co.uk/data.php')]:
        path=folder/name
        if not path.exists():path.write_bytes(fetch(url));time.sleep(.4)
    for year in range(2017,2025):
        season=f'{year}-{str(year+1)[-2:]}';code=f'{str(year)[-2:]}{str(year+1)[-2:]}'
        for division,league in CODES.items():
            path=folder/f'{code}_{division}.csv';url=f'https://www.football-data.co.uk/mmz4281/{code}/{division}.csv'
            if not path.exists():path.write_bytes(fetch(url));time.sleep(.4)
            raw=path.read_bytes()
            try:text=raw.decode('utf-8-sig')
            except UnicodeDecodeError:text=raw.decode('cp1252')
            rows,checked=audit_rows(list(csv.DictReader(io.StringIO(text))))
            audits.append(dict(league=league,season=season,**checked))
            files.append(dict(league=league,season=season,path=path.relative_to(ROOT).as_posix(),source_url=url,
                sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),retrieved_at_utc=datetime.now(timezone.utc).isoformat()))
            for field in FIELDS:
                coverage.append(dict(league=league,season=season,field=field,records=len(rows),
                    available=sum(r.get(field) not in ('',None) for r in rows)))
        print('Audited',season,flush=True)
    manifest=dict(provider='Football-Data.co.uk',source_page='https://www.football-data.co.uk/data.php',
        definitions='https://www.football-data.co.uk/notes.txt',files=files,
        use='Public free downloads; credit Football-Data.co.uk; private research; upstream redistribution rights not independently settled')
    (ROOT/'data/match_context_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    output=ROOT/'reports/match_context';output.mkdir(parents=True,exist_ok=True)
    with (output/'coverage.csv').open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
    (output/'audit.json').write_text(json.dumps(audits,indent=2),encoding='utf-8')
    print('Archived 40 source CSVs;',sum(a['records'] for a in audits),'matches; no automatic player merge',flush=True)


if __name__=='__main__':main()
