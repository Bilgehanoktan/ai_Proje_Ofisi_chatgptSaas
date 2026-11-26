const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const out=process.env.AICOS_STUDIO_OUT;
const {parsePlanProjection,readPlanProjection}=require(path.join(out,'features/core-review/planProjection.js'));
const {reviewStudioEvidence,rolePlanTasks}=require(path.join(out,'features/mvp/studioContext.js'));
const {parseSharedReplay}=require(path.join(out,'features/data/sharedSnapshot.js'));
const plan=JSON.parse(fs.readFileSync(process.env.AICOS_PLAN_JSON,'utf8'));
const clone=()=>JSON.parse(JSON.stringify(plan));
const selection={kind:'task',id:'research'};
const sample=()=>parseSharedReplay(fs.readFileSync(process.env.AICOS_REPLAY,'utf8'));
test('exact pinned plan accepted and DAG preserved',()=>{assert.deepEqual(parsePlanProjection(plan),plan);const p=readPlanProjection(plan);assert.equal(p.ok,true);assert.equal(p.groups.length,6);assert.equal(p.plan.tasks.length,7);assert.equal(p.plan.edges.length,7)});
for(const [name,mutate] of [
 ['scope',p=>p.scope.tenant_id='other'],['revision',p=>p.revision='sha256:'+'a'.repeat(64)],['unknown root field',p=>p.company_id='fake'],
 ['unknown nested field',p=>p.tasks[0].agent='fake'],['run assignment',p=>p.tasks[0].run_id='demo-a'],['task state',p=>p.tasks[0].state='RUNNING'],
 ['task role',p=>p.tasks[0].role='qa'],['edge',p=>p.edges[0].from='research'],['wave',p=>p.waves.reverse()],
 ['authority',p=>p.dispatch_allowed=true],['task duplicate',p=>p.tasks.push(p.tasks[0])],['missing property',p=>delete p.scope]
])test(name+' rejected',()=>{const p=clone();mutate(p);assert.equal(parsePlanProjection(p),null)});
test('malformed shapes rejected',()=>{for(const x of [null,[],true,{},'plan'])assert.equal(parsePlanProjection(x),null)});
test('role tasks use exact role identity',()=>{assert.deepEqual(rolePlanTasks(plan.tasks,'engineer').map(t=>t.id),['draft','merge']);assert.deepEqual(rolePlanTasks(plan.tasks,'Engineer'),[])});
test('human and IV remain separate gate roles',()=>{assert.deepEqual(rolePlanTasks(plan.tasks,'qa').map(t=>t.id),['qa']);assert.deepEqual(rolePlanTasks(plan.tasks,'independent-verifier').map(t=>t.id),['iv'])});
test('actual 0222 replay is incompatible with Research DAG',async()=>{const s=await sample(),r=reviewStudioEvidence(plan,selection,s);assert.equal(r.reason,'PLAN_REVISION_MISMATCH');assert.equal(r.joinAllowed,false);assert.equal(r.assignment,null);assert.equal(r.observation.taskId,'a');assert.equal(r.observation.runId,'demo-a');assert.equal(r.observation.timeline.length,s.snapshot_seq)});
test('role selection does not assign historical agent',async()=>{const s=await sample(),r=reviewStudioEvidence(plan,{kind:'role',id:'engineer'},s);assert.equal(r.assignment,null);assert.equal(r.dispatchAllowed,false);assert.equal(r.placementAllowed,false);assert.equal(r.observation.agentRef,'demo-agent')});
test('matching identity still cannot join',async()=>{const s=await sample(),p=s.prefix;const q={scope:{tenant_id:p.tenant,environment_id:p.environment,company_id:p.company},revision:p.plan_revision,tasks:[{id:p.task_id,run_id:p.run_id}]};const r=reviewStudioEvidence(q,{kind:'task',id:p.task_id},s);assert.equal(r.reason,'HISTORICAL_ONLY');assert.equal(r.joinAllowed,false);assert.equal(r.assignment,null)});
test('lost session clears observation',()=>{const r=reviewStudioEvidence(plan,selection,null);assert.equal(r.observation,null);assert.equal(r.reason,'NO_VERIFIED_SESSION')});
test('unknown project rejected',async()=>{const s=await sample();assert.equal(reviewStudioEvidence(plan,selection,{...s,project_id:'invented'}).observation,null)});
test('wrong sequence rejected',async()=>{const s=await sample();assert.equal(reviewStudioEvidence(plan,selection,{...s,snapshot_seq:99}).observation,null)});
test('no plan never claims binding',async()=>{const r=reviewStudioEvidence(null,selection,await sample());assert.equal(r.reason,'PLAN_UNAVAILABLE');assert.equal(r.assignment,null)});
