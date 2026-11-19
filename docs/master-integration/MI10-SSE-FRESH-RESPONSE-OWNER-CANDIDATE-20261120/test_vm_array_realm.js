'use strict';
const assert=require('node:assert/strict');
const vm=require('node:vm');
const context=vm.createContext({});
const records=vm.runInContext('[{sequence:1},{sequence:2},{sequence:3}]',context);
let rejection='';
try{assert.deepStrictEqual(records.map(x=>x.sequence),[1,2,3]);}
catch(e){rejection=e.code;}
assert.equal(rejection,'ERR_ASSERTION');
console.log('PASS 1: strict array comparison rejects identical cross-realm prototype values');
assert.deepStrictEqual(Array.from(records,x=>x.sequence),[1,2,3]);
console.log('PASS 2: host-realm Array.from normalizes prototype and still compares all three sequences');
assert.equal(records.map(x=>x.sequence).join(','),'1,2,3');
console.log('PASS 3: original record contents were correct; failure is realm identity, not sequence values');
const changed=vm.runInContext('[{sequence:1},{sequence:3},{sequence:2}]',context);
assert.throws(()=>assert.deepStrictEqual(Array.from(changed,x=>x.sequence),[1,2,3]),{code:'ERR_ASSERTION'});
console.log('PASS 4: normalized comparison still catches non-monotonic sequence');
console.log('RESULT 4/4 PASS — no actual browser/API or production module executed');
