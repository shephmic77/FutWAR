from pathlib import Path
p=Path('profile/explorer.html');s=p.read_text(encoding='utf-8')
s=s.replace('<script src="explorer.js"></script>','<script src="explorer_core.js"></script><script src="explorer.js"></script>')
s=s.replace('Provider estimates in EUR, separate from transfer fees, contribution and replacement cost. Headline uses the latest in-season estimate on or before June 30.','End-of-season market estimates in EUR, using the latest recorded value on or before June 30. Transfer fees are separate.')
s=s.replace('Recorded valuation dates','Exact dates & source history')
p.write_text(s,encoding='utf-8')
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
s=s.replace("String(s).normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase().trim()","FutwarCore.normalize(s)")
start=s.index('const groups=new Map()');end=s.index('\ncurrent=data.records.find',start)
s=s[:start]+'''const groups=FutwarCore.buildGroups(data.records),byId=new Map(data.records.map(r=>[r.id,r]));
for(const r of data.records)Object.defineProperty(r,'source_stats',{get:()=>Object.fromEntries(data.sourceColumns.map((c,i)=>[c,data.sourceRows[r.sourceIndex][i]]))});
'''+s[end:]
start=s.index('function search(text)');end=s.index('\nfunction initPeriod()',start)
s=s[:start]+'''function search(text){
 const query=norm(text),box=$('search-results');if(!query){box.hidden=true;return;}
 const {matches,suggested}=FutwarCore.searchGroups(groups,text);box.hidden=false;box.replaceChildren();
 for(const hit of matches.slice(0,40)){const b=document.createElement('button');b.type='button';b.className='search-hit';b.innerHTML=`<span><strong>${esc(hit.latest.name)}</strong><small> · ${esc(hit.latest.team)}</small></span><small>${[...new Set(hit.rows.map(r=>r.season))].length} seasons · ${esc(role(hit.latest))}</small>`;b.onclick=()=>openPlayer(hit.latest);box.append(b);}
 const p=document.createElement('p');p.className='small';p.textContent=matches.length?`${suggested?'Suggested spelling matches':'Players found'}: ${matches.length}${matches.length>40?' · Refine your search for more results':''}`:'No source record found. Try a surname or club.';box.append(p);announce(p.textContent);
}
document.addEventListener('pointerdown',e=>{if(!$('search-results').contains(e.target)&&!$('global-search').contains(e.target)&&!$('home-search').contains(e.target))$('search-results').hidden=true;});
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('search-results').hidden=true;});
'''+s[end:]
s=s.replace("initPeriod();initMetrics();show('player');announce(","initPeriod();initMetrics();show('player');window.scrollTo({top:0,behavior:'instant'});announce(")
s=s.replace("row('June 30 market estimate',market?euro(market.eur)+' · '+market.date:'Unavailable')","row('End-of-season market value',market?euro(market.eur)+' · '+market.cutoff.slice(0,4):'Unavailable')")
s=s.replace('Recorded ${esc(mv.date)} · cutoff ${esc(mv.cutoff)} · ${esc(headlineRecord.season)}','End of season · ${esc(mv.cutoff.slice(0,4))}')
start=s.index('function drawMarket()');end=s.index('\nfunction renderComparison()',start)
# drawMarket is followed by comparison helpers; preserve them.
next_function=s.index('\nfunction ',start+1);end=next_function
s=s[:start]+'''function drawMarket(){
 if(view!=='player'||tab!=='context')return;
 const values=FutwarCore.seasonValues(history()),f=chartFrame('market-chart','Season ending year','Market value · EUR');
 if(!values.length){f.svg.innerHTML='<text x="30" y="70">No end-of-season market values available.</text>';return;}
 const lo=values[0].year,hi=values.at(-1).year,max=Math.max(...values.map(v=>v.eur))||1;
 const a=axes(f,lo-.2,hi+.2,0,max*1.12,v=>String(Math.round(v)),euro);
 f.svg.innerHTML=a.html+`<path d="M${values.map(v=>`${a.x(v.year)} ${a.y(v.eur)}`).join('L')}" fill="none" stroke="var(--team)" stroke-width="2"/>`+values.map(v=>`<circle cx="${a.x(v.year)}" cy="${a.y(v.eur)}" r="${v.season===current.season?7:5}" fill="var(--team)"><title>${v.year} · ${euro(v.eur)}</title></circle>`).join('');
}
'''+s[end:]
s=s.replace("Recorded '+esc(value.date)","End of season '+esc(value.cutoff.slice(0,4))")
s=s.replace('June 30 estimate (last selected season)','End-of-season estimate (last selected year)')
p.write_text(s,encoding='utf-8')
p=Path('profile/explorer.css');s=p.read_text(encoding='utf-8')
s+='\n/* Search stays visible above the current section; selecting a result opens its banner. */\n#search-results{position:fixed;top:81px;left:36px;right:36px;max-height:60vh;overflow-y:auto;z-index:50;background:var(--surface);border:1px solid var(--line);border-radius:10px;box-shadow:0 10px 25px #0002;padding:12px 16px;}\n#search-results[hidden]{display:none;}\n'
p.write_text(s,encoding='utf-8')
