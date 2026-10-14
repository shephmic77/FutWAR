"""Build a private, source-tracked keeper staging table; no WAR or identity merge."""
import hashlib
import json
from pathlib import Path

from reconcile_keeper_candidates import load_csv, RAW, ROOT
import pandas as pd
import pyreadr

OUTPUT = ROOT / 'data/processed/keeper_archives'
REPORT = ROOT / 'reports/keeper_archive'


def json_value(value):
    return json.loads(pd.Series([value]).to_json(orient='values'))[0]


def flags_for(minutes, nineties, position, psxg, ga, og, delta, appearances, wdl):
    flags = []
    if pd.isna(minutes) or minutes <= 0:
        flags.append('missing_or_nonpositive_keeper_minutes')
    if pd.notna(minutes) and pd.notna(nineties) and abs(minutes/90-nineties) > 0.07:
        flags.append('keeper_minutes_vs_advanced_90s_disagree')
    if position != 'GK':
        flags.append('nominal_non_gk_keeper_record')
    if pd.isna(psxg):
        flags.append('missing_psxg')
    if all(pd.notna(v) for v in [psxg, ga, og, delta]) and abs(psxg-(ga-og)-delta)>0.15:
        flags.append('reported_psxg_residual_arithmetic_review')
    if all(pd.notna(v) for v in wdl) and pd.notna(appearances) and sum(wdl)>appearances:
        flags.append('wdl_exceeds_appearances')
    return flags


