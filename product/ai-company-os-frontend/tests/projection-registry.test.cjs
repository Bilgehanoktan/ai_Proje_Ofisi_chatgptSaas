const test=require('node:test'),assert=require('node:assert/strict');
const {registeredReader,projectionParsers}=require(process.argv[2]);
const {expectedLifecycle}=require(process.argv[3]);
test('registry fixed seven endpoint parsers',()=>assert.deepEqual(Object.keys(projectionParsers).sort(),['admission','lifecycle','lifecycle-prefix','mvp','office-workbench','outbox','task-budget']));
test('registry frozen',()=>assert.equal(Object.isFrozen(projectionParsers),true));
test('lifecycle accepts only its exact response',async()=>{const states=[];const r=registeredReader('lifecycle',s=>states.push(s),async(url,init)=>{assert.equal(url,'/api/demo/lifecycle');assert.equal(init.method,'GET');return Response.json(expectedLifecycle)});await r.read();assert.equal(states.at(-1).phase,'historical')});
for(const key of ['mvp','admission','outbox','office-workbench','task-budget','lifecycle-prefix'])test(key+' rejects lifecycle wire envelope',async()=>{const states=[];await registeredReader(key,s=>states.push(s),async()=>Response.json(expectedLifecycle)).read();assert.equal(states.at(-1).phase,'hold');assert.equal(states.at(-1).data,null)});
test('lifecycle rejects mismatched projection and clears data',async()=>{const states=[];let n=0;const r=registeredReader('lifecycle',s=>states.push(s),async()=>Response.json(n++?{mode:'D0'}:expectedLifecycle));await r.read();assert.equal(states.at(-1).phase,'historical');await r.read();assert.equal(states.at(-1).phase,'hold');assert.equal(states.at(-1).data,null)});
test('unknown registry key never starts transport',()=>assert.throws(()=>registeredReader('__proto__',()=>{},()=>assert.fail('unexpected transport')),/REGISTRY_HOLD/));
