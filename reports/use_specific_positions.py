from pathlib import Path
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
start=s.index('const roleNames=');end=s.index('\n',start)
s=s[:start]+"const roleNames={GK:'Goalkeeper',RB:'Right-back',RWB:'Right wingback',CB:'Centre-back',LB:'Left-back',LWB:'Left wingback',CM:'Central midfielder',CDM:'Defensive midfielder',CAM:'Attacking midfielder',LM:'Left midfielder',RM:'Right midfielder',ST:'Striker',LW:'Left winger',RW:'Right winger'};"+s[end:]
s=s.replace("function role(r){return r.display_role||history(r).find(x=>x.display_role)?.display_role||r.position||'Unavailable';}","function role(r){return FutwarCore.specificPosition(r.display_role||history(r).find(x=>x.display_role)?.display_role||r.position);}")
s=s.replace("+row('Source position',r.position||'Unavailable')+row('Profile position',roleNames[role(r)]||role(r))", "+row('Position',role(r))")
s=s.replace("+row('Source position',r.position||'Unavailable')", "")
s=s.replace("row('Displayed profile role',roleNames[role(r)]||role(r))", "row('Position',role(r))")
s=s.replace("role(r)+' · source '+(r.position||'unknown')", "role(r)")
s=s.replace("roleExposure.set(row.position,(roleExposure.get(row.position)||0)+(exposure(row)||0));", "const code=role(row);if(code!=='Unavailable')roleExposure.set(code,(roleExposure.get(code)||0)+(exposure(row)||0));")
s=s.replace("position:majorityRole,team:majorityClub", "position:majorityRole,display_role:majorityRole||'Unavailable',team:majorityClub")
s=s.replace("r.position===current.position&&exposure(r)>=900", "role(current)!=='Unavailable'&&role(r)===role(current)&&exposure(r)>=900")
s=s.replace('Peer band uses same broad source position, all five leagues, 900+ minutes.', 'Peer band uses the same specific profile position, all five leagues, 900+ minutes.')
s=s.replace("const roleMatches=p=>roleMode==='all'||(roleMode==='profile'?role(p)===role(current):p.position===display().position);", "const roleMatches=p=>roleMode==='all'||(role(display())!=='Unavailable'&&role(p)===role(display()));")
s=s.replace("chartPoints.map(p=>p.position||'Unknown')", "chartPoints.map(p=>role(p))")
s=s.replace("positions.indexOf(p.position||'Unknown')", "positions.indexOf(role(p))")
s=s.replace("(p.position||'Unknown')", "role(p)")
s=s.replace('<th>Source position</th>', '<th>Position</th>')
s=s.replace("${esc(r.position||'Unknown')}", "${esc(role(r))}")
# Do not display original broad position codes in the raw-stat inspector.
start=s.index('function renderSourceFields()');end=s.index('\nfunction ',start+1)
part=s[start:end]
part=part.replace('Object.entries(r.source_stats)', "Object.entries(r.source_stats).filter(([k])=>k!=='pos_')")
s=s[:start]+part+s[end:]
p.write_text(s,encoding='utf-8')
p=Path('profile/explorer.html');s=p.read_text(encoding='utf-8')
s=s.replace('<option value="source">Same source position</option><option value="profile">Same profile role (provisional)</option>', '<option value="profile">Same specific position (profile evidence)</option>')
p.write_text(s,encoding='utf-8')
