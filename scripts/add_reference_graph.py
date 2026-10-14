"""Install the recorded-metric baseline preview without inventing model values."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'profile/explorer.html';s=p.read_text(encoding='utf-8')
marker='<div id="value-context"></div>'
if 'id="reference-chart"' in s:raise ValueError('Preview already installed')
panel='''<section class="panel"><h3>Compare reference baselines</h3><p class="small">Recorded-metric preview · not WAR or an overall contribution score</p><div class="controls"><label>Comparison<select id="reference-mode"><option value="overall">Same-position average · all five leagues</option><option value="league">Same-position league average</option><option value="team">Team-accessible replacement · budget scenarios</option></select></label><label>Metric<select id="reference-metric"></select></label><label>Minimum reference minutes<input id="reference-minutes" type="number" min="1" step="100" value="900"></label><button id="download-reference">Download chart</button></div><div id="reference-leagues" class="legend" hidden></div><div id="reference-budget" hidden><div class="controls"><label>Cost scenario<select id="budget-scenario"><option>Free agents &amp; academy options</option><option>Loans &amp; low-cost acquisitions</option><option>Wider affordable shortlist</option></select></label></div><p class="small">Historical transfer allowance, gross wages, loan/signing/agent costs and realistic availability are needed. Missing costs are not zero; club market value and historic spending are not available budget.</p></div><svg id="reference-chart" class="chart" role="img" aria-label="Selected player's recorded metric above a reference average"></svg><div id="reference-legend" class="legend"></div><p id="reference-note" class="small"></p></section>'''
s=s.replace(marker,marker+panel).replace('<script src="explorer.js"></script>','<script src="value_comparisons.js"></script><script src="explorer.js"></script>')
p.write_text(s,encoding='utf-8')
p=ROOT/'profile/explorer.js';s=p.read_text(encoding='utf-8')
s=s.replace("function options(select,keys,selected)","function options(select,keys,selected)")
s=s.replace("function initMetrics(){const keys=metricKeys();", "function initMetrics(){const keys=metricKeys();options($('reference-metric'),keys,current.domain==='GK'?'reported_residual_per90':'npxg_per90');")
s=s.replace("if(t==='context')drawMarket();save();", "if(t==='context')drawMarket();if(t==='value')drawReferences();save();")
s=s.replace("const observer=new ResizeObserver(()=>{drawTrend();drawScatter();drawMarket();});for(const id of ['trend-chart','scatter-chart','market-chart'])", "const observer=new ResizeObserver(()=>{drawTrend();drawScatter();drawMarket();drawReferences();});for(const id of ['trend-chart','scatter-chart','market-chart','reference-chart'])")
extra='''
function drawReferences(){
 if(view!=='player'||tab!=='value')return;
 const mode=$('reference-mode').value,k=$('reference-metric').value,minimum=Number($('reference-minutes').value);
 $('reference-leagues').hidden=mode!=='league';$('reference-budget').hidden=mode!=='team';
 const f=chartFrame('reference-chart','Season ending year',(labels[k]||k)+' difference'+(k.endsWith('per90')?' / 90':' share'));
 if(!(minimum>0)){f.svg.innerHTML='<text x="30" y="70">Enter a positive reference-minute threshold.</text>';return;}
 if(mode==='team'){
  f.svg.innerHTML='<text x="30" y="70">Team-accessible contribution baseline: not estimated yet.</text>';
  $('reference-legend').innerHTML='';$('reference-note').textContent='Selected scenario: '+$('budget-scenario').value+'. A historical affordable shortlist and a validated contribution estimate are required. No numeric replacement is inferred from squad price, free-transfer status or missing wages.';return;
 }
 const selected=history(),years=[...new Set(selected.map(r=>r.season))].sort();
 const selectedLeagues=[...$('reference-leagues').querySelectorAll('input:checked')].map(e=>e.value);
 const refs=mode==='overall'?[null]:selectedLeagues;
 const series=refs.map(l=>({label:l||'All-five-league average',color:l?leagueColors[leagues.indexOf(l)]:'#16847d',points:years.map(season=>{
  const rows=selected.filter(r=>r.season===season),representative=rows.reduce((a,b)=>(exposure(a)||0)>=(exposure(b)||0)?a:b),player=FutwarReferences.pooled(rows,k),reference=FutwarReferences.reference(data.records,representative,season,k,l,minimum);
  return {year:Number(season.slice(0,4))+1,season,value:player.rate!=null&&reference.rate!=null?player.rate-reference.rate:null,n:reference.players,minutes:player.minutes};
 }).filter(p=>Number.isFinite(p.value))}));
 const values=series.flatMap(s=>s.points.map(p=>p.value));
 if(!values.length){f.svg.innerHTML='<text x="30" y="70">No compatible reference values for this selection.</text>';$('reference-legend').innerHTML='';$('reference-note').textContent='Choose at least one league, or review specific-position and metric coverage.';return;}
 const lo=Math.min(0,...values),hi=Math.max(0,...values),pad=(hi-lo||1)*.1,yearTicks=years.map(s=>Number(s.slice(0,4))+1);
 const a=axes(f,Math.min(...yearTicks)-.15,Math.max(...yearTicks)+.15,lo-pad,hi+pad,v=>String(v),v=>fmt(v,2),yearTicks);
 let html=a.html+`<path d="M${f.L} ${a.y(0)}H${f.w-f.R}" stroke="var(--muted)" stroke-dasharray="4 4"/>`;
 for(const line of series){html+=`<path d="${line.points.map((p,i)=>`${i===0||p.year-line.points[i-1].year>1?'M':'L'}${a.x(p.year)} ${a.y(p.value)}`).join(' ')}" fill="none" stroke="${line.color}" stroke-width="2"/>`;
  for(const p of line.points)html+=`<circle cx="${a.x(p.year)}" cy="${a.y(p.value)}" r="5" fill="${p.minutes<minimum?'var(--surface)':line.color}" stroke="${line.color}"><title>${esc(line.label+' · '+p.year+' · difference '+fmt(p.value)+' · '+p.n+' reference players · '+fmt(p.minutes,0)+' player minutes'+(p.minutes<minimum?' · low minutes':''))}</title></circle>`;
 }
 f.svg.innerHTML=html;$('reference-legend').innerHTML=series.filter(s=>s.points.length).map(s=>`<span><i style="background:${s.color}"></i>${esc(s.label)}</span>`).join('');
 $('reference-note').textContent='Player rate minus the equal-player reference mean in each season. Same specific profile position and '+minimum+'+ metric-supported minutes; selected identity excluded. Transfer stints are pooled within provisional identity groups. Hollow points indicate low selected exposure. Raw league differences are not league-strength-adjusted or player-value estimates. Unknown roles and unavailable metrics are excluded. Hover for reference counts.';
}
for(const l of leagues){const label=document.createElement('label');label.className='check';const input=document.createElement('input');input.type='checkbox';input.value=l;input.checked=true;input.onchange=drawReferences;label.append(input,document.createTextNode(l));$('reference-leagues').append(label);}
for(const id of ['reference-mode','reference-metric','reference-minutes','budget-scenario'])$(id).onchange=drawReferences;
$('download-reference').onclick=()=>downloadSVG('reference-chart','futwar-reference-comparison.svg');
'''
s=s.replace("document.querySelectorAll('[data-view]')",extra+"\ndocument.querySelectorAll('[data-view]')",1)
s=s.replace("const labels={", "const labels={blocks_per90:'Blocks',recoveries_per90:'Recoveries',aerial_duels_won_per90:'Aerial duels won',aerial_duels_lost_per90:'Aerial duels lost',key_passes_per90:'Key passes',progressive_receptions_per90:'Progressive receptions',passes_into_box_per90:'Passes into the box',dispossessions_per90:'Dispossessions',miscontrols_per90:'Miscontrols',errors_per90:'Recorded errors',")
p.write_text(s,encoding='utf-8')
print('Installed three-mode recorded-metric comparison preview.')
