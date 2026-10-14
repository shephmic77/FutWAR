"""Build research diagrams from the documented FutWAR design and coverage audits."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/war_research'
OUT.mkdir(parents=True, exist_ok=True)
INK = '#26352e'
MUTED = '#66736a'
PAPER = '#fbf8f1'
GREEN = '#51755d'
GOLD = '#bd884a'
RED = '#b74445'
BLUE = '#4b7694'


def esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def svg_start(width, height, title, description):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<title>{esc(title)}</title><desc>{esc(description)}</desc>',
            f'<rect width="100%" height="100%" fill="{PAPER}"/>',
            '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:'+INK+'}.muted{fill:'+MUTED+'}.small{font-size:15px}.body{font-size:18px}.head{font-size:27px;font-weight:700}.sub{font-size:19px}</style>']


def text(x, y, value, cls='body', fill=None):
    style = f' fill="{fill}"' if fill else ''
    return f'<text x="{x}" y="{y}" class="{cls}"{style}>{esc(value)}</text>'


def comparison_matrix():
    w, h = 1500, 940
    svg = svg_start(w, h, 'FutWAR six comparison views',
                    'Three requested baselines crossed with position locked and flexible replacement pools. No player scores are shown.')
    svg += [text(48, 55, 'FutWAR · comparison design', 'head'),
            text(48, 88, 'One shared contribution estimate; three season-specific references; two position-eligibility scopes.', 'sub'),
            text(48, 122, 'Design proposal · no weights fitted · no player WAR values generated', 'small muted')]
    left, top, labelw, colw, rowh = 48, 158, 224, 397, 185
    headers = ['All-five-league average', 'Selected-league average', 'Team-accessible replacement']
    subtitles = ['same season · benchmark', 'chosen league + season · benchmark', 'club · season-start resources']
    for j, (head, sub) in enumerate(zip(headers, subtitles)):
        x = left + labelw + j * colw
        svg += [f'<rect x="{x+5}" y="{top}" width="{colw-10}" height="105" rx="14" fill="#e9eee6"/>',
                text(x+22, top+37, head, 'body'), text(x+22, top+70, sub, 'small muted')]
    scopes = [
        ('Position locked', 'Replacement has the same verified main position.',
         'Same specific position', 'Same specific position', 'Same specific position', GREEN),
        ('Any evidenced position', 'Any eligible main or qualifying secondary role.',
         'Any eligible position', 'Any eligible position', 'Any affordable eligible role', BLUE),
    ]
    for i, (title, desc, a, b, c, color) in enumerate(scopes):
        y = top + 118 + i * rowh
        svg += [f'<rect x="{left}" y="{y}" width="{labelw-12}" height="{rowh-12}" rx="14" fill="#f0e8da"/>',
                text(left+18, y+38, title, 'body'),
                text(left+18, y+70, desc[:29], 'small muted'),
                text(left+18, y+92, desc[29:], 'small muted')]
        for j, (pool, color2) in enumerate(zip((a, b, c), (GREEN, GOLD, RED))):
            x = left + labelw + j * colw
            svg += [f'<rect x="{x+5}" y="{y}" width="{colw-10}" height="{rowh-12}" rx="14" fill="#fffdf8" stroke="#ded6c8"/>',
                    f'<circle cx="{x+29}" cy="{y+37}" r="8" fill="{color2}"/>',
                    text(x+48, y+43, pool, 'body'),
                    text(x+22, y+82, 'Per 90: player impact − pool impact', 'small'),
                    text(x+22, y+110, 'Season: per-90 difference × minutes / 90', 'small'),
                    text(x+22, y+140, 'Uncertainty + eligible-pool count shown', 'small muted')]
    band_y = top + 118 + 2 * rowh + 9
    svg += [f'<rect x="{left}" y="{band_y}" width="{labelw+3*colw-10}" height="85" rx="14" fill="#ede7db"/>',
            text(left+19, band_y+31, 'Contribution scale', 'body'),
            text(left+210, band_y+31, 'Context-aware actions → scoring/prevention value → calibrated expected points', 'body'),
            text(left+19, band_y+61, 'Locked/any-position changes replacement eligibility, not the player’s underlying contribution estimate.', 'small muted'),
            text(left, h-18, 'Average-based columns are above-average benchmarks. Only a feasible replacement comparison can be called WAR.', 'small muted'),
            '</svg>']
    (OUT / 'war_comparison_matrix.svg').write_text('\n'.join(svg), encoding='utf-8')


def readiness_figure():
    w, h = 1500, 700
    svg = svg_start(w, h, 'FutWAR WAR data readiness',
                    'Coverage and limitations by season for player statistics, fixtures, Wyscout events, positions and team budgets.')
    svg += [text(48, 54, 'What the current data can support', 'head'),
            text(48, 87, 'Coverage is not the same as comparability or verified meaning.', 'sub'),
            text(48, 120, '2017–18', 'small'), text(1314, 120, '2024–25', 'small')]
    x0, x1, y0, rowh = 165, 1060, 156, 79
    rows = [
        ('Player-season metrics', 40, 40, 'All 40 league-seasons; outfield + separate keeper work', GREEN),
        ('Match results + standings', 40, 40, 'All 40; team outcomes do not isolate player impact', GREEN),
        ('Fixture-level match context', 40, 40, 'All 40; one 2024–25 Bundesliga fixture misses box-score context', GOLD),
        ('Detailed events', 5, 40, 'Only 2017–18; provider IDs not joined to player-season identities', RED),
        ('Verified played-position minutes', 0, 40, 'Provider exports exist; played-position semantics not verified', RED),
        ('Historical team budget + wages', 0, 40, 'No comparable club-season wage/availability pool assembled', RED),
    ]
    for i, (label, covered, total, note, color) in enumerate(rows):
        y = y0 + i * rowh
        svg += [text(48, y+24, label, 'body'),
                f'<rect x="{x0}" y="{y}" width="{x1-x0}" height="27" rx="8" fill="#e4dfd5"/>']
        fill_width = (x1 - x0) * covered / total
        if fill_width:
            svg.append(f'<rect x="{x0}" y="{y}" width="{fill_width:.1f}" height="27" rx="8" fill="{color}"/>')
        svg += [text(x1+18, y+21, f'{covered} / {total}', 'small'),
                text(48, y+54, note, 'small muted')]
    svg += [text(48, 665, 'Implication: start with a one-season event pilot and a separate position/budget evidence audit. Keep the other years descriptive until comparable evidence is acquired.', 'small muted'), '</svg>']
    (OUT / 'data_readiness_by_season.svg').write_text('\n'.join(svg), encoding='utf-8')


if __name__ == '__main__':
    comparison_matrix()
    readiness_figure()
    print('Wrote two SVG diagrams to reports/war_research/.')
