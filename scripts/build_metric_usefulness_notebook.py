"""Create a reproducible entry point for the approved diagnostic experiment."""
from pathlib import Path
import nbformat as nb

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'notebooks/05_metric_usefulness.ipynb'
if target.exists():raise FileExistsError('Preserve existing notebook: '+str(target))
cells=[
 nb.v4.new_markdown_cell('# Metric usefulness: overlap and team opportunity\n\nOwner-selected diagnostic experiment. Five leagues, 2017–18 through 2024–25, 900+ reported-minute focus. No score, weights, replacement baseline or final WAR formula. Specific profile roles are provisional diagnostic strata, not historically evidenced main positions; do not use them for chronological model validation.'),
 nb.v4.new_code_cell("import sys\nfrom pathlib import Path\nfrom IPython.display import display, Markdown, Image\nroot=Path.cwd()\nif not (root/'scripts').exists(): root=root.parent\nsys.path.insert(0,str(root/'scripts'))\nfrom research_metric_usefulness import run\noverlaps,team_context,lineage=run()\ndisplay(Markdown((root/'reports/metric_usefulness/results.md').read_text(encoding='utf-8')))"),
 nb.v4.new_markdown_cell('## Inspect the cell counts\n\nEvery correlation retains paired record/club counts. Three pairs only permits calculation; it is not a reliability threshold. Cells are kept separate by league, season, specific profile role and source. Unknown roles and missing team context are counted in the coverage report.'),
 nb.v4.new_code_cell("import pandas as pd\ndisplay(pd.read_csv(root/'reports/metric_usefulness/cohort_accounting.csv'))\ndisplay(pd.read_csv(root/'reports/metric_usefulness/role_and_context_coverage.csv'))\ndisplay(overlaps.query(\"league == 'Premier League' and season == '2024-25'\"))"),
 nb.v4.new_markdown_cell('## Distinguish workload from value\n\nEach club-role-source contributes once to the team-context correlation. Exposure-weighted metric rates are descriptive, not adjusted performance. Goals conceded per match includes time when a player was absent and is not a direct defensive-opportunity measure. Keeper saves are partly contained in shots faced. Correlations do not establish causality or player importance.'),
 nb.v4.new_code_cell("display(team_context.query(\"league == 'Premier League' and season == '2024-25'\"))\ndisplay(Image(filename=str(root/'reports/metric_usefulness/metric_diagnostics.png')))"),
 nb.v4.new_markdown_cell('## Before modeling\n\nLow overlap does not prove that a metric captures valuable contributions. Direct event/location/pressure evidence and held-out validation are still needed. PSxG source warnings and arithmetic flags remain. Off-ball prevention is incompletely observed. No weights are selected to force defenders or keepers up a leaderboard. Read docs/metric_usefulness_experiment.md for the next discussion.'),
]
book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}})
nb.write(book,target)
print(target)
