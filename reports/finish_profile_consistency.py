from pathlib import Path
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
s=s.replace("const a=asset('action',r.name)||asset('portrait',r.name),remote=r.profile_portrait;","const a=asset('action',r.name)||asset('portrait',r.name),remote=profilePortrait(r);")
s=s.replace("function role(r){return r.display_role||r.position||'Unavailable';}","function profilePortrait(r){return r.profile_portrait||history(r).find(x=>x.profile_portrait)?.profile_portrait;}\nfunction role(r){return r.display_role||history(r).find(x=>x.display_role)?.display_role||r.position||'Unavailable';}")
s=s.replace("pc=r.profile_context,d=r.details;", "pc={...history(r).find(x=>x.profile_context?.height_cm)?.profile_context,...r.profile_context},d=r.details;")
s=s.replace("if(r.profile_portrait)$('player-evidence')", "if(profilePortrait(r))$('player-evidence')")
s=s.replace("${esc(r.profile_portrait.source_page)}", "${esc(profilePortrait(r).source_page)}")
s=s.replace("The image may be current and is not evidence of the selected season's kit or role.","The image may be current and can be shared across this source-name/birth-year profile. It is not evidence of the selected season's kit or role.")
p.write_text(s,encoding='utf-8')
