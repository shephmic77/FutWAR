"""Audit every source cell and build a private full-scope explorer derivative.

Player measurements remain from the original source; keeper measurements are
kept in a separate overlay. Profile/valuation links remain candidate identities.
"""
import bisect
import csv
import gzip
import hashlib
import json
import math
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAYER_SOURCE = ROOT / 'data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv'
KAGGLE = 'https://www.kaggle.com/datasets/emrey3lmaz/top-5-league-football-player-stats-2017-2025'
PUBLISHER = 'https://github.com/dcaribou/transfermarkt-datasets'
METRICS = {'goals_per90':'Performance_Gls','assists_per90':'Performance_Ast',
    'non_penalty_goals_per90':'Performance_G-PK','npxg_per90':'Expected_npxG',
    'xa_per90':'Expected_xA','xag_per90':'Expected_xAG',
    'progressive_passes_per90':'Progression_PrgP','progressive_carries_per90':'Progression_PrgC',
    'tackles_per90':'Tackles_Tkl','interceptions_per90':'Int_'}
TEXT = {'league','season','team','player','nation_','pos_'}
SIGNED = {'Expected_G-xG','Expected_np:G-xG','Expected_A-xAG','Team Success_+/-',
    'Team Success_+/-90','Team Success_On-Off','Team Success (xG)_On-Off',
    'Team Success (xG)_xG+/-','Team Success (xG)_xG+/-90'}
ROLES = {'Right Winger':'RW','Left Winger':'LW','Centre-Forward':'CF','Second Striker':'SS',
    'Attacking Midfield':'AM','Central Midfield':'CM','Defensive Midfield':'DM',
    'Left-Back':'LB','Right-Back':'RB','Centre-Back':'CB','Left Midfield':'LM','Right Midfield':'RM',
    'Goalkeeper':'GK'}

def read_csv(path, delimiter=','):
    with path.open(encoding='utf-8-sig', newline='') as h:
        return list(csv.DictReader(h, delimiter=delimiter))

def number(value):
    if value is None or str(value).strip() == '':
        return None
    result = float(str(value).strip().replace(',','.'))
    if not math.isfinite(result):
        raise ValueError('Non-finite source measurement')
    return result

def key(name):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',name.casefold()) if not unicodedata.combining(c)).split())

def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as h:
        writer=csv.DictWriter(h,fieldnames=fields or list(rows[0]))
        writer.writeheader();writer.writerows(rows)

def select_valuation(history, season):
    """Owner-approved June30 anchor. Never use a future or prior-season estimate."""
    year=int(season[:4]); start=f'{year}-07-01'; cutoff=f'{year+1}-06-30'
    dates=[r['date'] for r in history]
    ix=bisect.bisect_right(dates,cutoff)-1
    if ix<0 or dates[ix]<start:
        return None
    return dict(history[ix],cutoff=cutoff,policy='latest_recorded_estimate_in_season_on_or_before_June_30')

