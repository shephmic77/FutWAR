const assert=require('node:assert/strict');
const fs=require('node:fs');
const core=require('../profile/explorer_core.js');
const data=JSON.parse(fs.readFileSync('reports/explorer/data.json','utf8'));
const groups=core.buildGroups(data.records);
assert.equal([...groups.values()].flat().length,22418);
for(const query of ['Modric','modri','Yildiz','Pulisic','pulsic']){
 const result=core.searchGroups(groups,query);assert.ok(result.matches.length,query+' must be searchable');
 assert.equal(result.matches.filter(x=>core.normalize(x.latest.name).includes(query==='pulsic'?'pulisic':core.normalize(query))).length,1,query+' has one profile');
}
const modric=core.searchGroups(groups,'Modric').matches[0];
assert.equal(new Set(modric.rows.map(r=>r.season)).size,8);
assert.equal(new Set(data.records.map(r=>r.id)).size,22418);
assert.equal(core.searchGroups(groups,'pulsic').suggested,true);
const twins=[{id:'a',name:'Alex Smith',details:{birth_year:'1990'},provider_player_id:'1',season:'2020-21',team:'A'},{id:'b',name:'Alex Smith',details:{birth_year:'1990'},provider_player_id:'2',season:'2020-21',team:'B'}];
assert.equal(core.buildGroups(twins).size,2,'Different supported provider identities must not be merged by name alone');
const values=core.seasonValues(modric.rows);assert.equal(values.length,7,'Unlinked source season remains missing rather than filled from a different season');
assert.equal(values.at(-1).year,2025);assert.equal(values.at(-1).eur,4000000);
assert.equal(core.seasonValues([{season:'2024-25',market_value:{date:'2025-07-01',eur:999}}]).length,0);
assert.equal(core.seasonValues([{season:'2024-25',market_value:{date:'2025-06-30',eur:0}}])[0].eur,0);
for(const code of ['GK','RB','RWB','CB','LB','LWB','CM','CDM','CAM','LM','RM','ST','LW','RW'])assert.equal(core.specificPosition(code),code);
for(const broad of ['MF','DF','FW','MF,DF','FW,MF',''])assert.equal(core.specificPosition(broad),'Unavailable');
assert.equal(core.specificPosition('DM'),'CDM');assert.equal(core.specificPosition('AM'),'CAM');
assert.equal(core.specificPosition('CF'),'ST');assert.equal(core.specificPosition('SS'),'ST');
for(const r of data.records)assert.ok([...core.positionCodes,'Unavailable'].includes(core.specificPosition(r.display_role||r.position)));
console.log('Passed: complete record coverage, five search regressions, one eight-season Modric profile, homonym protection, annual values and cutoff boundaries.');
