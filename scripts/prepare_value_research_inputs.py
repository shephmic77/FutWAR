"""Expose auditable event features for a proposed VAEP-style pilot; no ratings."""
import csv,gzip,json,zipfile
from collections import Counter
from pathlib import Path
from audit_wyscout_research import verify,archive_rows,LEAGUES

ROOT=Path(__file__).resolve().parents[1]
FIELDS=['league','season','match_id','event_id','player_id','team_id','period','seconds',
        'event_type','subevent_type','start_x_pct','start_y_pct','end_x_pct','end_y_pct',
        'recorded_accurate','recorded_inaccurate','recorded_goal','tags_json']


def event_features(e,league):
    coords=e.get('positions',[]);first=coords[0] if coords else {};last=coords[-1] if len(coords)>1 else {}
    tags={t['id'] for t in e.get('tags',[])}
    return dict(zip(FIELDS,[league,'2017-18',e['matchId'],e['id'],e['playerId'],e['teamId'],
        e['matchPeriod'],e['eventSec'],e.get('eventName',''),e.get('subEventName',''),
        first.get('x'),first.get('y'),last.get('x'),last.get('y'),1801 in tags,1802 in tags,101 in tags,
        json.dumps(sorted(tags),separators=(',',':'))]))


def main():
    manifest=json.loads((ROOT/'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    hashes=verify(manifest)
    folder=ROOT/'data/processed/value_research';folder.mkdir(parents=True,exist_ok=True)
    output=ROOT/'reports/value_research';output.mkdir(parents=True,exist_ok=True)
    coverage=[];summary=[]
    with zipfile.ZipFile(ROOT/'data/raw/wyscout_research/2026-10-10/events.zip') as source:
        for country,(_,league) in LEAGUES.items():
            events=archive_rows(source,f'events_{country}.json');counts=Counter();missing=Counter()
            path=folder/f'{country}_2017-18_event_features.csv.gz'
            with path.open('wb') as binary,gzip.GzipFile(fileobj=binary,mode='wb',mtime=0) as zipped:
                import io
                with io.TextIOWrapper(zipped,encoding='utf-8',newline='') as h:
                    writer=csv.DictWriter(h,fieldnames=FIELDS);writer.writeheader()
                    for event in events:
                        row=event_features(event,league);writer.writerow(row);counts['records']+=1
                        counts['unattributed_player']+=row['player_id']==0
                        for f in FIELDS:missing[f]+=row[f] is None or row[f]==''
            for season in [f'{y}-{str(y+1)[-2:]}' for y in range(2017,2025)]:
                for f in FIELDS:
                    coverage.append(dict(league=league,season=season,field=f,records=len(events) if season=='2017-18' else 0,
                        missing_values=missing[f] if season=='2017-18' else None,
                        status='observed' if season=='2017-18' else 'not_in_release'))
            summary.append(dict(league=league,**counts));print(league,counts['records'],flush=True)
            del events
    with (output/'event_feature_coverage.csv').open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(coverage[0]));w.writeheader();w.writerows(coverage)
    lineage=dict(source_hashes=hashes,leagues=summary,formula_status='proposed, not fitted',
        tag_definitions='Wyscout release: 1801 accurate, 1802 inaccurate, 101 goal; retained source tags, no inferred xG/PSxG',
        limitations=['No verified specific seasonal roles','No cross-provider identity merge','No supplied calibrated xG/PSxG',
        'Only five 2017-18 cells; 35 absent','No inferred possession sequence, direction or keeper success','Player ID 0 retained'])
    (output/'event_input_lineage.json').write_text(json.dumps(lineage,indent=2),encoding='utf-8')


if __name__=='__main__':main()