def main():
    manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    files = {f['name']: f for f in manifest['files']}
    selected = ['release_big5_player_keepers.rds', 'release_big5_player_keepers_adv.rds']
    for season in ['2023-2024', '2024-2025']:
        selected += [f'nextgen_goalkeeping_{season}.csv', f'nextgen_advanced_goalkeeping_{season}.csv']
    for name in selected:
        if hashlib.sha256((ROOT/files[name]['path']).read_bytes()).hexdigest()!=files[name]['sha256']:
            raise ValueError('Selected source changed')
    sources = []
    b = next(iter(pyreadr.read_r(str(RAW/selected[0])).values()))
    a = next(iter(pyreadr.read_r(str(RAW/selected[1])).values()))
    b = b.loc[b.Season_End_Year.between(2018,2023)]
    a = a.loc[a.Season_End_Year.between(2018,2023)]
    sources.append(('worldfootballR_release', selected[0], selected[1], b, a,
                    ['Season_End_Year','Comp','Squad','Url'],
                    dict(minutes='Min_Playing',appearances='MP_Playing',basic_90s='Mins_Per_90',
                         advanced_90s='Mins_Per_90',psxg='PSxG_Expected',ga='GA_Goals',og='OG_Goals',
                         delta='PSxG+_per__minus__Expected',saves='Saves',sota='SoTA',
                         passes='Att_Passes',crosses='Opp_Crosses',crosses_stopped='Stp_Crosses',
                         sweeper='#OPA_Sweeper',wins='W',draws='D',losses='L')))
    for season in ['2023-2024','2024-2025']:
        bn,an=f'nextgen_goalkeeping_{season}.csv',f'nextgen_advanced_goalkeeping_{season}.csv'
        sources.append(('NextGenEUPlayers',bn,an,load_csv(bn,False),load_csv(an,True),
            ['Season_End_Year','Comp','Squad','Player','Born'],
            dict(minutes='minutes',appearances='appearances',basic_90s='nineties',advanced_90s='nineties',
                 psxg='psxg',ga='ga',og='og',delta='psxg_delta',saves='Performance_Saves',
                 sota='Performance_SoTA',passes='Passes_Att (GK)',crosses='Crosses_Opp',
                 crosses_stopped='Crosses_Stp',sweeper='Sweeper_#OPA',wins='wins',draws='draws',losses='losses')))
    rows = []
    for source,bn,an,basic,advanced,key,mapping in sources:
        if basic[key].isna().any().any() or advanced[key].isna().any().any():
            raise ValueError('Missing pair key')
        if basic.duplicated(key).any() or advanced.duplicated(key).any():
            raise ValueError('Ambiguous source key')
        advanced_index={tuple(r[k] for k in key): r for r in advanced.to_dict('records')}
        if set(advanced_index)!={tuple(r[k] for k in key) for r in basic.to_dict('records')}:
            raise ValueError('Unpaired source rows')
        for br in basic.to_dict('records'):
            ar=advanced_index[tuple(br[k] for k in key)]
            def number(which,name):
                value=(br if which=='basic' else ar).get(mapping[name])
                return pd.to_numeric(value,errors='coerce')
            year=int(br['Season_End_Year'])
            season=f'{year-1}-{str(year)[2:]}'
            identity=json.dumps([source,year,br['Comp'],br['Squad'],br.get('Url'),br['Player'],str(br['Born'])],ensure_ascii=False)
            flags=flags_for(number('basic','minutes'),number('advanced','advanced_90s'),br['Pos'],
                number('advanced','psxg'),number('advanced','ga'),number('advanced','og'),
                number('advanced','delta'),number('basic','appearances'),
                [number('basic',k) for k in ['wins','draws','losses']])
            rows.append(dict(keeper_record_id=hashlib.sha256(identity.encode()).hexdigest(),
                league=br['Comp'],season=season,team_name=br['Squad'],player_name=br['Player'],
                birth_year=br['Born'],nominal_position=br['Pos'],player_url=br.get('Url'),
                keeper_minutes=number('basic','minutes'),appearances=number('basic','appearances'),
                reported_basic_90s=number('basic','basic_90s'),reported_advanced_90s=number('advanced','advanced_90s'),
                saves=number('basic','saves'),shots_on_target_against=number('basic','sota'),
                psxg=number('advanced','psxg'),goals_against=number('advanced','ga'),own_goals_against=number('advanced','og'),
                reported_psxg_delta=number('advanced','delta'),pass_attempts=number('advanced','passes'),
                crosses_faced=number('advanced','crosses'),crosses_stopped=number('advanced','crosses_stopped'),
                sweeper_actions=number('advanced','sweeper'),source_variant=source,
                basic_source_url=files[bn]['source_url'],advanced_source_url=files[an]['source_url'],
                basic_sha256=files[bn]['sha256'],advanced_sha256=files[an]['sha256'],
                identity_status='unverified_cross_provider',metric_version_status='not_confirmed',
                reuse_status='user_authorized_personal_research_rights_unconfirmed',
                exposure_validated=False,quality_flags=json.dumps(flags),
                basic_source_values=json.dumps(json_value(br),ensure_ascii=False),
                advanced_source_values=json.dumps(json_value(ar),ensure_ascii=False)))
    df=pd.DataFrame(rows)
    if df.keeper_record_id.duplicated().any() or df.groupby(['league','season']).ngroups!=40:
        raise ValueError('Duplicate staging IDs or incomplete cell presence')
    OUTPUT.mkdir(parents=True,exist_ok=True)
    REPORT.mkdir(parents=True,exist_ok=True)
    target=OUTPUT/'keeper_seasons.csv'
    df.to_csv(target,index=False)
    coverage=[]
    for (league,season),cell in df.groupby(['league','season']):
        coverage.append(dict(league=league,season=season,records=len(cell),teams=cell.team_name.nunique(),
            source_variant=cell.source_variant.iloc[0],missing_psxg=int(cell.psxg.isna().sum()),
            flagged_records=int(cell.quality_flags.ne('[]').sum()),completeness='not_certified'))
    pd.DataFrame(coverage).to_csv(REPORT/'staged_coverage.csv',index=False)
    record=dict(rows=len(df),cells=len(coverage),flagged_records=int(df.quality_flags.ne('[]').sum()),
        selected_files={name:files[name] for name in selected},
        output_path=target.relative_to(ROOT).as_posix(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        user_decision_date='2026-10-10',use_scope='Personal project; cite sources; no dataset publication authorized',
        raw_modified=False,existing_player_stats_modified=False,war_model_finalized=False)
    (OUTPUT/'lineage.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Staged',len(df),'records across',len(coverage),'cells;',record['flagged_records'],'flagged records retained.')


if __name__=='__main__':
    main()
