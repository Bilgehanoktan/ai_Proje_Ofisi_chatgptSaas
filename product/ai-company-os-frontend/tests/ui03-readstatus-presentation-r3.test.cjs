'use strict';
/** Targeted R3 presentation checks. Does NOT rerun PR48's 12+9 reader suites. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const ts=require('typescript');
const target=process.env.AIOS_R3_TARGET||path.resolve(__dirname,'../features/data/SharedSnapshotPanel.tsx');
const helper=process.env.AIOS_R3_HELPER||path.resolve(__dirname,'../features/data/projectionRead.ts');
assert.ok(target&&helper,'usage: node --test test.cjs <SharedSnapshotPanel.tsx> <projectionRead.ts>');
const moduleCompile=(p)=>{
 const out=ts.transpileModule(fs.readFileSync(p,'utf8'),{fileName:p,reportDiagnostics:true,compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022,strict:true}});
 assert.deepEqual(out.diagnostics?.filter(d=>d.category===ts.DiagnosticCategory.Error),[]);
 return out.outputText;
};
const elements={jsx:(type,props,key)=>({type,props:props||{},key}),jsxs:(type,props,key)=>({type,props:props||{},key}),Fragment:Symbol('Fragment')};
const compile=(text,mocks)=>{
 const module={exports:{}};
 new Function('require','module','exports',text)((name)=>{
  if(Object.hasOwn(mocks,name))return mocks[name];
  throw Error('Unexpected dependency: '+name);
 },module,module.exports);
 return module.exports;
};
const {readStatus}=compile(moduleCompile(helper),{'../organization/organizationProjection':{organizationCap:1048576}});
let snapshot,organization;
const actions={plan:0,org:0,planReset:0,orgReset:0};
const panel=compile(moduleCompile(target),{
 'react/jsx-runtime':elements,
 './SharedSnapshotProvider':{useSharedSnapshot:()=>({state:{phase:'idle',data:null},read:()=>{},reset:()=>{},planRead:{state:snapshot,data:snapshot.data,read:()=>actions.plan++,reset:()=>actions.planReset++},organizationRead:{state:organization,data:organization.data,read:()=>actions.org++,reset:()=>actions.orgReset++}})},
 'next/link':{default:'a'},
 './projectionRead':{readStatus},
 '../mvp/historicalJoin':compile(moduleCompile(path.resolve(__dirname,'../features/mvp/historicalJoin.ts')),{}),
 '../security/securityModel':{readSecurityView:()=>({ok:true,trust:[{id:'iv',status:'INCONCLUSIVE'},{id:'release',status:'HOLD'}]})},
 }).default;
const walk=(node,fn)=>{
 if(Array.isArray(node)){for(const v of node)walk(v,fn);return;}
 if(node===null||node===undefined||typeof node==='boolean')return;
 if(typeof node==='object'&&Object.hasOwn(node,'type')){fn(node);walk(node.props.children,fn);}
};
const textOf=(node)=>{let out='';const visit=x=>{if(x===undefined||x===null||typeof x==='boolean')return;if(Array.isArray(x)){x.forEach(visit);return;}if(typeof x==='object'){visit(x.props?.children);return;}out+=String(x);};visit(node);return out;};
const nodeByLabel=(node,label)=>{let found;walk(node,e=>{if(e.props['aria-label']===label)found=e;});assert.ok(found,'missing '+label);return found;};
const state=(phase,reason)=>phase==='hold'?{phase,data:null,reason}:phase==='historical'?{phase,data:{tasks:[{id:'reference-task'}],waves:[{id:'reference-wave'}],positions:[{id:'sample-position'}]}}:{phase,data:null};
const render=(planState,orgState,office=false)=>{snapshot=planState;organization=orgState;return panel({office});};
const content=(planState,orgState)=>{const ui=render(planState,orgState);return {ui,plan:textOf(nodeByLabel(ui,'CEO proje planı')),org:textOf(nodeByLabel(ui,'CEO organizasyon kaydı'))};};

test('STALE plan explains expiry, hides plan counts, preserves ORG isolation',()=>{
 const r=content(state('hold','STALE'),state('idle'));
 assert.match(r.plan,/Tarihsel görüntüleme süresi doldu · HOLD/);
 assert.match(r.plan,/Gerçek görev yok/);
 assert.doesNotMatch(r.plan,/1 referans görev/);
 assert.match(r.org,/Okunmadı · HOLD/);
});
test('TIMEOUT organization explains deadline and never shows an active agent',()=>{
 const r=content(state('idle'),state('hold','TIMEOUT'));
 assert.match(r.org,/Okuma zaman aşımı · HOLD/);
 assert.match(r.org,/Aktif ajan bilinmiyor/);
 assert.doesNotMatch(r.org,/1 tarihsel pozisyon/);
 assert.match(r.plan,/Okunmadı · HOLD/);
});
test('READBACK_HOLD retains generic refusal, not a false timeout',()=>{
 const r=content(state('hold','READBACK_HOLD'),state('hold','READBACK_HOLD'));
 for(const value of [r.plan,r.org]){
  assert.match(value,/Okuma reddedildi · HOLD/);
  assert.doesNotMatch(value,/zaman aşımı|süresi doldu/);
 }
});
test('historical D0 is distinguishable from actual completion, identity and grant',()=>{
 const r=content(state('historical'),state('historical'));
 assert.match(r.plan,/Tarihsel D0 · HOLD/);
 assert.match(r.plan,/1 referans görev · 1 dalga/);
 assert.match(r.plan,/A0_SAMPLE_ONLY · gerçek tamamlanma bilinmiyor/);
 assert.match(r.org,/Tarihsel D0 · HOLD/);
 assert.match(r.org,/1 tarihsel pozisyon/);
 assert.match(r.org,/gerçek çalışan veya IAM grant değildir/);
});
test('loading clears displayed counts and keeps independent states',()=>{
 const r=content(state('loading'),state('hold','STALE'));
 assert.match(r.plan,/Okunuyor…/);
 assert.doesNotMatch(r.plan,/referans görev · 1/);
 assert.match(r.org,/Tarihsel görüntüleme süresi doldu · HOLD/);
});
test('existing read and reset buttons still delegate without actions or live API writes',()=>{
 const r=render(state('idle'),state('idle'));
 const buttons=[];walk(r,n=>{if(n.type==='button')buttons.push(n);});
 for(const [label,entry] of [['Plan kaydını oku','plan'],['ORG kaydını oku','org'],['Planı temizle','planReset'],['ORG temizle','orgReset']]){
  const b=buttons.find(b=>textOf(b)===label);
  assert.ok(b,label);
  if(!b.props.disabled){const before=actions[entry];b.props.onClick();assert.equal(actions[entry],before+1);}
 }
});
test('Office view remains historical-only with no CEO cross-reader join or geometry authority',()=>{
 const r=render(state('hold','STALE'),state('hold','TIMEOUT'),true);
 const text=textOf(r);
 assert.doesNotMatch(text,/CEO kaynak ve kontrol özeti/);
 assert.match(text,/HISTORICAL ONLY/);
 assert.match(text,/Statik ofis geometrisi ayrı referanstır/);
 assert.match(text,/Canlı SSE, ajan konumu/);
});
test('CEO control source, release and join limitations are preserved',()=>{
 const r=content(state('hold','STALE'),state('hold','TIMEOUT'));
 const text=textOf(r.ui);
 assert.match(text,/Statik geometri · JOIN_HOLD/);
 assert.match(text,/IV: INCONCLUSIVE · Yayın: HOLD/);
 assert.match(text,/HOLD \/ NO LIVE KPI/);
 assert.match(text,/Farklı endpoint sonuçları aynı tenant\/anda olduğuna dair kanıt olmadan eşleştirilmez/);
});
