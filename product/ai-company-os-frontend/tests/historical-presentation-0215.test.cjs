/** 0215 static reference fixture tests, NOT backend readback or browser. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const build=process.env.AICOS_UI_BUILD;
const {historicalPresentation}=require(path.join(build,'historicalPresentation.js'));
const {expectedLifecycle:t}=require(path.join(build,'lifecycleProjection.js'));
const prefix=(v)=>{const {schema_version,mode,lease_active,sample_reserved_minor,sample_released_minor,lease_version,heartbeat_revision,sample_budget_revision,causality,...keep}=t;
 return {...keep,schema_version:'lifecycle.prefix.v1-D0',mode:'D0_0196L_HISTORICAL_PREFIX',agent_instance_id:'demo-agent',principal_id:'demo-principal',lease_present:true,fence:1,policy_epoch:2,witness_epoch:3,sample_outstanding_minor:20,lease_freshness:'UNKNOWN',causality:'EXACT_FIXED_PREFIX_ONLY',model_binding:'HOLD',memory_acl:'HOLD',head_version:v,state:t.timeline[v-1].state,timeline:t.timeline.slice(0,v),lease_version:v>=3?2:1,heartbeat_revision:v>=3?1:0,heartbeat_tick:v>=3?11:10,expires_tick:v>=3?31:20,sample_budget_revision:v>=3?2:1};};
test('terminal provenance and budget',()=>{const p=historicalPresentation(t);assert.ok(p);assert.equal(p.sampleIdentity,'D0_LIFECYCLE_0196L_TERMINAL_FIXTURE / demo-a / v5');assert.equal(p.scope,'synthetic-tenant / synthetic-company / A0_SAMPLE_ONLY');assert.equal(p.revision,t.plan_revision);assert.equal(p.task,'a');assert.equal(p.budgetValue,'20 minor USD');assert.match(p.budgetLabel,/serbest/);assert.equal(p.leaseLabel,'Örnek lease kapandı');});
for(let v=1;v<=4;v++)test('prefix provenance '+v,()=>{const p=historicalPresentation(prefix(v));assert.ok(p);assert.equal(p.sampleIdentity,`D0_0196L_HISTORICAL_PREFIX / demo-a / v${v}`);assert.equal(p.recordLabel,`${v}/5 kayıt adımı`);assert.match(p.budgetLabel,/açık/);assert.equal(p.leaseLabel,'Güncel lease bilinmiyor');assert.ok(p.evidence.slots.slice(v).every(s=>s.state===null));});
test('no live count placement release or independent authority',()=>{for(const raw of [t,prefix(4)]){const p=historicalPresentation(raw);assert.equal(p.liveLabel,'CANLI VERİ DEĞİL');assert.equal(p.runCountLabel,'Bilinmiyor');assert.equal(p.placementLabel,'HOLD');assert.equal(p.releaseLabel,'HOLD');assert.equal(p.independentLabel,'HOLD');assert.equal(p.evidence.dispatchAllowed,false);}});
for(const change of [{company:'wrong'},{tenant:'wrong'},{environment:'live'},{plan_revision:'sha256:'+'0'.repeat(64)},{freshness:'ACTIVE_VERIFIED'},{real_run_count:1},{authoritative:true},{dispatch_allowed:true},{release_ready:true}])test('forged field '+Object.keys(change)[0],()=>assert.equal(historicalPresentation({...t,...change}),null));
test('combined samples fail closed',()=>assert.equal(historicalPresentation({terminal:t,prefix:prefix(4)}),null));
test('missing sample fails closed',()=>assert.equal(historicalPresentation(null),null));