def main():
    output=ROOT/'reports/explorer';output.mkdir(parents=True,exist_ok=True)
    lineage=json.loads((ROOT/'data/processed/lineage.json').read_text(encoding='utf-8'))
    if hashlib.sha256(PLAYER_SOURCE.read_bytes()).hexdigest()!=lineage['output_sha256']:
        raise ValueError('Processed source hash differs from approved lineage')
    raw=ROOT/'data/raw'/lineage['source_file']
    if hashlib.sha256(raw.read_bytes()).hexdigest()!=lineage['source_sha256']:
        raise ValueError('Original raw source changed')
    source=read_csv(PLAYER_SOURCE,';')
    if len(source)!=22418 or len({(r['league'],r['season']) for r in source})!=40:
        raise ValueError('Unexpected project scope')
    source_fields=list(source[0]); seen=set(); issues=[]; cell_quality=defaultdict(Counter)
    numeric_rows=[]; counts=Counter()
    for ordinal,row in enumerate(source,1):
        identity=tuple(row[k] for k in ('league','season','team','player'))
        if identity in seen: raise ValueError('Duplicate player-club-season source key')
        seen.add(identity); parsed={}
        for field,value in row.items():
            cell=cell_quality[row['league'],row['season'],field]
            cell['records']+=1;cell['missing']+=not value.strip();counts['checked_source_cells']+=1
            if field in TEXT: continue
            try: parsed[field]=number(value)
            except ValueError:
                cell['invalid']+=1;issues.append(dict(record_id=f'original_player:{ordinal}',league=row['league'],season=row['season'],player=row['player'],field=field,issue='invalid_numeric',source_value=value));continue
            n=parsed[field]
            if n is not None and ((field.endswith('%') and not 0<=n<=100) or (n<0 and field not in SIGNED)):
                cell['range_review']+=1;issues.append(dict(record_id=f'original_player:{ordinal}',league=row['league'],season=row['season'],player=row['player'],field=field,issue='range_review',source_value=value))
        for total,parts in [('Performance_G+A',['Performance_Gls','Performance_Ast']),('Performance_Gls',['Performance_G-PK','Performance_PK']),('Tkl+Int_',['Tackles_Tkl','Int_'])]:
            vals=[parsed.get(f) for f in [total,*parts]]
            if all(v is not None for v in vals) and abs(vals[0]-sum(vals[1:]))>1e-8:
                issues.append(dict(record_id=f'original_player:{ordinal}',league=row['league'],season=row['season'],player=row['player'],field=total,issue='arithmetic_review',source_value=row[total]))
        if parsed.get('Playing Time_Starts') is not None and parsed.get('Playing Time_MP') is not None and parsed['Playing Time_Starts']>parsed['Playing Time_MP']:
            issues.append(dict(record_id=f'original_player:{ordinal}',league=row['league'],season=row['season'],player=row['player'],field='Playing Time_Starts',issue='starts_exceed_appearances',source_value=row['Playing Time_Starts']))
        numeric_rows.append(parsed)
    audit_fields=['record_id','league','season','player','field','issue','source_value']
    write_csv(output/'source_cell_issues.csv',issues,audit_fields)
    quality=[dict(league=l,season=s,field=f,records=c['records'],missing=c['missing'],invalid=c['invalid'],range_review=c['range_review'],missing_pct=round(100*c['missing']/c['records'],2)) for (l,s,f),c in sorted(cell_quality.items())]
    write_csv(output/'source_field_coverage.csv',quality)
    manifest=json.loads((ROOT/'data/player_identity_source_manifest.json').read_text(encoding='utf-8'))
    files={r['filename']:r for r in manifest['files']}
    def publisher_rows(name):
        item=files[name+'.csv.gz'];path=ROOT/item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Publisher snapshot changed: '+name)
        with gzip.open(path,'rt',encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))
    profiles={r['player_id']:r for r in publisher_rows('players')}
    candidates={int(r['output_record']):r for r in read_csv(ROOT/'reports/player_identity/identity_candidates.csv')}
    valuation_groups=defaultdict(lambda:defaultdict(set)); valuation_issues=[]
    for v in publisher_rows('player_valuations'):
        date=v['date'][:10]
        try:datetime.strptime(date,'%Y-%m-%d');value=number(v['market_value_in_eur'])
        except ValueError:
            valuation_issues.append(dict(player_id=v['player_id'],date=date,issue='invalid_valuation',value=v['market_value_in_eur']));continue
        if value is None or value<0:
            valuation_issues.append(dict(player_id=v['player_id'],date=date,issue='missing_or_negative_valuation',value=v['market_value_in_eur']));continue
        valuation_groups[v['player_id']][date].add(value)
    valuations={}
    for pid,groups in valuation_groups.items():
        history=[]
        for date,values in sorted(groups.items()):
            if len(values)>1:
                valuation_issues.append(dict(player_id=pid,date=date,issue='conflicting_same_date_values',value=json.dumps(sorted(values))));continue
            history.append(dict(date=date,eur=next(iter(values))))
        valuations[pid]=history
    write_csv(output/'valuation_issues.csv',valuation_issues,['player_id','date','issue','value'])
    transfers=defaultdict(list)
    for t in publisher_rows('transfers'):
        date=t['transfer_date'][:10]
        if '2017-07-01'<=date<='2025-06-30':
            transfers[t['player_id']].append(dict(date=date,from_club=t['from_club_name'],to_club=t['to_club_name'],reported_fee=t['transfer_fee'],source=PUBLISHER,provider_player_id=t['player_id']))
    teams=read_csv(ROOT/'data/processed/exploration/team_results.csv')
    team_lookup={(r['league'],r['season'],r['team']):{k:(number(v) if k not in ('league','season','team') else v) for k,v in r.items()} for r in teams}
    notes=json.loads((ROOT/'data/profile_context_notes.json').read_text(encoding='utf-8'))['records']
    annotations=json.loads((ROOT/'data/profile_display_annotations.json').read_text(encoding='utf-8'))['records']
    issue_lookup=defaultdict(list)
    for issue in issues:issue_lookup[issue['record_id']].append(issue['issue']+': '+issue['field'])
    exploration={int(r['output_record']):r for r in read_csv(ROOT/'data/processed/exploration/player_team_seasons.csv')}
    records=[]; enriched=[]; coverage=defaultdict(Counter)
    for ordinal,(row,nums) in enumerate(zip(source,numeric_rows),1):
        rid=f'original_player:{ordinal}'; candidate=candidates.get(ordinal)
        if candidate and tuple(candidate[k] for k in ('player_label','birth_year','league','season','team'))!=(row['player'],row['born_'],row['league'],row['season'],row['team']):raise ValueError('Cached identity candidate differs')
        pid=None; profile=None
        if candidate and candidate['status']=='unique_candidate_with_historical_appearance' and '|' not in candidate['candidate_provider_ids']:
            pid=candidate['candidate_provider_ids'];profile=profiles[pid]
            if key(profile['name'])!=key(row['player']) or profile['date_of_birth'][:4]!=row['born_']:raise ValueError('Profile identity check differs')
        if rid in notes:
            pid=notes[rid]['provider_player_id'];profile=profiles[pid]
            if profile['name']!=row['player'] or profile['date_of_birth'][:4]!=row['born_']:raise ValueError('Reviewed identity check differs')
        history=valuations.get(pid,[]); selected=select_valuation(history,row['season']); minutes=nums.get('Playing Time_Min')
        role=ROLES.get(profile['sub_position']) if profile else None
        if rid in annotations:role=annotations[rid]['position']
        metrics={k:90*nums[v]/minutes if minutes and nums.get(v) is not None else None for k,v in METRICS.items()}
        warnings=issue_lookup[rid]+json.loads(exploration[ordinal]['quality_flags'])
        if minutes is None or minutes<900:warnings.append('Low or unknown playing time; excluded from default 900-minute peer focus.')
        warnings.append('Specific historical main position unvalidated; displayed profile role is not season-minute evidence.')
        if profile:warnings.append('Cross-provider profile/valuation link is provisional: exact normalized name, birth year and historical club-season appearance candidate.')
        if selected is None:warnings.append('No same-season dated estimate on or before June 30; not filled with latest or peak value.')
        context=dict(notes.get(rid,{}))
        if profile:context.update(dict(provider_player_id=pid,height_cm=number(profile['height_in_cm']),foot=profile['foot'] or None,birth_date=profile['date_of_birth'][:10],profile_position=profile['sub_position'],profile_reference=profile['url'],identity_review='Unique exact-name/birth-year/historical-appearance candidate; not independently verified identity.',profile_snapshot_retrieved_at=files['players.csv.gz']['retrieved_at_utc']))
        r=dict(id=rid,name=row['player'],team=row['team'],league=row['league'],season=row['season'],domain='GK' if 'GK' in row['pos_'].split(',') else 'Outfield',position=row['pos_'] or None,main_position=None,display_role=role,provider_player_id=pid,minutes=minutes,details=dict(age=nums.get('age_'),nationality=row['nation_'],birth_year=row['born_'],appearances=nums.get('Playing Time_MP'),starts=nums.get('Playing Time_Starts'),goals=nums.get('Performance_Gls'),assists=nums.get('Performance_Ast')),metrics=metrics,totals={k:nums.get(v) for k,v in METRICS.items()},source_stats=row,profile_context=context or None,team_context=team_lookup.get((row['league'],row['season'],row['team'])),market_value=selected,valuation_history=[v for v in history if f"{row['season'][:4]}-07-01"<=v['date']<=f"{int(row['season'][:4])+1}-06-30"],transfers=[t for t in transfers.get(pid,[]) if f"{row['season'][:4]}-07-01"<=t['date']<=f"{int(row['season'][:4])+1}-06-30"],warnings=warnings,source_links=[KAGGLE]+([profile['url'],PUBLISHER] if profile else []),source='original_player_csv',keeper=None)
        records.append(r)
        cell=coverage[row['league'],row['season']];cell['records']+=1;cell['profile_linked']+=bool(profile);cell['market_value_available']+=selected is not None;cell['low_minute_records']+=minutes is None or minutes<900
        added=dict(futwar_record_id=rid,profile_provider_player_id=pid or '',profile_identity_status='candidate' if pid else 'unresolved',profile_position=role or '',height_cm=context.get('height_cm') or '',preferred_foot=context.get('foot') or '',market_value_eur=selected['eur'] if selected else '',market_value_date=selected['date'] if selected else '',market_value_cutoff=f'{int(row["season"][:4])+1}-06-30',market_value_source=PUBLISHER if selected else '',profile_source=context.get('profile_reference',''),source_player_sha256=lineage['output_sha256'],market_value_source_sha256=files['player_valuations.csv.gz']['sha256'],review_flags=json.dumps(warnings,ensure_ascii=False))
        enriched.append(dict(row,**added))
    # Keeper overlay is a separately attributed source, never a silent statistical overwrite.
    keeper_path=ROOT/'data/processed/keeper_archives/keeper_seasons_analysis.csv'
    kp_lineage=json.loads(keeper_path.with_name('psxg_correction_lineage.json').read_text(encoding='utf-8'))
    if hashlib.sha256(keeper_path.read_bytes()).hexdigest()!=kp_lineage['output_sha256']:raise ValueError('Keeper snapshot differs')
    aliases=json.loads((ROOT/'data/keeper_identity_aliases.json').read_text(encoding='utf-8'))['rules']
    index=defaultdict(list)
    for r in records:index[r['league'],r['season'],r['team'],key(r['name']),str(r['details']['birth_year'])].append(r)
    keeper_match_counts=Counter()
    for kr in read_csv(keeper_path):
        name=kr['player_name'];team=kr['team_name'];birth=str(int(number(kr['birth_year']))) if kr['birth_year'] else ''
        for rule in aliases:
            if kr['league']==rule['league'] and kr['season'] in rule['seasons'] and team==rule['team_from']:
                if rule.get('player_from')==name and str(rule.get('birth_year'))==birth:name=rule['player_to'];team=rule['team_to']
                elif name in rule.get('players',{}) and str(rule['players'][name])==birth:team=rule['team_to']
        matches=index[kr['league'],kr['season'],team,key(name),birth]
        if len(matches)!=1:keeper_match_counts['unresolved']+=1;continue
        r=matches[0];keeper_match_counts['linked_overlay']+=1
        km=number(kr['keeper_minutes']);flags=json.loads(kr['unresolved_quality_flags'])+json.loads(kr['exposure_correction_warnings'])+json.loads(kr['psxg_correction_warnings'])
        mappings={'saves_per90':'saves','psxg_per90':'psxg','reported_residual_per90':'reported_psxg_delta','shots_on_target_against_per90':'shots_on_target_against','pass_attempts_per90':'pass_attempts','crosses_faced_per90':'crosses_faced','sweeper_actions_per90':'sweeper_actions'}
        kvals={k:90*number(kr[v])/km if km and number(kr[v]) is not None else None for k,v in mappings.items()}
        if 'reported_psxg_residual_arithmetic_review' in flags:kvals['reported_residual_per90']=None
        faced=number(kr['crosses_faced']);stopped=number(kr['crosses_stopped'])
        kvals['crosses_stopped_share']=stopped/faced if faced and stopped is not None and 0<=stopped<=faced else None
        r['keeper']=dict(id=kr['keeper_record_id'],minutes=km,appearances=number(kr['appearances']),metrics=kvals,totals={k:number(kr[v]) for k,v in mappings.items()},crosses={'faced':faced,'stopped':stopped} if faced and stopped is not None and 0<=stopped<=faced else None,source=kr['source_variant'],flags=flags,source_links=[kr['basic_source_url'],kr['advanced_source_url']],identity_status='source-exact/reviewed-alias candidate overlay; cross-provider identity remains unverified',model_versions_confirmed=False)
        r['warnings']+=flags
    assert len(records)==len(source)
    for r, row in zip(records,enriched):
        keeper=r['keeper']
        row.update(keeper_overlay_id=keeper['id'] if keeper else '',
                   keeper_overlay_minutes=keeper['minutes'] if keeper else '',
                   keeper_overlay_metrics_json=json.dumps(keeper['metrics']) if keeper else '',
                   keeper_overlay_source_urls=json.dumps(keeper['source_links']) if keeper else '',
                   keeper_overlay_warnings=json.dumps(keeper['flags']) if keeper else '',
                   keeper_source_sha256=kp_lineage['output_sha256'] if keeper else '')
    for original,row in zip(source,enriched):
        assert all(original[k]==row[k] for k in source_fields), 'Original statistic changed'
    final_path=ROOT/'data/processed/futwar/player_seasons_enriched.csv'
    write_csv(final_path,enriched)
    context_rows=[dict(source_sha256=lineage['source_sha256'],output_record=i,
                       context_source_sha256=files['player_valuations.csv.gz']['sha256'],
                       payload=json.dumps({k:v for k,v in row.items() if k not in source_fields},ensure_ascii=False))
                  for i,row in enumerate(enriched,1)]
    write_csv(ROOT/'data/processed/postgres/player_season_context.csv',context_rows)
    write_csv(output/'enrichment_coverage.csv',[dict(league=l,season=s,**c) for (l,s),c in sorted(coverage.items())])
    summary=dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),source_records=len(source),source_columns=len(source_fields),checked_source_cells=counts['checked_source_cells'],league_season_cells=len(coverage),source_issues=len(issues),issue_counts=dict(Counter(i['issue'] for i in issues)),profile_linked=sum(c['profile_linked'] for c in coverage.values()),market_value_available=sum(c['market_value_available'] for c in coverage.values()),valuation_issues=len(valuation_issues),keeper_overlay=dict(keeper_match_counts),original_statistics_unchanged=True,independent_verification_of_all_statistics=False,market_value_policy='Owner-approved latest estimate within season on/before June30; actual date retained',source_player_sha256=lineage['output_sha256'],valuation_sha256=files['player_valuations.csv.gz']['sha256'],keeper_sha256=kp_lineage['output_sha256'],output_sha256=hashlib.sha256(final_path.read_bytes()).hexdigest(),limitations=['Structural/arithmetic/provenance checks do not independently establish every football fact.','No replacement/overall WAR formula finalized.','Missing injury, image or exact-position coverage is not fabricated.','Profile identities are candidate links; sensitivity analyses must not treat them as universally verified.'])
    (output/'audit_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    payload=dict(records=records,teams=list(team_lookup.values()),audit=summary,metric_sources=METRICS,valuation_source=files['player_valuations.csv.gz'],source_manifest=manifest,images=[],scope=['2017-18','2018-19','2019-20','2020-21','2021-22','2022-23','2023-24','2024-25'])
    (output/'data.json').write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
