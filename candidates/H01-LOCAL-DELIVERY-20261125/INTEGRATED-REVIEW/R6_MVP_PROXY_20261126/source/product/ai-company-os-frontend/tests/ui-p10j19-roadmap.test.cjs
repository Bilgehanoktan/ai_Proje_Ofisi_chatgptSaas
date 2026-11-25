'use strict';
const assert=require('node:assert/strict'),test=require('node:test'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const file=path.join(__dirname,'../features/project-management/ProjectRoadmap.tsx');
const result=ts.transpileModule(fs.readFileSync(file,'utf8'),{fileName:file,compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},reportDiagnostics:true});
const jsx=(type,props)=>({type,props}),mod={exports:{}};
vm.runInNewContext(result.outputText,{exports:mod.exports,module:mod,require:id=>{if(id==='react/jsx-runtime')return {jsx,jsxs:jsx};if(id==='./ProjectRoadmap.module.css')return {};throw Error(id)}});
const {default:Roadmap,roadmapFacts}=mod.exports;
const task=(id,label,role)=>({id,label,role,state:'HOLD',run_id:null});
const groups=[[task('plan','Talebi ayrıştır','orchestrator')],[task('draft','Çıktı taslağı','engineer'),task('research','Kaynak incelemesi','research')],[task('merge','Taslağı birleştir','engineer')],[task('qa','Kalite incelemesi','qa')],[task('iv','Bağımsız doğrulama sınırı','independent-verifier')],[task('release','Yayın kapısı','human-authority')]];
const rows=groups.flatMap((g,i)=>g.map(task=>({task,wave:i+1}))),view={groups,rows,gates:rows.slice(-3),holdCount:7};
let selected=[];const render=(id='plan',v=view)=>Roadmap({view:v,selected:id,onSelect:id=>selected.push(id)});
function flatten(x,out=[]){if(Array.isArray(x)){for(const y of x)flatten(y,out)}else if(x&&typeof x==='object'){out.push(x);flatten(x.props?.children,out)}return out}
const nodes=(x,t)=>flatten(x).filter(n=>n.type===t);
function words(x){if(Array.isArray(x))return x.map(words).join(' ');if(x&&typeof x==='object')return words(x.props?.children);return typeof x==='string'||typeof x==='number'?String(x):''}
test('TSX syntax',()=>assert.equal(result.diagnostics.filter(d=>d.category===ts.DiagnosticCategory.Error).length,0));
test('six logical waves with only second parallel',()=>{const f=roadmapFacts(view);assert.equal(f.waves.length,6);assert.equal(f.parallelWaves,1);assert.equal(f.waves[1].parallel,true);assert.equal(f.waves[0].parallel,false)});
test('all seven reference tasks present in wave order',()=>assert.deepEqual(nodes(render(),'li').map(words).map(s=>s.match(/Dalga\s+\d/)[0].replace(/\s+/g,' ')),['Dalga 1','Dalga 2','Dalga 3','Dalga 4','Dalga 5','Dalga 6']));
test('actual completion and delivery unknown even when all HOLD',()=>assert.deepEqual(nodes(render(),'dd').map(words),['1','7 / 7','—','—']));
test('parallel tasks share wave',()=>assert.match(words(nodes(render(),'li')[1]),/Paralel plan.*Çıktı taslağı.*Kaynak incelemesi/));
test('three distinct gates with exact roles',()=>{const g=flatten(render()).find(n=>n.props?.['aria-label']==='Referans teslimat kapıları');assert.equal(nodes(g,'button').length,3);assert.match(words(g),/qa.*independent-verifier.*human-authority/)});
test('selection synchronized by prop including gate duplicate',()=>{const x=render('qa');assert.equal(nodes(x,'button').filter(n=>n.props['aria-pressed']).length,2);assert.ok(nodes(x,'button').filter(n=>n.props['aria-pressed']).every(n=>words(n).includes('Kalite incelemesi')))});
test('click delegates only task selection',()=>{selected=[];nodes(render(),'button')[2].props.onClick();assert.deepEqual(selected,['research'])});
test('unknown selection marks none',()=>assert.equal(nodes(render('missing'),'button').filter(n=>n.props['aria-pressed']).length,0));
test('no timing, progress, or acceptance inference',()=>{const s=words(render());assert.match(s,/kritik yol veya gerçekleşen ilerleme değildir/);assert.match(s,/Gerçek kabul, çıktı veya teslimat kanıtı yok/);assert.equal(nodes(render(),'progress').length,0)});
test('facts do not mutate reference input',()=>{const before=JSON.stringify(view);roadmapFacts(view);render();assert.equal(JSON.stringify(view),before)});
