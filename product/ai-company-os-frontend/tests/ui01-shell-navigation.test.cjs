'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require('typescript');
const sourceDir=path.join(__dirname,'../design-system');
const jsx=(type,props)=>({type,props:props||{}});
const flatten=(x,out=[])=>{if(Array.isArray(x)){x.forEach(y=>flatten(y,out));return out}if(x&&typeof x==='object'&&'type'in x){out.push(x);flatten(x.props.children,out)}return out};
const words=x=>Array.isArray(x)?x.map(words).join(''):x&&typeof x==='object'&&'type'in x?words(x.props.children):typeof x==='string'||typeof x==='number'?String(x):'';
function compile(name,modules,globals={}){
 const file=path.join(sourceDir,name),original=fs.readFileSync(file,'utf8');
 const compiled=ts.transpileModule(original,{fileName:file,compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},reportDiagnostics:true});
 assert.equal(compiled.diagnostics.filter(d=>d.category===ts.DiagnosticCategory.Error).length,0,name+' transpile diagnostics');
 const module={exports:{}};
 vm.runInNewContext(compiled.outputText,{module,exports:module.exports,require:id=>{assert.ok(Object.hasOwn(modules,id),'Unreviewed module '+id);return modules[id]},...globals},{filename:file});
 return {exports:module.exports,original};
}
function themeHarness(storage,available=true){
 let theme='dark',ctx,effects=[],writes=0,reads=0;
 const localStorage={getItem(k){reads++;if(!available)throw Error('denied');assert.equal(k,'ai-company-os:ui-theme');return storage;},setItem(k,v){writes++;if(!available)throw Error('denied');assert.equal(k,'ai-company-os:ui-theme');assert.ok(['dark','light'].includes(v));storage=v;}};
 const react={createContext:v=>ctx={value:v,Provider:'Provider'},useContext:c=>c.value,useState:()=>[theme,v=>{theme=typeof v==='function'?v(theme):v}],useEffect:f=>effects.push(f)};
 const m=compile('ThemeFrame.tsx',{'react':react,'react/jsx-runtime':{jsx,jsxs:jsx}},{window:{localStorage}});
 function render(){effects=[];const element=m.exports.default({children:'content'});ctx.value=element.props.value;return element;}
 function mount(){const before=render();const callbacks=[...effects];callbacks.forEach(f=>f());return {before,after:render()};}
 return {m,mount,render,toggle:()=>m.exports.ThemeToggle(),theme:()=>theme,writes:()=>writes,reads:()=>reads,storage:()=>storage};
}
function navigationHarness(mobile=false,current='Genel Bakış'){
 const items=[['Genel Bakış','A'],['Sanal Ofis','O'],['Güvenlik','S']];
 let index=0,hook=[],focusCount=0;const selected=[];
 const react={useState:init=>{const i=index++;if(!(i in hook))hook[i]=init;return [hook[i],v=>{hook[i]=typeof v==='function'?v(hook[i]):v}]},useRef:init=>({current:init}),useId:()=>String(index++),useEffect:()=>{}};
 const styles=new Proxy({},{get:(_,x)=>String(x)});
 const win={matchMedia:()=>({matches:mobile}),addEventListener(){},removeEventListener(){}};
 const document={getElementById:k=>{assert.equal(k,'main-content');return{focus(){focusCount++}}}};
 const m=compile('Navigation.tsx',{'react':react,'react/jsx-runtime':{jsx,jsxs:jsx},'next/link':{__esModule:true,default:'Link'},'./navigationModel':{groupNavigation:xs=>[{label:'test',items:xs}]},'./Navigation.module.css':{__esModule:true,default:styles}},{window:win,document,HTMLElement:class HTMLElement{}});
 function render(){index=0;return m.exports.default({items,current,onNavigate:n=>selected.push(n)})}
 return {m,render,items,selected,focus:()=>focusCount,hook};
}
test('ThemeFrame preserves initial dark SSR markup then restores only valid light choice',()=>{const h=themeHarness('light');const r=h.mount();assert.equal(flatten(r.before).find(x=>x.props.className==='eds-frame').props['data-eds-theme'],'dark');assert.equal(h.theme(),'light');assert.equal(flatten(r.after).find(x=>x.props.className==='eds-frame').props['data-eds-theme'],'light');assert.equal(h.writes(),0);assert.equal(h.reads(),1)});
test('theme button persists safe preference and aria-pressed remains truthful',()=>{const h=themeHarness('dark');h.mount();let button=h.toggle();assert.equal(button.props['aria-pressed'],false);button.props.onClick();h.render();button=h.toggle();assert.equal(h.theme(),'light');assert.equal(button.props['aria-pressed'],true);assert.equal(h.storage(),'light');assert.equal(h.writes(),1);button.props.onClick();assert.equal(h.storage(),'dark')});
test('unknown or malicious stored theme is ignored, never injected into DOM',()=>{const h=themeHarness('constructor');h.mount();assert.equal(h.theme(),'dark');assert.equal(h.writes(),0)});
test('storage denial cannot prevent in-memory theme selection',()=>{const h=themeHarness('light',false);h.mount();assert.equal(h.theme(),'dark');assert.doesNotThrow(()=>h.toggle().props.onClick());assert.equal(h.theme(),'light')});
test('navigation view button moves keyboard focus to main on desktop',()=>{const h=navigationHarness(false);const tree=h.render();const button=flatten(tree).find(n=>n.type==='button'&&n.props['aria-label']==='Güvenlik');assert.ok(button);button.props.onClick();assert.deepEqual(h.selected,['Güvenlik']);assert.equal(h.focus(),1)});
test('navigation continues to close mobile and focus main on section selection',()=>{const h=navigationHarness(true);const tree=h.render();const button=flatten(tree).find(n=>n.type==='button'&&n.props['aria-label']==='Güvenlik');button.props.onClick();assert.deepEqual(h.selected,['Güvenlik']);assert.equal(h.focus(),1);assert.equal(h.hook[2],false)});
test('navigation has a polite live region announcing the selected section',()=>{const h=navigationHarness();const tree=h.render();const status=flatten(tree).find(x=>x.props['aria-live']==='polite');assert.ok(status);assert.equal(status.props.role,'status');assert.match(words(status),/Görüntülenen bölüm: Genel Bakış/)});
test('office route remains an actual Link and does not dispatch an action',()=>{const h=navigationHarness(false,'Sanal Ofis');const tree=h.render();const link=flatten(tree).find(x=>x.type==='Link');assert.ok(link);assert.equal(link.props.href,'/office');assert.equal(link.props['aria-current'],'page');assert.deepEqual(h.selected,[])});
test('live status is visually clipped, not removed from accessibility tree',()=>{const h=navigationHarness();const status=flatten(h.render()).find(x=>x.props['aria-live']==='polite');assert.equal(status.props.style.position,'absolute');assert.equal(status.props.style.width,1);assert.equal(status.props.style.overflow,'hidden');assert.equal(status.props.style.display,undefined)});
test('UI-01 navigation and theme remain presentation-only',()=>{const theme=fs.readFileSync(path.join(sourceDir,'ThemeFrame.tsx'),'utf8'),nav=fs.readFileSync(path.join(sourceDir,'Navigation.tsx'),'utf8');for(const code of [theme,nav])assert.doesNotMatch(code,/fetch\(|axios|POST|localStorage\.removeItem|location\.assign|dispatch\(/);assert.match(nav,/onNavigate\(name\)/);assert.match(theme,/data-eds-theme=\{theme\}/)});
