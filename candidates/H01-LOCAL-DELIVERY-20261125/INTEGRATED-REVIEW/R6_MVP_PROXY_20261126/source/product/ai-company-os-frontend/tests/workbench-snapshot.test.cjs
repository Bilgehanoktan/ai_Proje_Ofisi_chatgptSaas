const assert = require('node:assert/strict');
const {test} = require('node:test');
const {parseWorkbenchSnapshot:parse} = require(process.argv[2]);
const ids=['draft','iv','merge','plan','qa','release','research'], order=['plan','draft','research','merge','qa'];
function sample(n=5){return {mode:'D0_WORKBENCH_0182',tenant:'synthetic-tenant',company:'synthetic-company',plan_digest:'6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9',tasks:ids.map(id=>order.slice(0,n).includes(id)?[id,'OBSERVED',1]:[id,'PENDING',0]),events:order.slice(0,n).map((id,i)=>[i+1,id,1,i+1,'a'.repeat(64)]),admission:'DENY',dispatch_allowed:false,release_ready:false,provider_called:false,spend_allowed:false,independent_accepted:false};}
const check=x=>parse(JSON.stringify(x));
test('all CLI prefixes',()=>{for(let n=0;n<=5;n++)assert.equal(check(sample(n)).events,n);});
test('effect flag denied',()=>{for(const k of ['dispatch_allowed','release_ready','provider_called','spend_allowed','independent_accepted'])assert.equal(check({...sample(),[k]:true}),null);});
test('scope and digest',()=>{for(const k of ['tenant','company','plan_digest','mode'])assert.equal(check({...sample(),[k]:'other'}),null);});
test('event mismatch',()=>{const x=sample();x.events[0][1]='iv';assert.equal(check(x),null);});
test('state mismatch',()=>{const x=sample();x.tasks[1]=['iv','OBSERVED',1];assert.equal(check(x),null);});
test('extra field and invalid JSON',()=>{assert.equal(check({...sample(),extra:1}),null);assert.equal(parse('{'),null);assert.equal(parse(' '.repeat(20001)),null);});
