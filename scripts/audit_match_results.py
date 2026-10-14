"""Audit pinned match results and compare source club labels without silent merging."""
import csv
import hashlib
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from collections import defaultdict
from pathlib import Path

if __package__:
    from .acquire_openfootball import COMMIT, SEASONS, CODES
    from .audit_data import write_csv
else:
    from acquire_openfootball import COMMIT, SEASONS, CODES
    from audit_data import write_csv


def inspect_matches(matches):
    fixtures, completed, teams, issues = [], [], set(), []
    for number, row in enumerate(matches, start=1):
        home, away = row.get('team1'), row.get('team2')
        if not isinstance(home,str) or not isinstance(away,str) or home == away:
            issues.append(('invalid_teams',number))
            continue
        teams.update([home,away])
        fixtures.append((home,away))
        try:
            date.fromisoformat(row.get('date',''))
        except (TypeError,ValueError):
            issues.append(('invalid_or_missing_date',number))
        score = (row.get('score') or {}).get('ft')
        if score is None:
            issues.append(('no_fulltime_score',number))
            continue
        if not isinstance(score,list) or len(score)!=2 or any(type(v) is not int or v<0 for v in score):
            issues.append(('invalid_fulltime_score',number))
            continue
        completed.append(row)
    duplicates = sum(n-1 for n in Counter(fixtures).values() if n>1)
    return completed, teams, issues, duplicates


