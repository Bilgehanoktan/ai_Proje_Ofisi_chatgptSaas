const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const {parseOutboxProjection:parse}=require(process.argv[2]);
const cases=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
for(const c of cases)test(`shared vector: ${c.name}`,()=>assert.equal(parse(c.body)!==null,c.valid));
