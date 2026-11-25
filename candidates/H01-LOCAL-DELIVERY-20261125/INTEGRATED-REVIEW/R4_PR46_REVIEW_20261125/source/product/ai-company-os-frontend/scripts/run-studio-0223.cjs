/** Isolated diagnostic runner, not full build, browser or PostgreSQL acceptance. */
const {spawnSync}=require('node:child_process');
const {mkdtempSync,rmSync}=require('node:fs');
const {tmpdir}=require('node:os');
const {join,resolve,delimiter}=require('node:path');
const root=resolve(__dirname,'..'),backend=resolve(root,'../ai-company-os-backend');
const temp=mkdtempSync(join(tmpdir(),'aicos-studio-0223-'));
const compiled=join(temp,'compiled');
const python=process.env.AICOS_PYTHON||'python';
const env={...process.env,PYTHONPATH:[backend,join(backend,'tests')].join(delimiter),PYTHONDONTWRITEBYTECODE:'1'};
function run(exe,args,extra={}){const p=spawnSync(exe,args,{cwd:root,env:{...env,...extra},stdio:'inherit'});if(p.error)throw p.error;if(p.status!==0)throw Error('exit '+p.status);}
try{
 const tsc=process.env.AICOS_TSC||require.resolve('typescript/bin/tsc');
 const declarations=process.env.AICOS_NODE_DECLARATION?[resolve(process.env.AICOS_NODE_DECLARATION)]:[];
 run(process.execPath,[tsc,'--target','ES2022','--lib','ESNext,DOM','--strict','--module','commonjs','--esModuleInterop','--resolveJsonModule','--rootDir',root,'--outDir',compiled,'features/core-review/planProjection.ts','features/mvp/studioContext.ts','app/api/demo/plan/route.ts',...declarations]);
 const generate=[
 'from pathlib import Path',
 'import json,sys',
 'from app.core.orchestrator.engine import canonical_plan',
 'from app.core.development_review.lifecycle_prefix_wire import prefix_wire',
 'from app.core.development_review.shared_snapshot import build_shared_replay',
 'p=Path(sys.argv[1]); f=Path(sys.argv[2]) / "fixtures"',
 'plan=canonical_plan(json.loads((f/"core.preview.json").read_text(encoding="utf-8"))["plan"])',
 'assert plan==json.loads((f/"core.plan.projection.json").read_text(encoding="utf-8"))',
 '(p/"compiled-plan.json").write_text(json.dumps(plan,ensure_ascii=False),encoding="utf-8")',
 'for n in range(1,5): (p/("replay-%d.sse"%n)).write_bytes(build_shared_replay(prefix_wire(n)).encode("ascii"))'
 ].join('\n');
 run(python,['-c',generate,temp,backend]);
 run(python,['-m','unittest','-v','test_plan_projection']);
 run(process.execPath,['--test','tests/studio-context-0223.test.cjs','tests/plan-proxy-0223.test.cjs','tests/shared-snapshot-0222.test.cjs'],{
  AICOS_STUDIO_OUT:compiled,AICOS_PLAN_JSON:join(root,'fixtures/core.plan.projection.json'),AICOS_REPLAY:join(temp,'replay-4.sse'),AICOS_COMPILED_PLAN:join(temp,'compiled-plan.json'),SHARED_HELPER_JS:join(compiled,'features/data/sharedSnapshot.js'),SHARED_REPLAY_DIR:temp
 });
}catch(e){console.error(e.message);process.exitCode=1;}finally{rmSync(temp,{recursive:true,force:true});}
