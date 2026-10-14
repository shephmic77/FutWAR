"""Inspect archived PSxG candidates; no values are filled or model versions assumed."""
import hashlib
import json
import re

from reconcile_keeper_candidates import ROOT
import pandas as pd
import pyreadr


def provider_id(url):
    match = re.search(r'/players/([0-9a-f]{8})(?:/|$)', str(url))
    return match[1] if match else None


def main():
    staged_path = ROOT / 'data/processed/keeper_archives/keeper_seasons_corrected.csv'
    staged = pd.read_csv(staged_path)
    missing = staged.loc[staged.psxg.isna()]
    hashes = {staged_path.relative_to(ROOT).as_posix(): hashlib.sha256(staged_path.read_bytes()).hexdigest()}
    manifest = json.loads((ROOT / 'data/keeper_archive_manifest.json').read_text(encoding='utf-8'))
    files = {item['name']: item for item in manifest['files']}
    sources = {}
    for variant in ['release', 'repository', 'statsbomb']:
        for advanced in [False, True]:
            name = f'{variant}_big5_player_keepers' + ('_adv' if advanced else '') + '.rds'
            item = files[name]
            path = ROOT / item['path']
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != item['sha256']:
                raise ValueError('Keeper source hash changed')
            hashes[item['path']] = digest
            frame = next(iter(pyreadr.read_r(str(path)).values()))
            frame['provider_id'] = frame.Url.map(provider_id)
            sources[variant, advanced] = frame
    rows = []
    for target in missing.to_dict('records'):
        identifier = provider_id(target['player_url'])
        if identifier is None:
            raise ValueError('Missing provider identity for missing-PSxG row')
        year = int(target['season'][:4]) + 1
        for variant in ['release', 'repository', 'statsbomb']:
            pair = []
            for advanced in [False, True]:
                frame = sources[variant, advanced]
                candidate = frame.loc[frame.provider_id.eq(identifier) & frame.Season_End_Year.eq(year)
                                      & frame.Comp.eq(target['league']) & frame.Squad.eq(target['team_name'])]
                if len(candidate) > 1:
                    raise ValueError('Ambiguous archived candidate')
                pair.append(candidate.iloc[0] if len(candidate) else None)
            basic, advanced = pair
            status = 'no_paired_record'
            psxg, minutes, appearances, nineties, ga, og = [None] * 6
            if basic is not None and advanced is not None:
                if int(basic.Born) != int(target['birth_year']) or int(advanced.Born) != int(target['birth_year']):
                    raise ValueError('Candidate birth year conflict')
                psxg, minutes, appearances = advanced.PSxG_Expected, basic.Min_Playing, basic.MP_Playing
                nineties, ga, og = advanced.Mins_Per_90, advanced.GA_Goals, advanced.OG_Goals
                compatible = (pd.notna(minutes) and minutes == target['keeper_minutes']
                    and appearances == target['appearances'] and pd.notna(nineties)
                    and abs(minutes / 90 - nineties) <= 0.07)
                if pd.isna(psxg):
                    status = 'psxg_still_missing'
                elif not compatible:
                    status = 'record_exposure_mismatch_do_not_fill'
                elif pd.notna(target['goals_against']) and ga != target['goals_against']:
                    status = 'goals_against_mismatch_do_not_fill'
                else:
                    status = 'exposure_agrees_metric_version_unconfirmed'
            name = f'{variant}_big5_player_keepers_adv.rds'
            rows.append(dict(keeper_record_id=target['keeper_record_id'], player_name=target['player_name'],
                league=target['league'], season=target['season'], team_name=target['team_name'],
                provider_player_id=identifier, source_variant=variant, candidate_status=status,
                candidate_psxg=psxg, candidate_keeper_minutes=minutes, candidate_appearances=appearances,
                candidate_advanced_90s=nineties, candidate_goals_against=ga, candidate_own_goals_against=og,
                target_keeper_minutes=target['keeper_minutes'], target_appearances=target['appearances'],
                target_goals_against=target['goals_against'], candidate_source_url=files[name]['source_url'],
                candidate_source_sha256=files[name]['sha256'],
                interpretation='Observed candidate only; common upstream, unknown model version; no correction applied'))
    result = pd.DataFrame(rows)
    output = ROOT / 'reports/keeper_archive'
    result.to_csv(output / 'missing_psxg_candidates.csv', index=False)
    summary = dict(missing_records=len(missing), candidate_checks=len(result),
        candidate_status_counts=result.candidate_status.value_counts().to_dict(),
        input_sha256=hashes, measurements_changed=False)
    (output / 'missing_psxg_lineage.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    for path, digest in hashes.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Input modified during candidate audit')
    print(json.dumps({key: value for key, value in summary.items() if key != 'input_sha256'}, indent=2))


if __name__ == '__main__':
    main()
