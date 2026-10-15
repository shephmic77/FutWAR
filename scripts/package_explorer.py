"""Build a self-contained local explorer and a split, faster public site."""
import base64
import csv
import gzip
import hashlib
import json
import mimetypes
import html as html_tools
import unicodedata
from collections import defaultdict
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    folder=ROOT/'reports/explorer'
    data=json.loads((folder/'data.json').read_text(encoding='utf-8'))
    # Use recorded final table order, not a points/GD sort that loses deductions
    # or league-specific tie-breakers. Retain the archived secondary citation.
    standings_manifest=json.loads((ROOT/'data/wikipedia_standings_manifest.json').read_text(encoding='utf-8'))
    source_cells={}
    for source in standings_manifest['files']:
        if hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError('Standings archive fingerprint differs')
        source_cells[source['league'],source['season']]=source
    with (ROOT/'data/processed/postgres/historical_standings.csv').open(encoding='utf-8') as handle:
        standings=list(csv.DictReader(handle))
    positions={};sizes={}
    for standing in standings:
        cell=(standing['league'],standing['season']);source=source_cells[cell]
        if standing['source_sha256']!=source['sha256'] or standing['source_url']!=source['source_url']:
            raise ValueError('Standings provenance differs')
        key=(*cell,standing['team'])
        if key in positions:raise ValueError('Duplicate club-season standing')
        positions[key]=standing;sizes[cell]=sizes.get(cell,0)+1
    if len(positions)!=780 or len(sizes)!=40:raise ValueError('Incomplete standings scope')
    for cell,size in sizes.items():
        expected=18 if cell[0]=='Bundesliga' or (cell[0]=='Ligue 1' and cell[1]>='2023-24') else 20
        order=[int(s['official_position']) for s in standings if (s['league'],s['season'])==cell]
        if size!=expected or sorted(order)!=list(range(1,expected+1)):
            raise ValueError('Invalid final standings order')
    contexts=data['teams']+[r['team_context'] for r in data['records'] if r.get('team_context')]
    for context in contexts:
        key=(context['league'],context['season'],context['team'])
        standing=positions.get(key)
        if not standing:raise ValueError('Missing club-season standing: '+str(key))
        context['final_league_position']=int(standing['official_position'])
        context['league_team_count']=sizes[key[:2]]
        context['standings_source_url']=standing['source_url']
    print(f'Final standings coverage: {len(positions)} club-seasons across {len(sizes)} league-seasons')
    with (folder/'source_field_coverage.csv').open(encoding='utf-8') as handle:
        data['fieldCoverage']=list(csv.DictReader(handle))
    # Keep publisher-provided portrait URLs tied to the already audited candidate
    # identity. Load only the currently displayed images, rather than bulk-fetching
    # thousands of files or retrying rate-limited Commons downloads.
    manifest=json.loads((ROOT/'data/player_identity_source_manifest.json').read_text(encoding='utf-8'))
    player_file=next(f for f in manifest['files'] if f['filename']=='players.csv.gz')
    player_archive=ROOT/player_file['path']
    assert hashlib.sha256(player_archive.read_bytes()).hexdigest()==player_file['sha256']
    with gzip.open(player_archive,'rt',encoding='utf-8') as handle:
        portraits={r['player_id']:{'url':r['image_url'],'source_page':r['url']}
                  for r in csv.DictReader(handle)
                  if r['image_url'].startswith('https://img.a.transfermarkt.technology/')}
    for record in data['records']:
        record['profile_portrait']=portraits.get(str(record['provider_player_id']))
        if record['domain']=='Outfield':
            extras={'blocks_per90':'Blocks_Blocks','recoveries_per90':'Performance_Recov',
                    'aerial_duels_won_per90':'Aerial Duels_Won','aerial_duels_lost_per90':'Aerial Duels_Lost',
                    'key_passes_per90':'KP_','progressive_receptions_per90':'Receiving_PrgR',
                    'passes_into_box_per90':'PPA_','dispossessions_per90':'Carries_Dis',
                    'miscontrols_per90':'Carries_Mis','errors_per90':'Err_'}
            for key,column in extras.items():
                source=record['source_stats'].get(column,'')
                total=float(str(source).replace(',','.')) if source not in ('',None) else None
                if total is not None and total<0:raise ValueError('Negative additional count')
                record['totals'][key]=total
                record['metrics'][key]=90*total/record['minutes'] if total is not None and record['minutes']>0 else None
    extra_path=folder/'additional_portraits.json'
    if extra_path.exists():
        extra=json.loads(extra_path.read_text(encoding='utf-8'))
        for name,expected in extra['source_hashes'].items():
            entry=next(f for f in manifest['files'] if f['filename']==name+'.csv.gz')
            if entry['sha256']!=expected:raise ValueError('Portrait candidate source differs: '+name)
        for record in data['records']:
            if not record['profile_portrait']:
                record['profile_portrait']=extra['records'].get(record['id'])
    data['portrait_coverage']={
        'linked_records':sum(bool(r['profile_portrait']) for r in data['records']),
        'unresolved_records':sum(not r['profile_portrait'] for r in data['records']),
        'source_sha256':player_file['sha256'],
        'policy':'On-demand remote portraits; private research only; upstream image rights unconfirmed; not historical-season photos.'}
    (folder/'portrait_coverage.json').write_text(json.dumps(data['portrait_coverage'],indent=2),encoding='utf-8')
    images=[]
    public_assets=ROOT/'site'/'assets'
    public_assets.mkdir(parents=True,exist_ok=True)
    def add(asset,label=None):
        a=dict(asset)
        if label:a['label']=label
        path=ROOT/a['path'];raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=a['sha256']:raise ValueError('Asset fingerprint differs: '+str(path))
        a['data_url']='data:'+mimetypes.guess_type(path.name)[0]+';base64,'+base64.b64encode(raw).decode('ascii')
        suffix=path.suffix.lower() or '.bin'
        public_name=a['sha256'][:20]+suffix
        shutil.copyfile(path,public_assets/public_name)
        a['site_url']='assets/'+public_name
        images.append(a)
    for name in ['profile_image_manifest.json','layout_additional_assets.json','explorer_official_assets.json','explorer_league_emblems.json']:
        p=ROOT/'data'/name
        if p.exists():
            for a in json.loads(p.read_text(encoding='utf-8'))['assets']:add(a)
    crest=json.loads((ROOT/'data/layout_full_crest_manifest.json').read_text(encoding='utf-8'))
    images=[a for a in images if not (a['kind']=='club' and a['label']=='Liverpool')]
    add(dict(crest,kind='club',label='Liverpool',title='Liverpool crest',artist='Liverpool Football Club',source_page='https://resources.premierleague.com/premierleague/badges/t14.svg',license='Rights retained; private research only; no open redistribution permission verified'))
    p=ROOT/'data/explorer_club_assets.json'
    if p.exists():
        clubs=json.loads(p.read_text(encoding='utf-8'));by_id={a['id']:a for a in clubs['assets']}
        for row in clubs['coverage']:
            if row.get('asset_id') in by_id:add(by_id[row['asset_id']],row['team'])
        data['club_asset_coverage']=clubs['coverage']
    p=ROOT/'data/explorer_action_assets.json'
    if p.exists():
        photos=json.loads(p.read_text(encoding='utf-8'))
        for a in photos['assets']:add(dict(a,kind='action',label=a.get('player_name',a.get('label'))))
        data['action_photo_gaps']=photos.get('access_gap')
        data['action_photo_candidates']=photos.get('reviewed_candidates',[])
    secondary=ROOT/'data/explorer_secondary_crests.json'
    if secondary.exists():
        for a in json.loads(secondary.read_text(encoding='utf-8'))['assets']:add(a)
    data['images']=list({(a['kind'],a['label']):a for a in images}.values())
    catalog_path=ROOT/'data/explorer_crest_catalog.json'
    if catalog_path.exists():
        catalog=json.loads(catalog_path.read_text(encoding='utf-8'))
        existing={(a['kind'],a['label']) for a in images}
        for a in catalog['assets']:
            if ('club',a['label']) not in existing:add(a)
        data['images']=list({(a['kind'],a['label']):a for a in images}.values())
        clubs={r['team'] for r in data['records']}
        marks={a['label'] for a in data['images'] if a['kind']=='club'}
        data['missing_club_crests']=sorted(clubs-marks)
    history_path=folder/'profile_history.json'
    if history_path.exists():
        profile_history=json.loads(history_path.read_text(encoding='utf-8'))
        for name,expected in profile_history['source_hashes'].items():
            entry=next(f for f in manifest['files'] if f['filename']==name+'.csv.gz')
            if entry['sha256']!=expected:raise ValueError('Profile history fingerprint differs')
        data['profile_history']=profile_history
    branding_path=ROOT/'data/explorer_branding.json'
    if branding_path.exists():
        branding=json.loads(branding_path.read_text(encoding='utf-8'))
        for a in branding['assets']:add(a)
        data['images']=list({(a['kind'],a['label']):a for a in images}.values())
    used_assets={a['site_url'].split('/')[-1] for a in data['images']}
    for candidate in public_assets.iterdir():
        if candidate.is_file() and len(candidate.stem)==20 and all(ch in '0123456789abcdef' for ch in candidate.stem) and candidate.name not in used_assets:
            candidate.unlink()
    # Audit every observed club in every league-season, using the actual bundled
    # asset selection. The same crest illustrates each season; this does not
    # claim a historically exact badge edition.
    club_marks={a['label']:a for a in data['images'] if a['kind']=='club'}
    cells=sorted({(r['league'],r['season'],r['team']) for r in data['records']})
    crest_rows=[dict(league=l,season=s,team=t,available=t in club_marks,
                     sha256=club_marks.get(t,{}).get('sha256',''),
                     source=club_marks.get(t,{}).get('source_page','')) for l,s,t in cells]
    with (folder/'club_crest_coverage.csv').open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(crest_rows[0]));w.writeheader();w.writerows(crest_rows)
    data['missing_club_crests']=sorted({t for l,s,t in cells}-set(club_marks))
    review='<!doctype html><html><meta charset="utf-8"><title>FutWAR crest audit</title><style>body{font:16px Segoe UI;background:#eee8df;color:#383630}main{display:grid;grid-template-columns:repeat(8,1fr);gap:16px}figure{margin:0;background:#f8f3eb;padding:12px;text-align:center}img{width:80px;height:90px;object-fit:contain}figcaption{font-size:14px}</style><h1>Club crest audit</h1><p>Every club observed in the five leagues, 2017–18 through 2024–25. Illustrative crest editions.</p><main>'
    review+=''.join('<figure><img alt="'+html_tools.escape(t,quote=True)+'" src="'+a['data_url']+'"><figcaption>'+html_tools.escape(t)+'</figcaption></figure>' for t,a in sorted(club_marks.items()))
    (folder/'club_crest_review.html').write_text(review+'</main></html>',encoding='utf-8')
    print(f'Crest coverage: {len(club_marks)} clubs; {len(cells)} club-season cells; {len(data["missing_club_crests"])} missing')
    with (folder/'enrichment_coverage.csv').open(encoding='utf-8') as h:
        data['coverage']=[{k:(int(v) if k not in ('league','season') else v) for k,v in row.items()} for row in csv.DictReader(h)]
    # Preserve all 178 original fields, but don't repeat their long keys per row.
    data['sourceColumns']=list(data['records'][0]['source_stats'])
    data['sourceRows']=[]
    for i,r in enumerate(data['records']):
        data['sourceRows'].append([r['source_stats'][k] for k in data['sourceColumns']])
        del r['source_stats'];r['sourceIndex']=i
    packed=base64.b64encode(gzip.compress(json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'),compresslevel=6,mtime=0)).decode('ascii')
    html=(ROOT/'profile/explorer.html').read_text(encoding='utf-8')
    html=html.replace('__EXPLORER_DATA__',json.dumps(packed))
    css=(ROOT/'profile/explorer.css').read_text(encoding='utf-8')
    js=(ROOT/'profile/explorer.js').read_text(encoding='utf-8')
    core=(ROOT/'profile/explorer_core.js').read_text(encoding='utf-8')
    comparisons=(ROOT/'profile/value_comparisons.js').read_text(encoding='utf-8')
    html=html.replace('<script src="value_comparisons.js"></script>','<script>'+comparisons+'</script>')
    html=html.replace('<script src="explorer_core.js"></script>','<script>'+core+'</script>')
    html=html.replace('<link rel="stylesheet" href="explorer.css">','<style>'+css+'</style>')
    html=html.replace('<script src="explorer.js"></script>','<script>'+js+'</script>')
    target=folder/'FutWAR_Explorer.html';target.write_text(html,encoding='utf-8')
    (folder/'index.html').write_text(html,encoding='utf-8')
    # Publish the large player library as a separate gzip asset so the browser
    # can render the shell and initialize fast search before parsing full stats.
    site_data=dict(data)
    site_data['images']=[{k:v for k,v in a.items() if k!='data_url'} for a in data['images']]
    site=ROOT/'site';site.mkdir(parents=True,exist_ok=True)
    data_gzip=gzip.compress(json.dumps(site_data,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8'),compresslevel=6,mtime=0)
    (site/'futwar-data.json.gz').write_bytes(data_gzip)
    # A compact identity-group index makes searching available while the full
    # player metrics download and decompress in the background.
    def identity_text(value):
        value=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode('ascii').lower()
        return ' '.join(value.split())
    identity_ids=defaultdict(set)
    for r in data['records']:
        details=r.get('details') or {}
        key=identity_text(r['name'])+'|'+str(details.get('birth_year') or 'unknown:'+r['id'])
        identity_ids[key].add(str(r.get('provider_player_id') or ''))
    grouped=defaultdict(list)
    for r in data['records']:
        details=r.get('details') or {}
        key=identity_text(r['name'])+'|'+str(details.get('birth_year') or 'unknown:'+r['id'])
        ids=identity_ids[key]-{''}
        player_id=str(r.get('provider_player_id') or '') or (next(iter(ids)) if len(ids)==1 else '')
        group='provider:'+player_id if player_id else 'source:'+key
        grouped[group].append({k:r.get(k) for k in ('id','name','team','league','season','domain','position','display_role')})
    search_groups=[]
    for group,rows in grouped.items():
        rows.sort(key=lambda r:(r['season'],r['team']))
        search_groups.append({'id':group,'rows':rows})
    search_gzip=gzip.compress(json.dumps({'groups':search_groups},ensure_ascii=False,separators=(',',':')).encode('utf-8'),compresslevel=6,mtime=0)
    (site/'futwar-search.json.gz').write_bytes(search_gzip)
    site_html=(ROOT/'profile/explorer.html').read_text(encoding='utf-8').replace('__EXPLORER_DATA__','')
    fast_search=(ROOT/'profile/fast_search.js').read_text(encoding='utf-8')
    site_html=site_html.replace('<script src="value_comparisons.js"></script>','<script>'+comparisons+'</script>')
    site_html=site_html.replace('<script src="explorer_core.js"></script>','<script>'+core+'</script>')
    site_html=site_html.replace('<link rel="stylesheet" href="explorer.css">','<style>'+css+'</style>')
    site_html=site_html.replace('<script src="explorer.js"></script>','<script>'+fast_search+'</script><script>'+js+'</script>')
    (site/'index.html').write_text(site_html,encoding='utf-8')
    print(f'Built local explorer: {len(data["records"]):,} records; {len(data["images"])} locally archived images; {target.stat().st_size:,} bytes')
    print(f'Built public site: {site_html.__len__():,} HTML chars; {len(data_gzip):,} data bytes; {len(search_gzip):,} search-index bytes; {len(data["images"])} external image assets')

if __name__=='__main__':main()
