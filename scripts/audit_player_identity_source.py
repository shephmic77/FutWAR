"""Audit publisher IDs and historical exposure; propose identities without merging."""
import csv
import gzip
import hashlib
import json
import unicodedata
from collections import Counter,defaultdict
from pathlib import Path
import io
from export_initial_eda import psql
from audit_standings_and_identity import write_csv

ROOT=Path('data/raw/transfermarkt_publisher/2026-10-10')
CODES={'GB1':'Premier League','ES1':'La Liga','IT1':'Serie A','L1':'Bundesliga','FR1':'Ligue 1'}


def read_rows(name):
    with gzip.open(ROOT/(name+'.csv.gz'),'rt',encoding='utf-8-sig',newline='') as handle:
        for row in csv.DictReader(handle):
            if None in row or any(v is None for v in row.values()):raise ValueError('Malformed CSV row in '+name)
            yield row


def name_key(name):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',name.casefold())
        if not unicodedata.combining(c)).split())


def identity_candidates(row,index,memberships,club_ids):
    # Only exact normalized full name + known birth year, then historical club-season evidence.
    if not row['born_']:
        return [],'missing_birth_year'
    candidates=index.get((name_key(row['player']),row['born_']),[])
    club=club_ids.get((row['league'],row['team']))
    if club is None:
        return candidates,'club_mapping_unresolved'
    supported=[p for p in candidates if (p['player_id'],club,row['league'],row['season']) in memberships]
    status='unique_candidate_with_historical_appearance' if len(supported)==1 else (
        'ambiguous_candidates' if len(supported)>1 else 'no_supported_exact_name_candidate')
    return supported,status


