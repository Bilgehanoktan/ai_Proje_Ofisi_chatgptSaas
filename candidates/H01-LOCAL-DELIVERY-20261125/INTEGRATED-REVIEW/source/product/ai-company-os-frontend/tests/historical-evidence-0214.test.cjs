/** Run with node --test after compiling the exact parser slice to CommonJS.
 * AICOS_UI_BUILD: compiled directory; AICOS_UI_EVIDENCE: genuine backend fixture JSON directory.
 */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {historicalEvidence}=require(path.join(process.env.AICOS_UI_BUILD,'historicalEvidence.js'));
const load=name=>JSON.parse(fs.readFileSync(path.join(process.env.AICOS_UI_EVIDENCE,name+'.json'),'utf8'));
const terminal=load('terminal');
for(let v=1;v<=4;v++)test('actual backend prefix '+v,()=>{
 const e=historicalEvidence(load('prefix-'+v)); assert.ok(e);
 assert.equal(e.profile,'PREFIX_SAMPLE'); assert.equal(e.observed,v);
 assert.equal(e.slots.filter(x=>x.state!==null).length,v);
 assert.ok(e.slots.slice(v).every(x=>x.state===null&&x.kind===null));
 assert.equal(e.lease,'CURRENT_FRESHNESS_UNKNOWN');assert.equal(e.budget.kind,'OUTSTANDING_IN_SAMPLE');
 assert.equal(e.liveRunCount,null);assert.equal(e.placementAllowed,false);assert.equal(e.dispatchAllowed,false);
});
test('actual backend terminal snapshot',()=>{
 const e=historicalEvidence(terminal);assert.ok(e);assert.equal(e.profile,'TERMINAL_SAMPLE');
 assert.equal(e.observed,5);assert.equal(e.recordedState,'FAILED');assert.equal(e.lease,'CLOSED_IN_SAMPLE');
 assert.deepEqual(e.budget,{kind:'RELEASED_IN_SAMPLE',minor:20,currency:'USD'});
 assert.equal(e.join,'HOLD');assert.equal(e.independentAccepted,false);
});
for(const mutation of [{authoritative:true},{real_run_count:3},{dispatch_allowed:true},{geometry_join:'OK'},{state:'SUCCEEDED'},{freshness:'ACTIVE_VERIFIED'},{tenant:'another-tenant'}])test('reject forged historical data '+Object.keys(mutation)[0],()=>assert.equal(historicalEvidence({...terminal,...mutation}),null));
test('reject combined samples',()=>assert.equal(historicalEvidence({terminal,prefix:load('prefix-1')}),null));
test('reject missing or altered timeline',()=>{assert.equal(historicalEvidence(null),null);assert.equal(historicalEvidence({...terminal,timeline:terminal.timeline.slice(0,4)}),null);});
