"""Extract archived secondary tables and compare without altering source results."""
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup
from export_initial_eda import psql
from audit_standings_and_identity import write_csv

LABELS = {'Pld':'played','W':'wins','D':'draws','L':'losses',
          'GF':'goals_for','GA':'goals_against','GD':'goal_difference','Pts':'official_points'}


def resolve_points(calculated, reported, review):
    if review is None:
        return reported, 'matches_secondary_reference' if calculated==reported else 'needs_explanation'
    if review['reference_points']!=reported or calculated+review['points_adjustment']!=review['reviewed_points']:
        raise ValueError('Reviewed points evidence no longer matches observed discrepancy')
    if not review['source_urls'] or review['classification'] not in (
        'secondary_reference_error','verified_points_deduction'):
        raise ValueError('Invalid discrepancy evidence')
    return review['reviewed_points'],review['classification']


def extract_table(html, expected_clubs):
    soup = BeautifulSoup(html,'html.parser')
    candidates = []
    for table in soup.find_all('table'):
        first = table.find('tr')
        if first is None:
            continue
        headers = [c.get_text(' ',strip=True) for c in first.find_all(['th','td'],recursive=False)]
        if not all(label in headers for label in LABELS) or not headers[1].startswith('Team'):
            continue
        rows = []
        for row in table.find_all('tr')[1:]:
            cells = row.find_all(['th','td'],recursive=False)
            if len(cells)<10:
                continue
            for cell in cells:
                for footnote in cell.find_all('sup'):
                    footnote.decompose()
            text = [c.get_text(' ',strip=True) for c in cells]
            if not re.fullmatch(r'\d+',text[0]):
                continue
            label = re.sub(r'\s*\([^)]*\)','',text[1]).strip()
            numeric = {metric:int(text[headers.index(col)].replace('\u2212','-').replace('+',''))
                       for col,metric in LABELS.items()}
            if numeric['played'] != numeric['wins']+numeric['draws']+numeric['losses']:
                raise ValueError('Invalid W/D/L accounting in reference')
            if numeric['goal_difference'] != numeric['goals_for']-numeric['goals_against']:
                raise ValueError('Invalid goal accounting in reference')
            rows.append(dict(source_team_label=label,official_position=int(text[0]),**numeric))
        if len(rows)==expected_clubs:
            if len({r['source_team_label'] for r in rows}) != expected_clubs:
                raise ValueError('Duplicate source clubs')
            candidates.append(rows)
    if len(candidates)!=1:
        raise ValueError(f'Expected one {expected_clubs}-club standings table, got {len(candidates)}')
    return candidates[0]


