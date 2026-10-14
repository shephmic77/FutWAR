"""Inspect source residual consistency; never correct values by arithmetic."""
import hashlib
import json

from reconcile_keeper_candidates import ROOT
import pandas as pd
import pyreadr


def diagnostic(psxg, ga, og, reported):
    if any(pd.isna(value) for value in [psxg, ga, og, reported]):
        return None, None
    value = psxg - (ga - og)
    return round(value, 4), round(reported - value, 4)


def main():
    source = ROOT / 'data/processed/keeper_archives/keeper_seasons_analysis.csv'
    frame = pd.read_csv(source)
    fingerprints = {source.relative_to(ROOT).as_posix(): hashlib.sha256(source.read_bytes()).hexdigest()}
    targets = frame.loc[frame.unresolved_quality_flags.str.contains('reported_psxg_residual_arithmetic_review', regex=False)]
    manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    files = {item['name']: item for item in manifest['files']}
    rows = []
    for target in targets.to_dict('records'):
        variants = []
        variants.append(dict(source_file='selected_analysis_record', source_url=target['advanced_source_url'],
            psxg=target['psxg'], ga=target['goals_against'], og=target['own_goals_against'],
            reported=target['reported_psxg_delta'], nineties=target['reported_advanced_90s']))
        if target['source_variant'] == 'worldfootballR_release':
            for variant in ['repository', 'statsbomb']:
                name = f'{variant}_big5_player_keepers_adv.rds'
                item = files[name]
                path = ROOT / item['path']
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest != item['sha256']:
                    raise ValueError('Residual comparison source changed')
                fingerprints[item['path']] = digest
                data = next(iter(pyreadr.read_r(str(path)).values()))
                match = data.loc[data.Url.eq(target['player_url'])
                    & data.Season_End_Year.eq(int(target['season'][:4])+1)
                    & data.Comp.eq(target['league']) & data.Squad.eq(target['team_name'])]
                if len(match) != 1 or int(match.iloc[0].Born) != int(target['birth_year']):
                    raise ValueError('Missing/ambiguous residual candidate')
                row = match.iloc[0]
                variants.append(dict(source_file=name, source_url=item['source_url'],
                    psxg=row.PSxG_Expected, ga=row.GA_Goals, og=row.OG_Goals,
                    reported=row['PSxG+_per__minus__Expected'], nineties=row.Mins_Per_90))
        for variant in variants:
            value, difference = diagnostic(variant['psxg'], variant['ga'], variant['og'], variant['reported'])
            rows.append(dict(keeper_record_id=target['keeper_record_id'], player_name=target['player_name'],
                season=target['season'], league=target['league'], **variant,
                arithmetic_candidate=value, reported_minus_arithmetic=difference,
                status='unresolved_selected_record' if variant['source_file'] == 'selected_analysis_record'
                    else 'older_snapshot_not_interchangeable', measurement_corrected=False))
    output = ROOT / 'reports/keeper_archive'
    pd.DataFrame(rows).to_csv(output / 'residual_snapshot_review.csv', index=False)
    comparable, mismatches = 0, 0
    for row in frame.itertuples():
        _, difference = diagnostic(row.psxg, row.goals_against, row.own_goals_against, row.reported_psxg_delta)
        if difference is not None:
            comparable += 1
            mismatches += abs(difference) > 0.15
    summary = dict(input_sha256=fingerprints, records=len(frame), comparable_records=comparable,
        arithmetic_mismatches=int(mismatches), target_records=len(targets), snapshot_comparisons=len(rows),
        tolerance=0.15, interpretation='Diagnostic identity only; no definition or WAR formula adopted.',
        measurements_changed=False)
    (output / 'residual_review_lineage.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    for path, digest in fingerprints.items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest:
            raise ValueError('Input changed during residual review')
    print(json.dumps({k: v for k, v in summary.items() if k != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
