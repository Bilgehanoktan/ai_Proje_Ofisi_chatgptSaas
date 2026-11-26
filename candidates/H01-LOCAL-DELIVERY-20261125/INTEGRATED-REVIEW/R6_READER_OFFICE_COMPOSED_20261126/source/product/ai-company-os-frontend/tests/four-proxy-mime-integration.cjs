'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {resolve}=require('node:path'),fs=require('node:fs'),vm=require('node:vm');
// Reuse exact original fixture declarations; do not load original test registrations.
const original=fs.readFileSync(resolve(__dirname,'d0-proxy-deadline.test.cjs'),'utf8');
const start=original.indexOf("const plan = "),end=original.indexOf('async function mockRun');
assert.ok(start>=0&&end>start);
const specs=vm.runInNewContext(original.slice(start,end)+';[...specs,{name:"office-workbench",body:office,hold:"D0_OFFICE_WORKBENCH_HOLD"}]');
for(const s of specs){
 const {GET}=require(resolve(process.argv[2],`app/api/demo/${s.name}/route.js`));
 for(const [label,mime,want] of [
 ['valid-json','application/json',200],
 ['valid-quoted-utf8','Application/JSON; charset="UTF-8"',200],
 ['coalesced-header','application/json; charset=UTF-8, text/html',503],
 ['duplicate-json','application/json; charset=UTF-8, application/json',503],
 ['duplicate-charset','application/json; charset=UTF-8; charset=UTF-8',503],
 ])test(`${s.name}: ${label}`,async()=>{
  const old=global.fetch;
  try{global.fetch=async()=>new Response(JSON.stringify(s.body),{headers:{'content-type':mime}});
   const r=await GET();assert.equal(r.status,want);assert.equal(r.headers.get('cache-control'),'no-store');
   if(want===503)assert.equal((await r.json()).mode,s.hold);else assert.deepEqual(await r.json(),JSON.parse(JSON.stringify(s.body)));
  }finally{global.fetch=old}
 });
}
