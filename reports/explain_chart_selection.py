from pathlib import Path
p=Path('profile/explorer.html');s=p.read_text(encoding='utf-8')
s=s.replace('<p id="peer-note" class="small"></p>', '<p id="peer-note" class="small"></p><details><summary>Why these dots?</summary><div id="peer-selection-details" class="small"></div></details>')
p.write_text(s,encoding='utf-8')
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
old="chartPoints=peerPoints().filter(p=>p.metrics[kx]!=null&&p.metrics[ky]!=null);"
new="""const eligible=peerPoints(),compatible=eligible.filter(p=>p.metrics[kx]!=null&&p.metrics[ky]!=null);chartPoints=[...compatible];
 const seasons=new Set(selectedRows().map(r=>r.season)),scope=data.records.filter(r=>r.domain===current.domain&&seasons.has(r.season));
 const selectedExtra=picked.metrics[kx]!=null&&picked.metrics[ky]!=null&&!chartPoints.some(p=>p.rows.some(r=>r.id===current.id));
 $('peer-selection-details').innerHTML=row('Selected season(s)',periodText(selectedRows()))+row('Player group',current.domain==='GK'?'Goalkeepers':'Outfield players')+row('Source records in those seasons/group',fmt(scope.length,0))+row('Position filter',$('peer-role').value==='all'?'All specific positions':role(display())+' · profile evidence')+row('League filter',$('peer-league').selectedOptions[0].textContent)+row('Minimum minutes',fmt(Number($('peer-minutes').value),0)+($('combine-period').checked?' across the selected period':' in the selected season'))+row('Peer observations passing these filters',fmt(eligible.length,0))+row('Excluded: one or both axis metrics missing',fmt(eligible.length-compatible.length,0))+row('Eligible peers plotted',fmt(compatible.length,0))+row('Selected-player exception',selectedExtra?'Added separately; hollow if below the minute cutoff':'Already qualifies, or required metrics are unavailable')+'<p>Every qualifying observation is shown. No random sample, top-player selection or dot-count cap is applied. Overlapping dots can look like one point. Single-season dots represent player-club-season records; pooled-period dots follow the selected league display. Unknown specific positions cannot qualify for a same-position peer filter.</p>';
"""
assert old in s;s=s.replace(old,new)
s=s.replace("if($('median-guides').checked){const x=a.x(quantile(xs,.5)),y=a.y(quantile(ys,.5));", "if($('median-guides').checked&&compatible.length){const x=a.x(quantile(compatible.map(p=>p.metrics[kx]),.5)),y=a.y(quantile(compatible.map(p=>p.metrics[ky]),.5));")
p.write_text(s,encoding='utf-8')
