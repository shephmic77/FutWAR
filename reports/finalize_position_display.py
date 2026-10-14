from pathlib import Path
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
s=s.replace('Object.entries(current.source_stats).filter(([k])=>norm(k).includes(norm(sourceQuery)))', "Object.entries(current.source_stats).filter(([k])=>k!=='pos_'&&norm(k).includes(norm(sourceQuery)))")
s=s.replace("const roleMatches=p=>roleMode==='all'||(role(display())!=='Unavailable'&&role(p)===role(display()));", "const wantedRole=role(display()),roleMatches=p=>roleMode==='all'||(wantedRole!=='Unavailable'&&role(p)===wantedRole);")
p.write_text(s,encoding='utf-8')
