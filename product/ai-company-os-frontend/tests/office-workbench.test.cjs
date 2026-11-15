const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const {parseOfficeWorkbench:parse}=require(process.argv[2]);
const {GET}=require(process.argv[3]);
const cases=JSON.parse(fs.readFileSync(process.argv[4],'utf8'));
for(const c of cases)test(c.name,()=>assert.equal(parse(c.body)!==null,c.valid));
async function mock(fn,check){const old=global.fetch;global.fetch=fn;try{await check(await GET());}finally{global.fetch=old;}}
test('fixed loopback GET',async()=>mock(async(url,opts)=>{assert.equal(url,'http://127.0.0.1:8000/demo/v1/office/workbench-projection');assert.equal(opts.method,'GET');assert.equal(opts.redirect,'error');return Response.json(cases[5].body);},async r=>{assert.equal(r.status,200);assert.equal(r.headers.get('cache-control'),'no-store');assert.deepEqual(await r.json(),cases[5].body);}));
test('bad response HOLD',async()=>mock(async()=>Response.json(cases[6].body),async r=>assert.equal(r.status,503)));
test('oversize HOLD',async()=>mock(async()=>Response.json({x:'a'.repeat(5000)}),async r=>assert.equal(r.status,503)));
test('network failure HOLD',async()=>mock(async()=>{throw Error('down');},async r=>assert.equal(r.status,503)));
