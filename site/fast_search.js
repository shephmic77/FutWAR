'use strict';
(async function(){
const $=id=>document.getElementById(id),forms=['global-search','home-search'].map(id=>$(id));
const normalize=FutwarCore.normalize;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function open(record){
 if(window.futwarOpenRecord){window.futwarOpenRecord(record.id);return;}
 window.futwarPendingRecord=record.id;
 $('dataset-status').textContent=`Opening ${record.name}; finishing the player profile download…`;
}
function render(text){
 const query=normalize(text),box=$('search-results');if(!query){box.hidden=true;return;}
 const {matches,suggested}=FutwarCore.searchGroups(groups,text);box.hidden=false;box.replaceChildren();
 for(const hit of matches.slice(0,40)){
  const button=document.createElement('button');button.type='button';button.className='search-hit';
  button.innerHTML=`<span><strong>${esc(hit.latest.name)}</strong><small> · ${esc(hit.latest.team)}</small></span><small>${new Set(hit.rows.map(r=>r.season)).size} seasons · ${esc(hit.latest.display_role||hit.latest.position||'Position unavailable')}</small>`;
  button.addEventListener('click',()=>open(hit.latest));box.append(button);
 }
 const note=document.createElement('p');note.className='small';note.textContent=matches.length?`${suggested?'Suggested spelling matches':'Players found'}: ${matches.length}${matches.length>40?' · Refine your search for more results':''}`:'No source record found. Try a surname or club.';box.append(note);
}
try{
 const response=await fetch('futwar-search.json.gz');if(!response.ok)throw Error('Search index request failed ('+response.status+')');
 const payload=JSON.parse(await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).text());
 const groups=new Map(payload.groups.map(group=>[group.id,group.rows]));
 if(window.futwarReady)return;
 $('dataset-status').textContent='Player search is ready; full season statistics are loading in the background.';
 for(const form of forms){const input=form.querySelector('input');form.addEventListener('submit',event=>{event.preventDefault();render(input.value);});input.addEventListener('input',()=>input.value.trim()?render(input.value):$('search-results').hidden=true);if(input.value.trim())render(input.value);}
}catch(error){if(!window.futwarReady)$('dataset-status').textContent='Search directory unavailable; the full library is still loading. You can try again after it finishes.';}
})();
