const test=require('node:test'),assert=require('node:assert/strict');
const {readFileSync}=require('node:fs');
const {join}=require('node:path');
const {parseSharedReplay,readSharedText}=require(process.env.SHARED_HELPER_JS);
const sample=n=>readFileSync(join(process.env.SHARED_REPLAY_DIR,'replay-'+n+'.sse'),'utf8');
const frames=()=>sample(4).slice(0,-2).split('\n\n');
const pack=f=>f.join('\n\n')+'\n\n';
for(let n=1;n<=4;n++)test('Python replay '+n+' cross-language digest',async()=>{
 const s=await parseSharedReplay(sample(n));assert.equal(s.snapshot_seq,n);assert.equal(s.project_id,null);assert.equal(s.world_id,null);assert.equal(s.prefix.real_run_count,null);assert.equal(s.prefix.dispatch_allowed,false);
});
for(const [name,change] of [
 ['gap',f=>f.splice(2,1)],['duplicate',f=>f.splice(2,0,f[1])],['out of order',f=>[f[1],f[2]]=[f[2],f[1]]],
 ['wrong digest',f=>f[1]=f[1].replace(/"digest":"[0-9a-f]+"/,'"digest":"bad"')],
 ['wrong scope',f=>f[0]=f[0].replace('synthetic-tenant','other-tenant')],
 ['epoch drift',f=>f[0]=f[0].replace('"policy_epoch":2','"policy_epoch":3')],
 ['unproven project',f=>f[0]=f[0].replace('"project_id":null','"project_id":"p"')],
 ['missing complete',f=>f.pop()],['extra event',f=>f.push(f[1])],
 ['duplicate JSON key',f=>f[0]=f[0].replace('"project_id":null','"project_id":null,"project_id":null')],
 ['unexpected SSE field',f=>f[0]='id: 0\n'+f[0]],['wrong final sequence',f=>f[5]=f[5].replace('"sequence":4','"sequence":3')]
])test(name+' fails closed',async()=>{const f=frames();change(f);await assert.rejects(parseSharedReplay(pack(f)));});
test('incomplete framing fails',async()=>assert.rejects(parseSharedReplay(sample(4).slice(0,-1))));
const response=(body,type='text/event-stream')=>new Response(body,{headers:{'Content-Type':type}});
test('bounded body accepted',async()=>assert.equal(await readSharedText(response(sample(1)),new AbortController().signal),sample(1)));
test('wrong media type fails',async()=>assert.rejects(readSharedText(response(sample(1),'application/json'),new AbortController().signal)));
test('oversize fails',async()=>assert.rejects(readSharedText(response('x'.repeat(16385)),new AbortController().signal)));
test('invalid UTF8 fails',async()=>assert.rejects(readSharedText(response(Uint8Array.of(255)),new AbortController().signal)));
test('aborted read fails',async()=>{const c=new AbortController();c.abort();await assert.rejects(readSharedText(response(sample(1)),c.signal));});