def main():
    manifest = json.loads(Path('data/wikipedia_standings_manifest.json').read_text(encoding='utf-8'))
    if len(manifest['files'])!=40:
        raise ValueError('Acquisition must finish all 40 pages before the audit')
    baseline = list(csv.DictReader(io.StringIO(psql('--csv','-c',
        'SELECT * FROM futwar.team_results_baseline ORDER BY league,season,team;'))))
    lookup = {(r['league'],r['season'],r['team']):r for r in baseline}
    aliases_path = Path('data/wikipedia_club_aliases.json')
    aliases = json.loads(aliases_path.read_text(encoding='utf-8')) if aliases_path.exists() else {}
    references,unmatched = [],[]
    for source in manifest['files']:
        path = Path(source['path'])
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest()!=source['sha256']:
            raise ValueError(f'Archived source changed: {path}')
        expected = 18 if source['league']=='Bundesliga' or (
            source['league']=='Ligue 1' and source['season']>='2023-24') else 20
        parsed = json.loads(payload.decode('utf-8'))['parse']
        if parsed['revid']!=source['revision_id'] or parsed['title']!=source['title']:
            raise ValueError('Archived revision metadata differs')
        rows = extract_table(parsed['text']['*'],expected)
        for row in rows:
            league,season = source['league'],source['season']
            name = row['source_team_label']
            canonical = aliases.get(league,{}).get(name,name)
            if (league,season,canonical) not in lookup:
                unmatched.append(dict(league=league,season=season,source_team_label=name))
            references.append(dict(source_sha256=source['sha256'],league=league,season=season,
                team=canonical,revision_id=source['revision_id'],source_url=source['source_url'],**row))
    report = Path('reports/historical_standings')
    report.mkdir(parents=True,exist_ok=True)
    if unmatched:
        unique = {tuple(r.values()):r for r in unmatched}
        write_csv(report/'unmatched_clubs.csv',list(unique.values()))
        print(json.dumps({'unmatched':list(unique.values())},indent=2,ensure_ascii=False))
        raise ValueError('Review explicit aliases before generating validated comparisons')
    keys = [(r['league'],r['season'],r['team']) for r in references]
    if len(keys)!=len(set(keys)) or set(keys)!=set(lookup):
        raise ValueError('References do not map one-to-one onto all baseline club-seasons')
    review_path=Path('data/raw/standings_references/historical_points_adjudications_2026-10-10.json')
    review_payload=review_path.read_bytes()
    reviews=json.loads(review_payload.decode('utf-8'))['records']
    reviewed={(r['league'],r['season'],r['team']):r for r in reviews}
    if len(reviewed)!=len(reviews) or not set(reviewed).issubset(set(keys)):
        raise ValueError('Duplicate or unmatched points adjudication')
    comparisons = []
    for ref in references:
        base = lookup[ref['league'],ref['season'],ref['team']]
        diff = {f'{m}_difference':int(base[m])-ref[m] for m in LABELS.values() if m!='official_points'}
        points_diff = ref['official_points']-int(base['earned_match_points'])
        review=reviewed.get((ref['league'],ref['season'],ref['team']))
        reviewed_points,status=resolve_points(int(base['earned_match_points']),ref['official_points'],review)
        if any(diff.values()):
            status='needs_explanation'
        comparisons.append(dict(league=ref['league'],season=ref['season'],team=ref['team'],
            **diff,calculated_match_points=int(base['earned_match_points']),
            official_points=ref['official_points'],points_adjustment_or_discrepancy=points_diff,
            reviewed_points=reviewed_points,status=status,
            source_url=ref['source_url'],source_sha256=ref['source_sha256']))
    write_csv(report/'comparisons.csv',comparisons)
    differences = [r for r in comparisons if any(r[f'{m}_difference'] for m in LABELS.values()
        if m!='official_points') or r['points_adjustment_or_discrepancy']]
    write_csv(report/'discrepancies.csv',differences,list(comparisons[0]))
    write_csv(Path('data/processed/postgres/historical_standings.csv'),references)
    review_sha=hashlib.sha256(review_payload).hexdigest()
    write_csv(Path('data/processed/postgres/points_adjudications.csv'),[
        dict(source_sha256=review_sha,league=r['league'],season=r['season'],team=r['team'],
             reference_points=r['reference_points'],reviewed_points=r['reviewed_points'],
             points_adjustment=r['points_adjustment'],classification=r['classification'],
             source_urls=json.dumps(r['source_urls']),note=r['note'],reviewed_at=r['reviewed_at']) for r in reviews])
    summary = dict(source='Wikipedia contributors; archived secondary references, not official certification',
        reference_club_seasons=len(references),league_seasons=len(set((r['league'],r['season']) for r in references)),
        unmatched_club_seasons=0,compared_metrics_per_club=8,
        discrepancy_club_seasons=len(differences),status_counts=dict(Counter(r['status'] for r in comparisons)),
        unresolved_club_seasons=sum(r['status']=='needs_explanation' for r in comparisons),
        adjudications_sha256=review_sha,
        original_results_modified=False)
    (report/'run.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    print(json.dumps(differences,indent=2,ensure_ascii=False))


if __name__=='__main__':
    main()
