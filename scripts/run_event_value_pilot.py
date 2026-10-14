"""Chronological goal-danger diagnostic, not SPADL, VAEP ratings or FutWAR.

Preserves source event order for equal timestamps. Labels use ten subsequent raw
events in the same period. Save-attempt goal tags are never additional goals.
No player ratings, fabricated positions or budget estimates are generated.
"""
import csv, hashlib, json, os, zipfile
from collections import Counter, defaultdict
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','4')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss, average_precision_score
from audit_wyscout_research import archive_rows, verify, LEAGUES

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/event_value_pilot'
FEATURES=['event_type','subevent_type','start_x','start_y','end_x','end_y',
          'accurate','inaccurate','seconds','period','previous_type','previous_same_team',
          'seconds_since_previous','second_previous_type','second_previous_same_team']


def scoring_team(event,teams):
    tags={t['id'] for t in event.get('tags',[])}
    team=event['teamId']
    if team not in teams:raise ValueError('Event team outside fixture')
    if event.get('eventName')=='Save attempt':return None
    if 102 in tags:return next(t for t in teams if t!=team)
    return team if 101 in tags else None


def horizon_labels(events,teams,horizon=10):
    """Strictly after current event; complete same-period horizon required."""
    goals=[scoring_team(e,teams) for e in events]
    labels=[]
    for i,event in enumerate(events):
        future=events[i+1:i+1+horizon]
        if len(future)!=horizon or any(e['matchPeriod']!=event['matchPeriod'] for e in future):
            labels.append(None);continue
        following=goals[i+1:i+1+horizon]
        labels.append((int(event['teamId'] in following),int(any(t is not None and t!=event['teamId'] for t in following))))
    return labels


def event_vector(events,i):
    event=events[i];positions=event.get('positions',[]);tags={t['id'] for t in event.get('tags',[])}
    first=positions[0] if positions else {};last=positions[-1] if len(positions)>1 else {}
    def coordinate(point,key):
        value=point.get(key)
        # Preserve the raw archive. Out-of-pitch values are missing only in this
        # derived feature matrix; do not clip them into plausible locations.
        x,y=point.get('x'),point.get('y')
        if x is not None and y is not None and (not 0<=x<=100 or not 0<=y<=100):
            return np.nan
        return value if value is not None and 0<=value<=100 else np.nan
    past=[]
    for lag in [1,2]:
        prior=events[i-lag] if i>=lag and events[i-lag]['matchPeriod']==event['matchPeriod'] else None
        past.append(prior)
    previous,second=past
    values=[event['eventId'],event['subEventId'],coordinate(first,'x'),coordinate(first,'y'),
            coordinate(last,'x'),coordinate(last,'y'),int(1801 in tags),int(1802 in tags),
            event['eventSec'],1 if event['matchPeriod']=='1H' else 2,
            previous['eventId'] if previous else np.nan,
            int(previous['teamId']==event['teamId']) if previous else np.nan,
            event['eventSec']-previous['eventSec'] if previous else np.nan,
            second['eventId'] if second else np.nan,
            int(second['teamId']==event['teamId']) if second else np.nan]
    return [float(v) if v not in ('',None) else np.nan for v in values]


def split_for(date):
    return 'train' if date<'2018-01-01' else 'validation' if date<'2018-03-01' else 'test'


