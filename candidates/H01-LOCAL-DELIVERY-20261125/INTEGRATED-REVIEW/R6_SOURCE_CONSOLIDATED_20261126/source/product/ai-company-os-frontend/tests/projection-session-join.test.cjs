const test=require('node:test'),assert=require('node:assert/strict');
const {sessionReadState}=require(process.argv[2]),{inspectHistoricalJoin}=require(process.argv[3]);
const owner={},second={},third={},entry={owner,state:{phase:'historical',data:{example:1}}};
test('same reader retains result',()=>assert.equal(sessionReadState(owner,entry),entry.state));
test('new reader discards old result',()=>assert.deepEqual(sessionReadState(second,entry),{phase:'idle',data:null}));
test('A B A cannot revive old A',()=>assert.deepEqual(sessionReadState(third,entry),{phase:'idle',data:null}));
test('no entry is idle',()=>assert.deepEqual(sessionReadState(owner,null),{phase:'idle',data:null}));
const rev='sha256:'+'a'.repeat(64),sample={tenant:'t',company:'c',environment:'e',plan_revision:rev,task_id:'task',run_id:'run',freshness:'HISTORICAL_SAMPLE'};
const plan=()=>({scope:{tenant_id:'t',environment_id:'e',company_id:'c'},revision:rev,tasks:[{id:'task',run_id:'run'}]});
const hold=(p,reason)=>assert.deepEqual(inspectHistoricalJoin(p,sample),{decision:'HOLD',reason,join_allowed:false});
test('matching IDs never authorize historical join',()=>hold(plan(),'HISTORICAL_ONLY'));
for(const [name,mutate,reason] of [
 ['tenant',p=>p.scope.tenant_id='wrong','SCOPE_MISMATCH'],['environment',p=>p.scope.environment_id='wrong','SCOPE_MISMATCH'],['company',p=>p.scope.company_id='wrong','SCOPE_MISMATCH'],['revision',p=>p.revision='sha256:'+'b'.repeat(64),'PLAN_REVISION_MISMATCH'],['task missing',p=>p.tasks=[],'TASK_MISSING_OR_DUPLICATE'],['task duplicate',p=>p.tasks.push(p.tasks[0]),'TASK_MISSING_OR_DUPLICATE'],['missing company',p=>delete p.scope.company_id,'COMPANY_SCOPE_MISSING'],['null run',p=>p.tasks[0].run_id=null,'RUN_BINDING_MISSING_OR_MISMATCH'],['wrong run',p=>p.tasks[0].run_id='wrong','RUN_BINDING_MISSING_OR_MISMATCH']])test(name+' fails closed',()=>{const p=plan();mutate(p);hold(p,reason)});
