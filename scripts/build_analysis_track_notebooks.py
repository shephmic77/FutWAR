"""Create two clean entry notebooks preserving the existing domain notebooks."""
from pathlib import Path
import nbformat as nb

ROOT=Path(__file__).resolve().parents[1]
setup="""import sys
from pathlib import Path
from IPython.display import display
root=Path.cwd()
if not (root/'scripts').exists():
    root=root.parent
sys.path.insert(0,str(root/'scripts'))
from analysis_tracks import run
outfield,keepers,accounting,positions,overlaps,role_counts=run()
display(accounting)
display(role_counts)
"""
spec=dict(display_name='Python 3',language='python',name='python3')
tracks={
    '03_all_positions_exploration.ipynb':[
        nb.v4.new_markdown_cell('# Player analysis by position — outfield and GK\n\n'
            'Describe each position separately, with 900+ reported minutes and exclusions counted. '
            'GK is part of this analysis. Outfield nominal DF/MF/FW and mixed labels remain provisional; '
            'we cannot fabricate LB/RB/CB/LWB/RWB from them. No overall score or model is produced.'),
        nb.v4.new_code_cell(setup),
        nb.v4.new_markdown_cell('## Same research scope, distinct measurements\n\n'
            'Both domains cover the Big Five, 2017–18 through 2024–25, including COVID seasons. '
            'Records are player–club–season stints. Original GK rows are outside the outfield cohort; '
            'keeper measurements come from the reviewed separate archive. No cross-provider identity or stat merge '
            'is implied. Do not sum the two source counts as unique players. The analysis-domain counts refer to separate stints.'),
        nb.v4.new_code_cell("display(positions.groupby(['position','metric'],as_index=False)[['included_records','available_values','missing_values']].sum())\nassert (positions.position=='GK').any()\nassert outfield.nominal_position.ne('GK').all()"),
        nb.v4.new_markdown_cell('## Within-position distributions\n\n'
            'Select a league/season, then inspect positions separately. Metrics and units differ by domain; '
            'neither tackles nor PSxG can be interpreted as the same amount of player value. Missing cells remain missing. '
            'Empty position groups are not filled with invented records.'),
        nb.v4.new_code_cell("season='2024-25'\nleague='Premier League'\ndisplay(positions.loc[positions.season.eq(season)&positions.league.eq(league)])"),
        nb.v4.new_markdown_cell('## Domain details and retained warnings\n\n'
            'Continue with 01_player_metrics_exploration.ipynb for outfield figures and '
            '02_keeper_metrics_exploration.ipynb for keeper domains, exclusions and warnings. '
            'Reported keeper residuals with arithmetic flags are unavailable for that metric. '
            'Older-source PSxG fills remain in descriptions with explicit warnings; all exact model versions are unresolved. '
            'Secondary historical roles require at least five appearances and 10% of full-season appearances. '
            'This notebook does not add any position labels.'),
        nb.v4.new_code_cell("display(keepers.loc[keepers.has_diagnostic_flag|keepers.has_exposure_warning|keepers.has_psxg_warning,['player_name','season','unresolved_quality_flags','exposure_correction_warnings','psxg_correction_warnings']])"),
    ],
    '04_player_value_metric_research.ipynb':[
        nb.v4.new_markdown_cell('# Overall player-value research — every position, including GK\n\n'
            'Core question: observed seasonal contribution above a readily available replacement-level player. '
            'This first step examines measurement coverage and overlap before any contribution formula is chosen. '
            'Different positions need different evidence; eventual comparison requires a validated common outcome scale. '
            'No score, weights, replacement baseline or league adjustment is selected here.'),
        nb.v4.new_code_cell(setup),
        nb.v4.new_markdown_cell('## Candidate contribution domains\n\n'
            '- Attacking: goals, non-penalty goals, assists, npxG, xA and xAG.\n'
            '- Progression: progressive passes and carries.\n'
            '- Defensive actions: tackles and interceptions; these omit much off-ball prevention.\n'
            '- Keeper actions: reported shot-stopping residual, distribution, cross stopping and sweeping. '
            'PSxG faced and shot counts also describe opportunity/difficulty rather than ability alone.\n\n'
            'These are measurement candidates, not independently additive contributions. More events do not automatically '
            'mean greater value. Goals will not be downweighted merely to force a balanced leaderboard.'),
        nb.v4.new_code_cell("display(positions.groupby(['position','metric'],as_index=False)[['available_values','missing_values']].sum())"),
        nb.v4.new_markdown_cell('## Metric overlap within context\n\n'
            'Spearman correlations are descriptive checks within position × league × season × source. '
            'Pair counts and constant/insufficient samples are shown. Three pairs is only a computability guard, '
            'not evidence of reliability. Older-source PSxG fills are omitted only from these source-cohort '
            'correlations; they remain in descriptive profiles. Source versions remain unconfirmed. '
            'Correlations cannot determine importance, weights, causality or league strength.'),
        nb.v4.new_code_cell("league='Premier League'\nseason='2024-25'\nselected=overlaps.loc[overlaps.league.eq(league)&overlaps.season.eq(season)]\ndisplay(selected.loc[selected.position.isin(['FW','DF','GK'])].sort_values(['position','left_metric','right_metric']).head(90))"),
        nb.v4.new_markdown_cell('## Decisions still needed before a model\n\n'
            'Read docs/player_value_research.md and docs/replacement_baseline_research.md for the existing research. '
            'We need to agree on credit allocation, specific position/role comparators, replacement-pool estimation, '
            'league/opponent context, small-sample stabilization and calibration to outcomes. '
            'Teammate, opponent and tactical effects are not estimated by this notebook. '
            'The 900-minute exploratory focus does not define replacement eligibility. '
            'A position-relative percentile would not by itself put GK and outfield value on one common scale. '
            'Inspect overlap and coverage, then discuss a bounded contribution-estimation pilot before implementing it.'),
    ]
}
for filename,cells in tracks.items():
    target=ROOT/'notebooks'/filename
    if target.exists():
        raise ValueError(f'Notebook already exists: {target}')
    notebook=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':spec})
    nb.write(notebook,target)
    print(target)