def write_csv(path,rows):
    with path.open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'data/wyscout_research_manifest.json').read_text(encoding='utf-8'))
    hashes=verify(manifest)
    blocks=[];audits=[];coverage=[];invalid_position_points=0
    with zipfile.ZipFile(ROOT/'data/raw/wyscout_research/2026-10-10/events.zip') as ez,zipfile.ZipFile(ROOT/'data/raw/wyscout_research/2026-10-10/matches.zip') as mz:
        for country,(_,league) in LEAGUES.items():
            matches={m['wyId']:m for m in archive_rows(mz,f'matches_{country}.json')}
            by_match=defaultdict(list)
            for event in archive_rows(ez,f'events_{country}.json'):by_match[event['matchId']].append(event)
            vectors=[];meta=[]
            for mid,match in sorted(matches.items(),key=lambda item:(item[1]['dateutc'],item[0])):
                teams=tuple(int(t) for t in match['teamsData'])
                events=by_match.get(mid,[])
                events=sorted(enumerate(events),key=lambda item:({'1H':1,'2H':2}.get(item[1]['matchPeriod'],99),item[1]['eventSec'],item[0]))
                events=[e for _,e in events]
                reasons=[];counts=Counter()
                for e in events:
                    for point in e.get('positions',[]):
                        x,y=point.get('x'),point.get('y')
                        if x is not None and y is not None and (not 0<=x<=100 or not 0<=y<=100):
                            invalid_position_points+=1
                    try:
                        goal=scoring_team(e,teams)
                        if goal:counts[goal]+=1
                    except ValueError:reasons.append('unknown_event_team')
                expected={int(t):int(v['score']) for t,v in match['teamsData'].items()}
                if any(counts[t]!=expected[t] for t in teams):reasons.append('goal_score_mismatch')
                if not events:reasons.append('no_events')
                if any(e['matchPeriod'] not in ('1H','2H') or e['eventSec']<0 for e in events):reasons.append('period_or_time_invalid')
                audits.append(dict(league=league,match_id=mid,date=match['dateutc'][:10],source_score=json.dumps(expected),reconstructed_score=json.dumps({t:counts[t] for t in teams}),events=len(events),status='excluded' if reasons else 'included',reasons=';'.join(sorted(set(reasons)))))
                if reasons:continue
                labels=horizon_labels(events,teams)
                # This is a sampled prediction diagnostic, not a season valuation.
                for i in range(0,len(events),3):
                    if labels[i] is None:continue
                    vector=event_vector(events,i)
                    vectors.append(vector);meta.append([league,mid,split_for(match['dateutc'][:10]),*labels[i]])
            frame=pd.DataFrame(np.asarray(vectors,dtype=np.float32),columns=FEATURES)
            for j,key in enumerate(['league','match_id','split','score_label','concede_label']):frame[key]=[m[j] for m in meta]
            blocks.append(frame)
            for split in ['train','validation','test']:
                sub=frame[frame.split==split]
                coverage.append(dict(league=league,split=split,states=len(sub),fixtures=sub.match_id.nunique(),scoring_prevalence=float(sub.score_label.mean()),conceding_prevalence=float(sub.concede_label.mean())))
            print(league,len(frame),'diagnostic states',flush=True)
            del by_match,vectors,meta
    write_csv(OUT/'match_goal_reconciliation.csv',audits);write_csv(OUT/'split_coverage.csv',coverage)
    states=pd.concat(blocks,ignore_index=True);del blocks
    states.to_pickle(ROOT/'data/processed/value_research/event_pilot_states.pkl.gz',compression='gzip')
    train=states[states.split=='train'];test=states[states.split=='test'];validation=states[states.split=='validation']
    # Deterministic uniform training subsample; no outcome-based balancing.
    train=train.sample(n=min(160000,len(train)),random_state=42).sort_index()
    metrics=[];calibration=[];prediction_rows=[]
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for target,ax in zip(['score','concede'],axes):
        y=target+'_label';base=float(train[y].mean())
        for model_name,columns in [('location_context',['start_x','start_y','end_x','end_y','seconds','period']),('event_history',FEATURES)]:
            categorical=[c for c in columns if c.endswith('_type') or c=='period']
            model=HistGradientBoostingClassifier(max_iter=60,max_leaf_nodes=15,l2_regularization=1,early_stopping=False,random_state=42,categorical_features=categorical)
            model.fit(train[columns],train[y])
            for split,frame in [('validation',validation),('test',test)]:
                pred=model.predict_proba(frame[columns])[:,1];truth=frame[y].to_numpy()
                for league in [None,*LEAGUES.values()]:
                    label='All five' if league is None else league[1]
                    mask=np.ones(len(frame),dtype=bool) if league is None else frame.league.to_numpy()==label
                    yy=truth[mask];pp=pred[mask]
                    metrics.append(dict(target=target,model=model_name,split=split,league=label,states=len(yy),brier=float(brier_score_loss(yy,pp)),log_loss=float(log_loss(yy,pp,labels=[0,1])),average_precision=float(average_precision_score(yy,pp)),constant_brier=float(brier_score_loss(yy,np.full(len(yy),base))),constant_log_loss=float(log_loss(yy,np.full(len(yy),base),labels=[0,1]))))
                if split=='test':
                    edges=np.unique(np.quantile(pred,np.linspace(0,1,11)))
                    bins=np.clip(np.searchsorted(edges,pred,side='right')-1,0,len(edges)-2)
                    rows=[]
                    for b in sorted(set(bins)):
                        mask=bins==b
                        item=dict(target=target,model=model_name,bin=int(b),states=int(mask.sum()),mean_prediction=float(pred[mask].mean()),observed_rate=float(truth[mask].mean()))
                        rows.append(item);calibration.append(item)
                    ax.plot([r['mean_prediction'] for r in rows],[r['observed_rate'] for r in rows],marker='o',label=model_name.replace('_',' '))
                    if model_name=='event_history':
                        # Aggregate by fixture, retaining grouped held-out diagnostics.
                        temp=pd.DataFrame({'league':frame.league,'match_id':frame.match_id,'prediction':pred,'observed':truth})
                        for (league,mid),g in temp.groupby(['league','match_id']):prediction_rows.append(dict(target=target,league=league,match_id=int(mid),states=len(g),prediction_mean=float(g.prediction.mean()),observed_rate=float(g.observed.mean())))
        ax.plot([0,.25],[0,.25],ls='--',c='gray',label='perfect calibration')
        ax.set(title=f'{target.title()} in next 10 raw events',xlabel='Mean predicted probability',ylabel='Observed proportion');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Held-out March–May 2018 matches · goal-danger diagnostic, not player WAR')
    fig.tight_layout();fig.savefig(OUT/'heldout_calibration.png',dpi=160);plt.close(fig)
    write_csv(OUT/'prediction_metrics.csv',metrics);write_csv(OUT/'calibration_bins.csv',calibration);write_csv(OUT/'heldout_fixture_predictions.csv',prediction_rows)
    run=dict(source_hashes=hashes,states=len(states),included_fixtures=sum(a['status']=='included' for a in audits),excluded_fixtures=[a for a in audits if a['status']=='excluded'],features=FEATURES,training_rows=len(train),sampling='every third raw event; complete ten-event same-period future horizon',chronology={'train':'before 2018-01-01','validation':'2018-01-01 through 2018-02-28','test':'2018-03-01 onward'},model='HistGradientBoostingClassifier; 60 iterations; 15 leaves; fixed diagnostic settings, not tuned on test',invalid_coordinate_points=invalid_position_points,coordinate_policy='Out-of-pitch coordinate pairs are counted and set missing in derived model features; raw source values are unchanged and never clipped.',limitations=['Not SPADL or a complete VAEP implementation','No player value or WAR computed','Raw event horizon differs from action horizon','Coordinates kept in provider frame; action transformation remains unvalidated','No keeper/outfield common value calibration','No fitted league-strength translation','No historical budget or specific-position replacement estimates','Validation is later matches within one season, not future-season validation'])
    (OUT/'run.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
    print('Finished',run['included_fixtures'],'fixtures;',len(run['excluded_fixtures']),'excluded;',len(states),'states',flush=True)


if __name__=='__main__':main()
