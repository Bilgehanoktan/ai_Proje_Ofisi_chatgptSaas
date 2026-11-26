const test=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const {ceoSections,workSections,isSection}=require(path.join(process.env.P10D_MODEL,'sectionModel.js'));
test('CEO defaults to summary, work defaults to projects',()=>{assert.equal(ceoSections[0].id,'summary');assert.equal(workSections[0].id,'projects');});
test('each view has exactly three distinct sections',()=>{for(const s of [ceoSections,workSections]){assert.equal(s.length,3);assert.equal(new Set(s.map(x=>x.id)).size,3);assert.ok(s.every(x=>x.label&&x.description));}});
test('all local IDs accepted in own view',()=>{for(const s of [ceoSections,workSections])for(const x of s)assert.equal(isSection(s,x.id),true);});
test('cross-view and invalid values rejected',()=>{for(const x of ['projects','audit','workflow','__proto__',null,{},1])assert.equal(isSection(ceoSections,x),false);for(const x of ['summary','operations','evidence','constructor',undefined])assert.equal(isSection(workSections,x),false);});
