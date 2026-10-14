from pathlib import Path
p=Path('profile/explorer.js')
s=p.read_text(encoding='utf-8')
start=s.index('function photograph(')
end=s.index('\nfunction crest(',start)
s=s[:start]+'''function photograph(r,tiny=false){
 const a=asset('action',r.name)||asset('portrait',r.name),remote=r.profile_portrait;
 const url=a?.data_url||remote?.url;
 return url?`<img class="${tiny?'tiny-photo':'photo'} ${a?.kind==='action'?'':'portrait'}" src="${esc(url)}" alt="${esc(r.name)} ${a?.kind==='action'?'match photo':'portrait'}" data-player-photo="${esc(r.name)}" data-tiny="${tiny}" loading="lazy" referrerpolicy="no-referrer">`:`<div class="${tiny?'tiny-initials':'initials'}" aria-label="Player photo unavailable">${esc(initials(r.name))}</div>`;
}
document.addEventListener('error',event=>{const img=event.target;if(!(img instanceof HTMLImageElement)||!img.dataset.playerPhoto)return;const fallback=document.createElement('div');fallback.className=img.dataset.tiny==='true'?'tiny-initials':'initials';fallback.setAttribute('aria-label','Player photo unavailable');fallback.title='The source photograph could not be loaded.';fallback.textContent=initials(img.dataset.playerPhoto);img.replaceWith(fallback);},true);
''' + s[end:]
s=s.replace('${fmt(d.appearances,0)} appearances in ${esc(r.season)}','${fmt(d.appearances,0)} appearances')
s=s.replace('<p class="small" style="margin-top:12px;margin-bottom:0">${esc(periodText(selectedRows()))} · Profile role; seasonal role minutes unvalidated.</p>','')
needle=" const images=data.images.filter"
assert needle in s
s=s.replace(needle,""" if(r.profile_portrait)$('player-evidence').insertAdjacentHTML('beforeend',`<h3>Player portrait</h3><p><a href="${esc(r.profile_portrait.source_page)}" target="_blank" rel="noreferrer">Transfermarkt player profile</a> · Portrait URL recorded in the hashed publisher archive. Profile identity remains provisional. The image may be current and is not evidence of the selected season's kit or role. Remote images require internet access; image rights remain with their owners.</p>`);
 const images=data.images.filter""")
p.write_text(s,encoding='utf-8')
