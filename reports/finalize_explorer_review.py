from pathlib import Path
p=Path('profile/explorer.js')
s=p.read_text(encoding='utf-8')
old="${euro([...p.rows].sort((a,b)=>a.season.localeCompare(b.season)).at(-1).market_value?.eur)}"
new="${(()=>{const value=[...p.rows].sort((a,b)=>a.season.localeCompare(b.season)).at(-1).market_value;return euro(value?.eur)+(value?'<br><span class=\"small\">Recorded '+esc(value.date)+'</span>':'');})()}"
assert old in s
s=s.replace(old,new)
s=s.replace("p.name+' · '+p.league+' · '+p.team+' · '+fmt(p.minutes,0)+' minutes'", "p.name+' · '+p.league+' · '+p.team+' · Position: '+(p.position||'Unknown')+' · '+fmt(p.minutes,0)+' minutes'")
p.write_text(s,encoding='utf-8')