def main():
    manifest=json.loads(Path('data/player_identity_source_manifest.json').read_text(encoding='utf-8'))
    for source in manifest['files']:
        p=Path(source['path'])
        if hashlib.sha256(p.read_bytes()).hexdigest()!=source['sha256']:
            raise ValueError('Source fingerprint changed: '+str(p))
    players_list=list(read_rows('players'))
    players={r['player_id']:r for r in players_list}
    if len(players)!=len(players_list):raise ValueError('Duplicate provider player IDs')
    if '' in players:raise ValueError('Missing provider player ID')
    clubs_list=list(read_rows('clubs'))
    clubs={r['club_id']:r for r in clubs_list}
    if len(clubs)!=len(clubs_list):raise ValueError('Duplicate provider club IDs')
    games={}
    scoped_games={}
    coverage={(league,f'{year}-{str(year+1)[-2:]}'):dict(league=league,season=f'{year}-{str(year+1)[-2:]}',
        games=0,scored_games=0,games_with_appearances=0,appearance_records=0,
        missing_minutes=0,missing_goals=0,missing_assists=0,missing_yellow_cards=0,missing_red_cards=0,
        missing_player_profile=0,missing_birth_date=0,invalid_minutes=0)
        for league in CODES.values() for year in range(2017,2025)}
    club_memberships=defaultdict(set)
    for g in read_rows('games'):
        if g['game_id'] in games:raise ValueError('Duplicate provider game ID')
        games[g['game_id']]=True
        if g['competition_id'] not in CODES or g['season'] not in {str(y) for y in range(2017,2025)}:continue
        league=CODES[g['competition_id']];season=f'{g["season"]}-{str(int(g["season"])+1)[-2:]}'
        scoped_games[g['game_id']]=(league,season,g)
        cell=coverage[league,season];cell['games']+=1
        cell['scored_games']+=bool(g['home_club_goals'] and g['away_club_goals'])
        club_memberships[league,g['home_club_id']].add(season)
        club_memberships[league,g['away_club_id']].add(season)
    aliases=json.loads(Path('data/wikipedia_club_aliases.json').read_text(encoding='utf-8'))
    extra_path=Path('data/identity_club_aliases.json')
    if extra_path.exists():
        for league,m in json.loads(extra_path.read_text(encoding='utf-8')).items():aliases.setdefault(league,{}).update(m)
    baseline=list(csv.DictReader(Path('reports/standings_identity/standings_coverage.csv').open(encoding='utf-8')))
    contexts={(r['league'],r['season'],r['team']) for r in baseline}
    club_ids={};unmatched=[]
    for (league,cid),seasons in club_memberships.items():
        if cid not in clubs:raise ValueError('Missing club profile')
        label=clubs[cid]['name'];team=aliases.get(league,{}).get(label,label)
        if all((league,s,team) in contexts for s in seasons):
            if (league,team) in club_ids and club_ids[league,team]!=cid:raise ValueError('Club map collision')
            club_ids[league,team]=cid
        else:unmatched.append(dict(league=league,provider_club_id=cid,source_name=label,proposed_name=team))
    fixture_rows=list(csv.DictReader(io.StringIO(psql('--csv','-c',
        'SELECT league,season,match_date,home_team,away_team,home_goals,away_goals FROM futwar.normalized_match_results;'))))
    fixture_lookup={(r['league'],r['season'],r['match_date'],r['home_team'],r['away_team']):r for r in fixture_rows}
    pair_lookup=defaultdict(list)
    for r in fixture_rows:pair_lookup[r['league'],r['season'],r['home_team'],r['away_team']].append(r)
    reverse_clubs={(league,cid):team for (league,team),cid in club_ids.items()}
    fixture_issues=[];matched_fixture_keys=set();matched_club_pair_keys=set()
    for gid,(league,season,g) in scoped_games.items():
        home=reverse_clubs.get((league,g['home_club_id']));away=reverse_clubs.get((league,g['away_club_id']))
        key=(league,season,g['date'][:10],home,away)
        base=fixture_lookup.get(key)
        if base:matched_fixture_keys.add(key)
        issue=''
        pair=(league,season,home,away)
        if base is None and len(pair_lookup[pair])==1:
            base=pair_lookup[pair][0];issue='date_discrepancy_same_unique_club_pair'
        if base:matched_club_pair_keys.add(pair)
        if base is None:issue='unmatched_fixture_key'
        elif (g['home_club_goals'],g['away_club_goals'])!=(base['home_goals'],base['away_goals']):
            issue='score_definition_or_source_discrepancy'
        if issue:
            fixture_issues.append(dict(game_id=gid,league=league,season=season,match_date=g['date'],
                home_team=home,away_team=away,provider_home_goals=g['home_club_goals'],provider_away_goals=g['away_club_goals'],
                baseline_home_goals=base['home_goals'] if base else '',baseline_away_goals=base['away_goals'] if base else '',
                baseline_match_date=base['match_date'] if base else '',issue=issue))
    memberships=set();appearance_seen=set();appearance_games=set();exposure=Counter();orphan_games=0
    for a in read_rows('appearances'):
        if a['game_id'] not in scoped_games:
            orphan_games+=a['game_id'] not in games
            continue
        if a['appearance_id'] in appearance_seen:raise ValueError('Duplicate scoped appearance ID')
        appearance_seen.add(a['appearance_id']);appearance_games.add(a['game_id'])
        league,season,g=scoped_games[a['game_id']];cell=coverage[league,season]
        if a['competition_id']!=g['competition_id'] or a['player_club_id'] not in (g['home_club_id'],g['away_club_id']):
            raise ValueError('Appearance competition or historical club contradicts game')
        cell['appearance_records']+=1
        for metric in ['minutes','goals','assists','yellow_cards','red_cards']:
            field='minutes_played' if metric=='minutes' else metric
            cell['missing_'+metric]+=not a[field]
        cell['missing_player_profile']+=a['player_id'] not in players
        p=players.get(a['player_id'],{})
        cell['missing_birth_date']+=not p.get('date_of_birth')
        memberships.add((a['player_id'],a['player_club_id'],league,season))
        if a['minutes_played']:
            minutes=int(a['minutes_played']);cell['invalid_minutes']+=minutes<0 or minutes>120
            exposure[a['player_id'],a['player_club_id'],league,season]+=minutes
    for gid in appearance_games:
        league,season,_=scoped_games[gid];coverage[league,season]['games_with_appearances']+=1
    index=defaultdict(list)
    for p in players_list:
        if p['date_of_birth']:index[name_key(p['name']),p['date_of_birth'][:4]].append(p)
    path=Path('data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv')
    with path.open(encoding='utf-8-sig',newline='') as f:local=list(csv.DictReader(f,delimiter=';'))
    proposed=[]
    for ordinal,r in enumerate(local,start=1):
        options,status=identity_candidates(r,index,memberships,club_ids)
        proposed.append(dict(output_record=ordinal,player_label=r['player'],birth_year=r['born_'],
            league=r['league'],season=r['season'],team=r['team'],status=status,
            candidate_provider_ids='|'.join(p['player_id'] for p in options),
            verified_player_id='',original_minutes=r['Playing Time_Min'],
            candidate_minutes=exposure[options[0]['player_id'],club_ids[r['league'],r['team']],r['league'],r['season']]
                if len(options)==1 and status=='unique_candidate_with_historical_appearance' else ''))
    transfers=Counter();sample_transfers=[];future_transfer_dates=0;transfer_total=0;transfer_players=set();transfer_player_seasons=set()
    for t in read_rows('transfers'):
        transfer_total+=1;future_transfer_dates+=t['transfer_date'][:10]>'2026-10-10'
        if t['transfer_date'][:10]>'2026-10-10':continue
        transfer_players.add(t['player_id'])
        season=t['transfer_season'];year='20'+season[:2] if len(season)==5 else None
        if year and 2017<=int(year)<=2024:
            full=f'{year}-{season[-2:]}'
            transfer_player_seasons.add((t['player_id'],full))
            for league,cid in club_memberships:
                if cid in (t['from_club_id'],t['to_club_id']) and full in club_memberships[league,cid]:
                    transfers[league,full]+=1
            if t['player_name'] in {'Aaron Lennon','Abdukodir Khusanov','Abde Ezzalzouli'}:
                sample_transfers.append(t)
    for key,cell in coverage.items():
        cell['transfer_records_touching_scoped_clubs']=transfers[key]
    # Result-derived baseline count is an external structural benchmark, not an appearance completeness claim.
    expected=Counter();expected_played=Counter()
    for r in csv.DictReader(Path('data/processed/postgres/historical_standings.csv').open(encoding='utf-8')):
        expected[r['league'],r['season']]+=1
        expected_played[r['league'],r['season']]+=int(r['played'])
    for key,cell in coverage.items():
        cell['expected_clubs']=expected[key]
        cell['expected_scored_games']=expected_played[key]//2
        cell['game_count_difference']=cell['scored_games']-cell['expected_scored_games']
    out=Path('reports/player_identity');out.mkdir(parents=True,exist_ok=True)
    multiclub=defaultdict(set)
    for pid,cid,league,season in memberships:multiclub[pid,season].add((league,cid))
    transfer_gaps=[dict(provider_player_id=pid,season=season,club_contexts=json.dumps(sorted(ctx)),
        status='no_published_transfer_in_declared_season',
        has_any_published_transfer=pid in transfer_players)
        for (pid,season),ctx in sorted(multiclub.items()) if len(ctx)>1 and (pid,season) not in transfer_player_seasons]
    write_csv(out/'transfer_coverage_gaps.csv',transfer_gaps,
        ['provider_player_id','season','club_contexts','status','has_any_published_transfer'])
    write_csv(out/'fixture_discrepancies.csv',fixture_issues,
        ['game_id','league','season','match_date','home_team','away_team','provider_home_goals','provider_away_goals',
         'baseline_home_goals','baseline_away_goals','baseline_match_date','issue'])
    write_csv(out/'coverage.csv',list(coverage.values()))
    write_csv(out/'club_mapping_queue.csv',unmatched,['league','provider_club_id','source_name','proposed_name'])
    write_csv(out/'identity_candidates.csv',proposed)
    write_csv(out/'sample_transfers.csv',sample_transfers,list(sample_transfers[0]) if sample_transfers else
        ['player_id','transfer_date','transfer_season','from_club_id','to_club_id'])
    summary=dict(provider_players=len(players),provider_clubs=len(clubs),provider_games=len(games),
        scoped_games=len(scoped_games),scoped_appearances=len(appearance_seen),
        scoped_games_without_appearances=len(scoped_games)-len(appearance_games),
        all_source_appearances_with_unknown_game=orphan_games,club_aliases_needed=len(unmatched),
        local_records=len(local),candidate_status_counts=dict(Counter(r['status'] for r in proposed)),
        transfer_records=transfer_total,transfer_dates_after_retrieval=future_transfer_dates,
        scoped_multiple_club_player_seasons_without_transfer_record=len(transfer_gaps),
        verified_player_ids_assigned=0,processed_player_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        matched_fixture_keys=len(matched_fixture_keys),fixture_discrepancies=len(fixture_issues),
        matched_unique_club_pair_keys=len(matched_club_pair_keys),
        fixture_issue_counts=dict(Counter(r['issue'] for r in fixture_issues)),
        limitation='Unique candidates are not verified identities; current-club fields are never used for historical membership.')
    (out/'run.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2));print(json.dumps(unmatched,ensure_ascii=True))


if __name__=='__main__':main()
