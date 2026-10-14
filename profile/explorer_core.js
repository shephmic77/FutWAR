(function(root){
'use strict';
function normalize(value){return String(value??'').toLowerCase().replace(/[ıøłđðæœ’]/g,c=>({'ı':'i','ø':'o','ł':'l','đ':'d','ð':'d','æ':'ae','œ':'oe','’':"'"}[c])).normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ').trim();}
const positionCodes=['GK','RB','RWB','CB','LB','LWB','CM','CDM','CAM','LM','RM','ST','LW','RW'];
function specificPosition(value){const code=String(value??'').trim().toUpperCase(),mapped=({DM:'CDM',AM:'CAM',CF:'ST',SS:'ST'})[code]||code;return positionCodes.includes(mapped)?mapped:'Unavailable';}
function buildGroups(records){
 const links=new Map(),key=r=>normalize(r.name)+'|'+(r.details.birth_year||'unknown:'+r.id);
 for(const r of records){const ids=links.get(key(r))||new Set();if(r.provider_player_id)ids.add(String(r.provider_player_id));links.set(key(r),ids);}
 const groups=new Map();
 for(const r of records){const ids=links.get(key(r));const pid=r.provider_player_id||(ids.size===1?[...ids][0]:null);r.group=pid?'provider:'+pid:'source:'+key(r);const rows=groups.get(r.group)||[];rows.push(r);groups.set(r.group,rows);}
 for(const rows of groups.values())rows.sort((a,b)=>a.season.localeCompare(b.season)||a.team.localeCompare(b.team));
 return groups;
}
function distance(a,b){let prev=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){const next=[i];for(let j=1;j<=b.length;j++)next[j]=Math.min(next[j-1]+1,prev[j]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));prev=next;}return prev[b.length];}
function searchGroups(groups,text){
 const query=normalize(text);if(!query)return {matches:[],suggested:false};
 const matches=[];
 for(const [id,rows] of groups){const hit=rows.some(r=>normalize(r.name+' '+r.team).includes(query));if(hit){const latest=rows.at(-1);matches.push({id,rows,latest,score:normalize(latest.name)===query?0:normalize(latest.name).includes(query)?1:2});}}
 let suggested=false;
 if(!matches.length&&query.length>=4){suggested=true;for(const [id,rows] of groups){const latest=rows.at(-1),tokens=normalize(latest.name).split(' ');const score=Math.min(distance(query,normalize(latest.name)),...tokens.map(t=>distance(query,t)));if(score<=(query.length>=7?2:1))matches.push({id,rows,latest,score});}}
 matches.sort((a,b)=>a.score-b.score||a.latest.name.localeCompare(b.latest.name));return {matches,suggested};
}
// One observed June-30-cutoff value per season; no current/peak/future backfill.
function seasonValues(rows){const bySeason=new Map();for(const r of rows){const v=r.market_value;if(!v)continue;const end=String(Number(r.season.slice(0,4))+1),cutoff=end+'-06-30';if(v.date>cutoff||v.date<r.season.slice(0,4)+'-07-01')continue;const old=bySeason.get(r.season);if(!old||v.date>old.date)bySeason.set(r.season,{...v,season:r.season,year:Number(end)});else if(v.date===old.date&&v.eur!==old.eur)throw Error('Conflicting market values in the same season');}return [...bySeason.values()].sort((a,b)=>a.year-b.year);}
const api={normalize,buildGroups,searchGroups,seasonValues,positionCodes,specificPosition};if(typeof module==='object'&&module.exports)module.exports=api;else root.FutwarCore=api;
})(typeof window==='object'?window:this);
