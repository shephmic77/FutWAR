from pathlib import Path
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
s=s.replace('<span class="badge" aria-label="Club crest unavailable">${esc(r.team)}</span>', '<span class="crest-fallback" aria-label="Club crest unavailable" title="${esc(r.team)} crest unavailable">${esc(initials(r.team))}</span>')
p.write_text(s,encoding='utf-8')
p=Path('profile/explorer.css');p.write_text(p.read_text(encoding='utf-8')+'\n.crest-fallback{display:inline-grid;place-items:center;width:48px;height:56px;border-radius:6px;background:var(--soft);color:var(--muted);font-size:18px;}\n',encoding='utf-8')
