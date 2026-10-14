from pathlib import Path
p=Path('profile/explorer.js');s=p.read_text(encoding='utf-8')
start=s.index('function axes(');end=s.index('\nfunction ',start+1)
s=s[:start]+'''function axes(f,xmin,xmax,ymin,ymax,formatX,formatY,xTicks=null){
 const {w,h,L,R,T,B}=f,dx=xmax-xmin||1,dy=ymax-ymin||1,x=v=>L+(v-xmin)/dx*(w-L-R),y=v=>h-B-(v-ymin)/dy*(h-T-B);
 let html=`<path class="axis" fill="none" d="M${L} ${T}V${h-B}H${w-R}"/>`;
 const ticks=xTicks||Array.from({length:4},(_,i)=>xmin+dx*i/3);
 ticks.forEach((v,i)=>{html+=`<text x="${x(v)}" y="${h-B+25}" text-anchor="${i===0?'start':i===ticks.length-1?'end':'middle'}">${esc(formatX(v))}</text>`;});
 for(let i=0;i<4;i++){const v=ymin+dy*i/3;html+=`<text x="${L-12}" y="${y(v)+5}" text-anchor="end">${esc(formatY(v))}</text>`;}
 html+=`<text x="${L}" y="23">${esc(f.ylabel)}</text><text x="${(w+L-R)/2}" y="${h-8}" text-anchor="middle">${esc(f.xlabel)}</text>`;return {x,y,html};
}
'''+s[end:]
s=s.replace("const a=axes(f,lo-.2,hi+.2,0,max*1.12,v=>String(Math.round(v)),euro);","const years=[...new Set(history().map(r=>Number(r.season.slice(0,4))+1))].sort();\n const a=axes(f,Math.min(...years)-.2,Math.max(...years)+.2,0,max*1.12,v=>String(v),euro,years);")
s=s.replace("values.map(v=>`${a.x(v.year)} ${a.y(v.eur)}`).join('L')","values.map((v,i)=>`${i===0||v.year-values[i-1].year>1?'M':'L'}${a.x(v.year)} ${a.y(v.eur)}`).join(' ')")
s=s.replace('d="M${values.map((v,i)', 'd="${values.map((v,i)')
s=s.replace('const vh=rows.flatMap(r=>r.valuation_history);','const vh=history().flatMap(r=>r.valuation_history);')
p.write_text(s,encoding='utf-8')
