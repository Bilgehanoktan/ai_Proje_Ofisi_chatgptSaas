'use strict';
const {test,afterEach}=require('node:test'),assert=require('node:assert/strict');
const {createProjectionReader}=require(process.argv[2]);
const stale={phase:'hold',data:null,reason:'STALE'};
const parse=x=>x?.mode==='D0'&&x.allowed===false?x:null;
const good=()=>Response.json({mode:'D0',allowed:false});
let reader;
afterEach(()=>{reader?.cancel();reader=undefined;delete global.document;});
function setup(hidden,transport,parser=parse){
 global.document={hidden};const states=[];
 reader=createProjectionReader('plan',parser,s=>states.push(s),transport,400,40);
 return states;
}
test('hidden before read: no transport, STALE/HOLD',async()=>{
 let calls=0;const s=setup(true,async()=>{calls++;return good()});await reader.read();
 assert.deepEqual({calls,last:s.at(-1)},{calls:0,last:stale});
});
test('late body after hidden, before event callback: no historical publication',async()=>{
 let resolve;const s=setup(false,()=>new Promise(r=>resolve=r));const p=reader.read();
 document.hidden=true;resolve(good());await p;
 assert.deepEqual(s,[{phase:'loading',data:null},stale]);
});
test('hidden during parser: validated data must not become historical',async()=>{
 const s=setup(false,async()=>good(),x=>{document.hidden=true;return parse(x)});await reader.read();
 assert.deepEqual(s,[{phase:'loading',data:null},stale]);
});
test('hidden refresh of existing history clears data without second transport',async()=>{
 let calls=0;const s=setup(false,async()=>{calls++;return good()});await reader.read();assert.equal(s.at(-1).phase,'historical');
 document.hidden=true;await reader.read();assert.deepEqual({calls,last:s.at(-1)},{calls:1,last:stale});
});
test('explicit visible reread after HOLD works; no auto-read or grant',async()=>{
 let calls=0;const s=setup(false,async()=>{calls++;return good()});await reader.read();reader.invalidate();
 assert.deepEqual(s.at(-1),stale);assert.equal(calls,1);await reader.read();assert.equal(calls,2);assert.equal(s.at(-1).phase,'historical');assert.equal(s.at(-1).data.allowed,false);
});
