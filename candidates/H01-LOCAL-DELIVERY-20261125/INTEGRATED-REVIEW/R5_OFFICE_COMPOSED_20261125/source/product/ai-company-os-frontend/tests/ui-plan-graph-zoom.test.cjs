'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const file=path.resolve(__dirname,'../features/graph/PlanGraph.tsx');
const source=fs.readFileSync(file,'utf8');
const compiled=ts.transpileModule(source,{fileName:file,compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true},reportDiagnostics:true});
const jsx=(type,props)=>({type,props:props||{}});
const styles=new Proxy({}, {get(_target,key){return String(key)}});
const graph={width:444,height:144,nodes:[{id:'plan',label:'Plan',role:'orchestrator',x:24,y:56},{id:'qa',label:'QA',role:'qa',x:248,y:56}],edges:[{from:'plan',to:'qa',kind:'reference',d:'M0 0 H1'}]};
let zoomState=1,selected=[];
const requireMock=id=>{
 if(id==='react')return {useId:()=>':graph:',useState:initial=>[zoomState,change=>{zoomState=typeof change==='function'?change(zoomState):change}]};
 if(id==='react/jsx-runtime')return {jsx,jsxs:jsx};
 if(id==='./graphPresentation')return {graphPresentation:(tasks)=>tasks.length?graph:null,NODE_WIDTH:172,NODE_HEIGHT:64};
 if(id==='./PlanGraph.module.css')return {__esModule:true,default:styles};
 throw Error('UNEXPECTED_REQUIRE: '+id);
};
const mod={exports:{}};
vm.runInNewContext(compiled.outputText,{exports:mod.exports,module:mod,require:requireMock});
const {default:PlanGraph,GRAPH_ZOOM_STEPS,stepGraphZoom}=mod.exports;
const props={tasks:[{id:'plan',label:'Plan',role:'orchestrator'},{id:'qa',label:'QA',role:'qa'}],waves:[['plan'],['qa']],links:[{from:'plan',to:'qa',kind:'reference'}],selected:'plan',onSelect:id=>selected.push(id),label:'Referans plan DAG'};
function flatten(x,out=[]){if(Array.isArray(x))for(const n of x)flatten(n,out);else if(x&&typeof x==='object'){out.push(x);flatten(x.props?.children,out)}return out}
function render(p=props){return flatten(PlanGraph(p))}
function button(nodes,label){const b=nodes.find(x=>x.type==='button'&&x.props['aria-label']===label);assert.ok(b,label);return b}
function viewport(nodes){const n=nodes.find(x=>x.type==='div'&&x.props.className==='viewport');assert.ok(n);return n}
function canvas(nodes){const n=nodes.find(x=>x.type==='div'&&x.props.className==='canvas');assert.ok(n);return n}
test('actual TSX transpiles without syntax diagnostic',()=>assert.equal(compiled.diagnostics.filter(d=>d.category===ts.DiagnosticCategory.Error).length,0));
test('zoom levels fixed with meaningful reset',()=>{assert.deepEqual(Array.from(GRAPH_ZOOM_STEPS),[.75,1,1.25,1.5]);assert.equal(stepGraphZoom(.75,-1),.75);assert.equal(stepGraphZoom(1.5,1),1.5)});
test('invalid incoming scale recovers to known levels',()=>{assert.equal(stepGraphZoom(NaN,1),1.25);assert.equal(stepGraphZoom(999,-1),.75)});
test('initial 100 percent keeps original canvas geometry',()=>{zoomState=1;const n=render();assert.equal(viewport(n).props.style.width,444);assert.equal(viewport(n).props.style.height,144);assert.equal(canvas(n).props.style.transform,'scale(1)')});
test('two click zoom in, disabled at upper bound, reset to baseline',()=>{zoomState=1;for(const [scale,w] of [[1.25,555],[1.5,666]]){button(render(),'Grafiği yakınlaştır').props.onClick();assert.equal(zoomState,scale);assert.equal(viewport(render()).props.style.width,w)}assert.equal(button(render(),'Grafiği yakınlaştır').props.disabled,true);button(render(),'Grafik ölçeğini sıfırla').props.onClick();assert.equal(zoomState,1);assert.equal(button(render(),'Grafik ölçeğini sıfırla').props.disabled,true)});
test('zoom out bounds and viewport height',()=>{zoomState=1;button(render(),'Grafiği uzaklaştır').props.onClick();assert.equal(zoomState,.75);assert.equal(viewport(render()).props.style.height,108);assert.equal(button(render(),'Grafiği uzaklaştır').props.disabled,true)});
test('controls are keyboard-operable semantic buttons with live output',()=>{zoomState=1;const n=render();const output=n.find(x=>x.type==='output');assert.equal(output.props['aria-live'],'polite');assert.equal(output.props.children[0],100);assert.equal(button(n,'Grafiği yakınlaştır').props.type,'button');assert.ok(n.find(x=>x.props.role==='group'&&x.props['aria-label']==='Referans plan DAG · grafik ölçeği'))});
test('task selection semantics and graph evidence unchanged after zoom',()=>{zoomState=1.5;selected=[];const n=render();const buttons=n.filter(x=>x.type==='button'&&x.props.className==='node');assert.equal(buttons.length,2);assert.equal(buttons[0].props['aria-pressed'],true);buttons[1].props.onClick();assert.deepEqual(selected,['qa']);assert.equal(n.filter(x=>x.type==='path'&&x.props['data-kind']==='reference').length,1);assert.equal(n.find(x=>x.type==='details').props.className,'edges')});
test('invalid graph stays HOLD and cannot expose controls',()=>{zoomState=1;const n=render({...props,tasks:[]});assert.ok(n.some(x=>x.type==='p'&&x.props.role==='status'));assert.equal(n.filter(x=>x.type==='button').length,0)});
test('display-only interactions do not mutate provided plan',()=>{zoomState=1;const before=JSON.stringify(props);const n=render();button(n,'Grafiği yakınlaştır').props.onClick();render();assert.equal(JSON.stringify(props),before)});
test('stylesheet retains scroll and focus accessibility',()=>{const css=fs.readFileSync(path.resolve(__dirname,'../features/graph/PlanGraph.module.css'),'utf8');assert.match(css,/\.scroll\{overflow:auto/);assert.match(css,/\.zoomControls button:focus-visible/);assert.match(css,/\.viewport\{position:relative/)});
