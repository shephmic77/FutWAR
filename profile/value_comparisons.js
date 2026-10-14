/* Recorded-metric references for research UI; not a contribution estimator. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory(require('./explorer_core.js'));else root.FutwarReferences=factory(root.FutwarCore);})(typeof globalThis!=='undefined'?globalThis:this,function(core){
 'use strict';
 function minutes(r){return r.domain==='GK'?r.keeper?.minutes:r.minutes;}
 function measurements(r,k){const source=r.domain==='GK'?r.keeper:r;return {rate:source?.metrics?.[k],total:source?.totals?.[k]};}
 function pooled(rows,k){
  const valid=rows.filter(r=>Number.isFinite(measurements(r,k).rate)&&minutes(r)>0);
  const exposure=valid.reduce((s,r)=>s+minutes(r),0);
  if(!exposure)return {rate:null,minutes:0};
  if(k==='crosses_stopped_share'){
   const pairs=valid.filter(r=>r.keeper?.crosses?.faced>0&&Number.isFinite(r.keeper?.crosses?.stopped));
   const faced=pairs.reduce((s,r)=>s+r.keeper.crosses.faced,0);
   return {rate:faced?pairs.reduce((s,r)=>s+r.keeper.crosses.stopped,0)/faced:null,minutes:exposure};
  }
  if(valid.some(r=>!Number.isFinite(measurements(r,k).total)))return {rate:null,minutes:exposure};
  return {rate:90*valid.reduce((s,r)=>s+measurements(r,k).total,0)/exposure,minutes:exposure};
 }
 function majorityRole(rows){
  const counts=new Map();for(const r of rows){const p=core.specificPosition(r.display_role);if(p!=='Unavailable')counts.set(p,(counts.get(p)||0)+(minutes(r)||0));}
  const ordered=[...counts].sort((a,b)=>b[1]-a[1]);return !ordered.length||(ordered[1]&&ordered[0][1]===ordered[1][1])?'Unavailable':ordered[0][0];
 }
 function reference(records,selected,season,k,league=null,minimum=900){
  if(!(minimum>0))throw Error('Positive reference exposure required');
  const selectedRole=core.specificPosition(selected.display_role);
  if(selectedRole==='Unavailable')return {rate:null,players:0,status:'Specific position unavailable'};
  const groups=new Map();let unknown=0;
  for(const r of records){if(r.season!==season||r.domain!==selected.domain||(league&&r.league!==league)||r.id===selected.id||(selected.group&&r.group===selected.group))continue;
   const key=r.group||r.id;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r);}
  const values=[];let below=0;
  for(const rows of groups.values()){
   const p=majorityRole(rows);if(p==='Unavailable'){unknown++;continue;}if(p!==selectedRole)continue;
   const value=pooled(rows,k);if(value.minutes<minimum){below++;continue;}if(Number.isFinite(value.rate))values.push(value.rate);
  }
  return {rate:values.length?values.reduce((s,v)=>s+v,0)/values.length:null,players:values.length,belowMinimum:below,unknownRoles:unknown,
   status:values.length?'Raw recorded-metric average; provisional identity/role groups; no league-strength adjustment':'No usable reference pool'};
 }
 return {reference,pooled,majorityRole};
});
