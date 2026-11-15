/** Run selected checked-in synthetic Node suites, not Next or security acceptance. */
const {spawnSync}=require('node:child_process');const {mkdtempSync,rmSync}=require('node:fs');const {tmpdir}=require('node:os');const {join,resolve}=require('node:path');
const repo=resolve(__dirname,'../..'),root=join(repo,'product','ai-company-os-frontend'),backend=join(repo,'product','ai-company-os-backend'),out=mkdtempSync(join(tmpdir(),'aicos-0187-w1-'));
function run(args){const p=spawnSync(process.execPath,args,{cwd:root,stdio:'inherit'});if(p.error)throw p.error;if(p.status!==0)throw Error('exit '+p.status);}
const js=p=>join(out,p+'.js'),fixture=p=>join(root,'fixtures',p+'.json'),shared=p=>join(backend,'tests',p+'.json');
const tests=[
 ['lifecycle-prefix.test.cjs',js('features/mvp/lifecyclePrefix'),shared('lifecycle_prefix_cases')],
 ['projection-registry.test.cjs',js('features/data/projectionRegistry'),js('features/mvp/lifecycleProjection')],
 ['lifecycle-projection.test.cjs',js('features/mvp/lifecycleProjection')],
 ['projection-read.test.cjs',js('features/data/projectionRead')],
 ['workflow-layout.test.cjs',js('design-system/workflowLayout')],
 ['navigation-model.test.cjs',js('design-system/navigationModel')],
 ['office-artwork.test.cjs',js('office/engine/officeArtwork'),js('office/engine/geometry'),fixture('core.preview')],
 ['gallery-camera.test.cjs',js('office/engine/galleryCamera')],
 ['role-visuals.test.cjs',js('design-system/roleVisuals'),js('office/engine/officeArtwork'),js('office/engine/geometry'),fixture('core.preview')],
 ['project-model.test.cjs',js('features/project-management/projectModel'),fixture('core.plan.projection')],
 ['finance-model.test.cjs',js('features/finance/financeModel'),fixture('company.catalog'),fixture('office.snapshot')],
 ['security-model.test.cjs',js('features/security/securityModel'),fixture('company.catalog'),fixture('office.snapshot'),fixture('core.preview')],
 ['workbench-snapshot.test.cjs',js('features/mvp/workbenchSnapshot')],
 ['admission-projection.test.cjs',js('features/mvp/admissionProjection'),js('app/api/demo/admission/route')],
 ['outbox-projection.test.cjs',js('features/mvp/outboxProjection'),js('app/api/demo/outbox/route')],
 ['outbox-contract.test.cjs',js('features/mvp/outboxProjection'),shared('outbox_projection_cases')],
 ['office-workbench.test.cjs',js('features/mvp/officeWorkbenchProjection'),js('app/api/demo/office-workbench/route'),shared('office_workbench_cases')],
];
try{
 const tsc=require.resolve('typescript/bin/tsc',{paths:[root]});
 const version=spawnSync(process.execPath,[tsc,'--version'],{encoding:'utf8'});if(version.status!==0||version.stdout.trim()!=='Version 5.9.3')throw Error('Pinned TypeScript 5.9.3 required');
 const entries=['features/mvp/lifecyclePrefix.ts','features/data/projectionRegistry.ts','features/mvp/lifecycleProjection.ts','features/data/projectionRead.ts','design-system/workflowLayout.ts','design-system/navigationModel.ts','design-system/roleVisuals.ts','office/engine/geometry.ts','office/engine/officeArtwork.ts','office/engine/galleryCamera.ts','features/project-management/projectModel.ts','features/finance/financeModel.ts','features/security/securityModel.ts','features/mvp/workbenchSnapshot.ts','app/api/demo/admission/route.ts','app/api/demo/outbox/route.ts','app/api/demo/office-workbench/route.ts'];
 run([tsc,'--strict','--target','ES2020','--lib','ESNext,DOM','--module','commonjs','--resolveJsonModule','--esModuleInterop','--rootDir',root,'--outDir',out,...entries]);
 for(const [name,...args] of tests)run([join(root,'tests',name),...args]);
 run([join(__dirname,'office-workbench-merge.test.cjs'),js('features/mvp/officeWorkbenchProjection'),js('app/api/demo/office-workbench/route')]);
 run([join(root,'scripts/run-diagnostics-tests.cjs')]);
}catch(e){console.error(e.message);process.exitCode=1;}finally{rmSync(out,{recursive:true,force:true});}
