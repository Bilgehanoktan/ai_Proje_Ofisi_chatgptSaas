const test=require('node:test'),assert=require('node:assert/strict');
const {parseLifecycleProjection,expectedLifecycle}=require(process.argv[2]);
const clone=()=>JSON.parse(JSON.stringify(expectedLifecycle));
test('fixed sample matches',()=>assert.deepEqual(parseLifecycleProjection(clone()),expectedLifecycle));
for(const [name,change] of [
 ['wrong scope',x=>x.tenant='other'],['wrong revision',x=>x.plan_revision='sha256:wrong'],
 ['live authority',x=>x.authoritative=true],['provider',x=>x.provider_called=true],
 ['actual run count',x=>x.real_run_count=0],['wrong settlement',x=>x.sample_released_minor=19],
 ['gap',x=>x.timeline.splice(1,1)],['reorder',x=>x.timeline.reverse()],
 ['wrong head',x=>x.state='RUNNING'],['extra key',x=>x.extra=1],
 ['lease active',x=>x.lease_active=true],['geometry join',x=>x.geometry_join='PASS']
])test(name,()=>{const x=clone();change(x);assert.equal(parseLifecycleProjection(x),null)});
test('nonobject',()=>assert.equal(parseLifecycleProjection(null),null));
test('exported expected envelope deep frozen',()=>{assert(Object.isFrozen(expectedLifecycle));assert(Object.isFrozen(expectedLifecycle.timeline));assert(Object.isFrozen(expectedLifecycle.timeline[0]))});
test('parsed envelope isolated from canonical expected and other consumers',()=>{const a=parseLifecycleProjection(clone());a.timeline[0].state='FORGED';a.authoritative=true;assert.equal(expectedLifecycle.timeline[0].state,'ADMITTED');assert.equal(parseLifecycleProjection(clone()).authoritative,false);assert.equal(parseLifecycleProjection(a),null)});
