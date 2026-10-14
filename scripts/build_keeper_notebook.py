"""Create the clean descriptive keeper notebook without source data or outputs."""
from pathlib import Path
import nbformat as nb

ROOT = Path(__file__).resolve().parents[1]
notebook = nb.v4.new_notebook()
notebook.metadata.kernelspec = dict(display_name='Python 3', language='python', name='python3')
notebook.cells = [
    nb.v4.new_markdown_cell('# Goalkeeper metrics: first descriptive analysis\n\n'
        'Owner-approved focus: 900+ reported keeper minutes, with exclusions and warnings counted. '
        'All five leagues and eight seasons remain in scope. This is not a FutWAR model or eligibility rule. '
        'Rows are player–club–season records; transfers are not automatically combined.'),
    nb.v4.new_code_cell("import sys\nfrom pathlib import Path\nroot = Path.cwd()\nif not (root/'scripts').exists():\n    root = root.parent\nsys.path.insert(0, str(root/'scripts'))\nfrom explore_keeper_metrics import load_inputs, prepare, reports, plot_domains\nfrom IPython.display import display, Image\nraw, digest = load_inputs()\nframe = prepare(raw)\nexclusions, coverage, distributions, summary = reports(frame, digest)\ndisplay(summary)"),
    nb.v4.new_markdown_cell('## Coverage and exclusions\n\n'
        'The focus uses nominal GK and reported keeper minutes, not advanced source 90s. '
        'Emergency outfield keeper rows stay in the source and exclusion counts. Cell presence is not proof of complete data. '
        'COVID seasons remain included; exclusion or contextual treatment is undecided.'),
    nb.v4.new_code_cell('display(exclusions)\nassert exclusions.eligible_records.sum() + exclusions.excluded_records.sum() == len(frame)\nassert len(coverage) == 40 * 8'),
    nb.v4.new_markdown_cell('## Metric availability and warnings\n\n'
        'Missing measurements remain unknown. Riemann/Lecomte residuals fail the arithmetic check and are unavailable '
        'only for that display; other fields retain their warnings. Approved older-source PSxG fills are identified separately. '
        'All exact model versions remain unconfirmed; comparisons do not establish absolute league strength.'),
    nb.v4.new_code_cell("display(coverage.loc[coverage.unavailable_values.gt(0)])\nwarning_rows = frame.loc[frame.eligible & (frame.has_diagnostic_flag | frame.has_exposure_warning | frame.has_psxg_warning)]\ndisplay(warning_rows[['player_name','team_name','league','season','keeper_minutes','unresolved_quality_flags','exposure_correction_warnings','psxg_correction_warnings','psxg_measurement_source']])"),
    nb.v4.new_markdown_cell('## Separate keeper domains\n\n'
        'Per-90 values are 90 × recorded totals / reported keeper minutes. Cross stopping uses stopped/faced counts, '
        'with nonpositive or invalid denominators unavailable. PSxG/90 describes shot difficulty faced, not ability by itself. '
        'Saves and sweeping depend on opportunities and team tactics. Pass-attempt labels differ between source archives. '
        'Plots separate season/source groups; PSxG fills receive their own source group. No composite score, cross-season '
        'leaderboard or replacement value is produced.'),
    nb.v4.new_code_cell('chart = plot_domains(frame)\ndisplay(Image(filename=str(chart)))\ndisplay(distributions.head(24))'),
    nb.v4.new_markdown_cell('## What this supports next\n\n'
        'Inspect within-season variation, opportunity denominators and source warnings before choosing any keeper contribution method. '
        'PSxG, reported residuals, distribution, crosses and sweeping remain separate domains. This notebook does not validate '
        'model versions, exposure seconds or outcome calibration. Specific historical outfield roles remain a separate data need.\n\n'
        'Provenance: data/keeper_archive_manifest.json, the exposure/PSxG correction ledgers, and docs/keeper_missing_psxg_review.md. '
        'Raw archives, generated reports and executed notebook remain local and ignored by Git.'),
]
path = ROOT/'notebooks/02_keeper_metrics_exploration.ipynb'
if path.exists():
    raise ValueError('Notebook already exists; edit deliberately rather than overwrite')
nb.write(notebook, path)
print(path)
