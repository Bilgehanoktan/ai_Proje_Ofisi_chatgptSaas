'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const file=path.join(__dirname,'../features/ceo-dashboard/OperationalReadback.tsx');
const compiled=ts.transpileModule(fs.readFileSync(file,'utf8'),{fileName:file,compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},reportDiagnostics:true});
const jsx=(type,props)=>({type,props});let current,key,reads=0,resets=0;
const modules={'react/jsx-runtime':{jsx,jsxs:jsx},'../data/useProjectionRead':{useProjectionRead:k=>{key=k;return {state:current,data:current.data,read:()=>reads++,reset:()=>resets++}}},'../data/projectionRead':{readStatus:(s,l)=>s.reason==='TIMEOUT'?'Okuma zaman aşımı · HOLD':l[s.phase]},'./OperationalReadback.module.css':{details:'details',card:'card',rows:'rows',row:'row',budget:'budget',hold:'hold',source:'source'}};
const mod={exports:{}};vm.runInNewContext(compiled.outputText,{exports:mod.exports,module:mod,require:id=>{assert.ok(Object.hasOwn(modules,id));return modules[id]}});
const roles=[['orchestrator',1,1],['research',1,1],['engineer',1,2],['qa',0,1]].map(([role,observed,total])=>({role,station_id:'station-'+role,observed,total}));
const sample={pair_id:'a'.repeat(32),research_event_seq:3,office:{sample_event_count:3,roles},budget:{phase:'UNKNOWN_HOLD',version:2,sample_reserved_minor:100,sample_observed_minor:0,sample_remaining_minor:900}};
const render=(phase,data=null,reason)=>{current={phase,data,reason};return mod.exports.default()};
function flatten(x,out=[]){if(Array.isArray(x)){for(const y of x)flatten(y,out)}else if(x&&typeof x==='object'){out.push(x);flatten(x.props?.children,out)}return out}
function nodes(x,t){return flatten(x).filter(n=>n.type===t)}
function words(x){if(Array.isArray(x))return x.map(words).join(' ');if(x&&typeof x==='object')return words(x.props?.children);return typeof x==='string'||typeof x==='number'?String(x):''}
function button(x,name){return nodes(x,'button').find(n=>words(n)===name)}
test('TSX syntax and fixed endpoint',()=>{assert.equal(compiled.diagnostics.filter(d=>d.category===ts.DiagnosticCategory.Error).length,0);render('idle');assert.equal(key,'task-budget')});
test('idle has unknown KPI and no invented chart or money',()=>{const x=render('idle');assert.equal(nodes(x,'meter').length,0);assert.equal(nodes(x,'dd').length,0);assert.match(words(x),/Gerçek aktif run —/);assert.equal(button(x,'Kaydı temizle').props.disabled,true)});
test('loading removes prior data and disables read',()=>{const x=render('loading',sample);assert.equal(nodes(x,'meter').length,0);assert.equal(button(x,'Operasyon kaydını oku').props.disabled,true)});
test('hold clears even unexpected stale data and exposes timeout',()=>{const x=render('hold',sample,'TIMEOUT');assert.equal(nodes(x,'meter').length,0);assert.match(words(x),/zaman aşımı/);assert.doesNotMatch(words(x),/900/)});
test('historical role bars preserve numerator and denominator',()=>{const x=render('historical',sample);assert.deepEqual(nodes(x,'meter').map(n=>[n.props.value,n.props.max]),[[1,1],[1,1],[1,2],[0,1]]);assert.match(words(x),/performans değil/)});
test('budget keeps zero, reserve and remaining distinct',()=>{const x=render('historical',sample);assert.deepEqual(nodes(x,'dd').map(words),['100','0','900']);assert.match(words(x),/gerçek maliyet değildir/);assert.match(words(x),/Harcama ve yayın DENY/)});
test('pair identity visible without claiming atomicity or live work',()=>{const x=render('historical',sample);assert.match(words(x),new RegExp(sample.pair_id));assert.match(words(x),/Atomiklik doğrulanmadı/);assert.match(words(x),/Gerçek aktif run —/)});
test('read and reset call only existing hook callbacks',()=>{const x=render('historical',sample);button(x,'Operasyon kaydını oku').props.onClick();button(x,'Kaydı temizle').props.onClick();assert.equal(reads,1);assert.equal(resets,1);assert.equal(nodes(render('idle'),'meter').length,0)});
test('research not observed is not zero or success',()=>{const x=render('historical',{...sample,research_event_seq:null});assert.match(words(x),/Research örnek olayı Gözlenmedi/)});