def run():
    root=Path('data/raw/openfootball')/COMMIT
    manifest=json.loads(Path('data/openfootball_manifest.json').read_text(encoding='utf-8'))
    output=Path('reports/match_audit');output.mkdir(parents=True,exist_ok=True)
    player_path=Path('data/processed/player_seasons/Top5_League_Players_2017to2024_dataset.csv')
    with player_path.open(encoding='utf-8',newline='') as handle:
        players=list(csv.DictReader(handle,delimiter=';'))
    aliases_path=Path('data/club_aliases.json')
    aliases=json.loads(aliases_path.read_text(encoding='utf-8-sig')) if aliases_path.exists() else {}
    summaries, issues_report, club_comparisons, normalized = [], [], [], []
    for season in SEASONS:
        for code,league in CODES.items():
            relative=f'{season}/{code}.json';path=root/relative
            if not path.exists():
                summaries.append({'league':league,'season':season,'status':'missing_file'})
                continue
            if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['file_sha256'][relative]:
                raise ValueError(f'Changed raw match input: {relative}')
            data=json.loads(path.read_text(encoding='utf-8-sig'))
            matches=data['matches']
            completed,teams,issues,duplicates=inspect_matches(matches)
            appearance_counts=Counter()
            for r in completed:
                appearance_counts.update([r['team1'],r['team2']])
                normalized.append({'league':league,'season':season,'match_date':r.get('date',''),
                    'home_label':r['team1'],'away_label':r['team2'],'home_goals':r['score']['ft'][0],
                    'away_goals':r['score']['ft'][1],'source_file':relative,
                    'source_sha256':manifest['file_sha256'][relative]})
            player_teams={r['team'] for r in players if r['league']==league and r['season']==season}
            mapped={aliases.get(league,{}).get(t,t) for t in teams}
            if len(mapped)!=len(teams):
                raise ValueError(f'Club aliases are not one-to-one: {league}/{season}')
            for label in sorted(teams):
                canonical=aliases.get(league,{}).get(label,label)
                club_comparisons.append({'league':league,'season':season,'match_label':label,
                    'player_label':canonical if canonical in player_teams else '',
                    'status':'explicit_alias_match' if label in aliases.get(league,{}) and canonical in player_teams else 'exact_label_match' if label in player_teams else 'unresolved',
                    'matches_played':appearance_counts[label]})
            for t in sorted(player_teams-mapped):
                club_comparisons.append({'league':league,'season':season,'match_label':'',
                                        'player_label':t,'status':'player_label_unmatched','matches_played':''})
            summaries.append({'league':league,'season':season,'fixture_rows':len(matches),
                'completed_results':len(completed),'team_labels':len(teams),
                'double_round_robin_benchmark':len(teams)*(len(teams)-1),
                'difference_from_benchmark':len(completed)-len(teams)*(len(teams)-1),
                'minimum_club_matches':min(appearance_counts.values()) if appearance_counts else 0,
                'maximum_club_matches':max(appearance_counts.values()) if appearance_counts else 0,
                'duplicate_directed_pair_rows':duplicates,'quality_issue_count':len(issues),
                'unmatched_match_labels':len(mapped-player_teams),'unmatched_player_labels':len(player_teams-mapped),
                'status':'audited_not_certified_complete'})
            issues_report.extend({'league':league,'season':season,'issue':issue,'source_record':record} for issue,record in issues)
    fields=['league','season','fixture_rows','completed_results','team_labels','double_round_robin_benchmark',
            'difference_from_benchmark','minimum_club_matches','maximum_club_matches','duplicate_directed_pair_rows',
            'quality_issue_count','unmatched_match_labels','unmatched_player_labels','status']
    write_csv(output/'league_season_coverage.csv',fields,summaries)
    write_csv(output/'issues.csv',['league','season','issue','source_record'],issues_report)
    write_csv(output/'club_comparison.csv',['league','season','match_label','player_label','status','matches_played'],club_comparisons)
    dest=Path('data/processed/match_results');dest.mkdir(parents=True,exist_ok=True)
    write_csv(dest/'openfootball_results.csv',['league','season','match_date','home_label','away_label','home_goals','away_goals','source_file','source_sha256'],normalized)
    # Compare aggregate exposure using reviewed labels; never adjust player values.
    player_groups = defaultdict(list)
    for r in players:
        player_groups[(r['league'],r['season'],r['team'])].append(r)
    exposure = []
    for r in club_comparisons:
        if not r['match_label'] or not r['player_label']:
            continue
        subset = player_groups[(r['league'],r['season'],r['player_label'])]
        games = int(r['matches_played'])
        starts = sum(Decimal(p['Playing Time_Starts']) for p in subset)
        minutes = sum(Decimal(p['Playing Time_Min']) for p in subset)
        exposure.append({'league':r['league'],'season':r['season'],'team':r['player_label'],
            'completed_match_results':games,'player_start_total':str(starts),
            'eleven_starters_benchmark':11*games,'starts_difference':str(starts-11*games),
            'player_minutes_total':str(minutes),'eleven_players_90_minutes_benchmark':games*11*90,
            'minutes_difference_pct':str(round(100*(minutes/(games*11*90)-1),4)) if games else ''})
    write_csv(output/'team_exposure_comparison.csv', list(exposure[0]), exposure)
    # Prepare traceable SQL audit imports from the same pinned raw-file evidence.
    source_rows = []
    for season in SEASONS:
        for code, league in CODES.items():
            relative = f'{season}/{code}.json'
            if relative not in manifest['file_sha256']:
                continue
            source_rows.append({'source_sha256':manifest['file_sha256'][relative],
                'filename':relative,
                'source_url':f'https://raw.githubusercontent.com/openfootball/football.json/{COMMIT}/{relative}',
                'metadata':json.dumps({'provider':'OpenFootball','license':'CC0-1.0',
                    'commit':COMMIT,'retrieved_at_utc':manifest['acquisition']['retrieved_at_utc'],
                    'league':league,'season':season,'granularity':'domestic match results',
                    'completeness':'audited_not_certified_complete'})})
    write_csv(dest/'source_files.csv',['source_sha256','filename','source_url','metadata'],source_rows)
    alias_rows = {(r['league'],r['match_label'],r['player_label']) for r in club_comparisons
                  if r['match_label'] and r['player_label']}
    write_csv(dest/'club_labels.csv',['league','match_label','player_label'],
              [dict(zip(['league','match_label','player_label'],r)) for r in sorted(alias_rows)])
    print('Cells:',len(summaries),'completed matches:',len(normalized),'issues:',len(issues_report))
    print('Benchmark exceptions:',json.dumps([r for r in summaries if r.get('difference_from_benchmark')],indent=2))
    for league in CODES.values():
        unmatched={r['match_label'] for r in club_comparisons if r['league']==league and r['status']=='unresolved'}
        missing={r['player_label'] for r in club_comparisons if r['league']==league and r['status']=='player_label_unmatched'}
        print(league,'match labels',sorted(unmatched),'player labels',sorted(missing))


if __name__=='__main__':
    run()
