const {spawnSync}=require('node:child_process');
const {mkdtempSync,rmSync}=require('node:fs');
const {tmpdir}=require('node:os');
const {join,resolve}=require('node:path');
const root=resolve(__dirname,'..');
const out=mkdtempSync(join(tmpdir(),'company-os-mvp-'));
function run(args,env=process.env){const p=spawnSync(process.execPath,args,{cwd:root,env,stdio:'inherit'});if(p.error)throw p.error;if(p.status!==0)throw Error('exit '+p.status);}
try{
 run([require.resolve('typescript/bin/tsc'),'--target','ES2020','--lib','ESNext,DOM','--strict','--module','commonjs','--outDir',out,'app/api/demo/mvp/route.ts','features/mvp/mvpDiagnostics.ts']);
 run(['--test','tests/mvpDiagnostics.test.cjs','tests/mvpProxy.test.cjs'],{...process.env,MVP_HELPER_JS:join(out,'features/mvp/mvpDiagnostics.js'),MVP_PROXY_JS:join(out,'app/api/demo/mvp/route.js')});
}catch(e){console.error(e.message);process.exitCode=1;}finally{rmSync(out,{recursive:true,force:true});}
