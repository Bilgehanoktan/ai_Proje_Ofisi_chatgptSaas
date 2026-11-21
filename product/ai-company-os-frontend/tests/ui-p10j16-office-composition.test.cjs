'use strict';
// Isolated JSX projection test, not a React/Next/Phaser/browser acceptance.
const assert=require('node:assert/strict');
const test=require('node:test');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');
const file=path.join(__dirname,'../components/dashboard/OfficePanel.tsx');
const source=fs.readFileSync(file,'utf8');
const compiled=ts.transpileModule(source,{fileName:file,compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},reportDiagnostics:true});
const jsx=(type,props,key)=>({type,props,key});
const modules={'react/jsx-runtime':{jsx,jsxs:jsx},'next/link':'Link','../../design-system/OfficeControls':{DisplayControls:'DisplayControls',FloorControls:'FloorControls'},'../../office/scenes/OfficeScene':'OfficeScene','../../office/components/OfficeIllustration':'OfficeIllustration','../../features/mvp/OfficeWorkbenchPanel':'OfficeWorkbenchPanel','../../features/data/SharedSnapshotPanel':'SharedSnapshotPanel'};
const mod={exports:{}};
vm.runInNewContext(compiled.outputText,{exports:mod.exports,module:mod,require:id=>{assert.ok(Object.hasOwn(modules,id),"Unexpected module: "+id);return modules[id];}});
const panel=mod.exports.default;
const render=overrides=>panel({floors:[{id:'floor-1',name:'Core'},{id:'floor-2',name:'Reserve'}],floorId:'floor-1',display:'scene',onFloor:()=>{},onDisplay:()=>{},officeOnly:false,stations:jsx('span',{children:'stations'}),demoFloor:{id:'floor-1'},layoutRevision:'layout-1',snapshotRevision:'layout-1',geometryReason:'unbound',...overrides});
function flatten(x,out=[]){if(Array.isArray(x)){for(const v of x)flatten(v,out);}else if(x&&typeof x==='object'){out.push(x);flatten(x.props?.children,out);}return out;}
function nodes(x,type){return flatten(x).filter(n=>n.type===type);}
function words(x){if(Array.isArray(x))return x.map(words).join(' ');if(x&&typeof x==='object')return words(x.props?.children);return typeof x==='string'?x:'';}
function links(x){return nodes(x,'Link').map(n=>n.props.href);}
test('TSX has no transpilation diagnostics',()=>assert.equal(compiled.diagnostics.filter(d=>d.category===ts.DiagnosticCategory.Error).length,0));
test('embedded office keeps shared snapshot and all three routes',()=>{const x=render();assert.deepEqual(links(x),['/office','/office/premium','/office/premium/unified']);assert.equal(nodes(x,'SharedSnapshotPanel').length,1);assert.equal(nodes(x,'SharedSnapshotPanel')[0].props.office,true);});
test('fullscreen retains premium navigation but not redundant fullscreen link',()=>assert.deepEqual(links(render({officeOnly:true})),['/office/premium','/office/premium/unified']));
test('all three displays retain shared history and explicit non-authority',()=>{for(const display of ['scene','list','engine']){const x=render({display});assert.equal(nodes(x,'SharedSnapshotPanel').length,1);assert.match(words(x),/JOIN_HOLD/);assert.match(words(x),/STATIC_ONLY/);assert.match(words(x),/dekoratif bir D0/);}});
test('scene and engine retain separate render paths',()=>{assert.equal(nodes(render(),'OfficeIllustration').length,1);assert.equal(nodes(render({display:'engine'}),'OfficeScene').length,1);assert.equal(nodes(render({display:'list'}),'OfficeScene').length,0);});
test('mismatched revisions never grant geometry join',()=>assert.match(words(render({snapshotRevision:'other'})),/Yerleşim revizyonları farklı: other \/ layout-1.*canlı hareket ve konum birleştirmesi yok/s));
test('missing geometry renders HOLD and keeps navigation',()=>{const x=render({display:'engine',demoFloor:undefined});assert.equal(nodes(x,'OfficeScene').length,0);assert.match(words(x),/Geometri HOLD.*unbound/s);assert.ok(links(x).includes('/office/premium'));});
test('reserve floor never gains core workbench',()=>{const x=render({floorId:'floor-2',demoFloor:{id:'floor-2'}});assert.equal(nodes(x,'OfficeWorkbenchPanel').length,0);assert.equal(nodes(x,'SharedSnapshotPanel').length,1);});
