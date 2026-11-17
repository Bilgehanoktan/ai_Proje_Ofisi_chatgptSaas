"""Generate U3A-pinned review patch, not an automatic product activation."""
from pathlib import Path
import hashlib, difflib, json
HERE=Path(__file__).resolve().parent
PREFIX='product/ai-company-os-frontend/'
PINS={
 'projectionRead.ts':('features/data/projectionRead.ts','5456a3812117d4f4d9503e4875625e58bea0382b'),
 'projectionRegistry.ts':('features/data/projectionRegistry.ts','ff46b18ad1a20b295066f3e7a3aad1c79dfc07b6'),
 'useProjectionRead.ts':('features/data/useProjectionRead.ts','73ef76f14855875aa50a7e619214a5311c1393f2'),
 'AgentDirectory.tsx':('features/evidence/AgentDirectory.tsx','bb3ad084dd62a094363a44e86805f9693400bb30')}
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('PATCH_ANCHOR_HOLD')
 return s.replace(a,b)
def build():
 before={}
 for name,(_,pin) in PINS.items():
  raw=(HERE/'base'/name).read_bytes()
  if blob(raw)!=pin:raise ValueError('SOURCE_PIN_HOLD')
  before[name]=raw.decode()
 after=dict(before)
 after['projectionRead.ts']=once(before['projectionRead.ts'],"export const endpointCaps", "import {organizationCap} from '../organization/organizationProjection';\nexport const endpointCaps")
 after['projectionRead.ts']=once(after['projectionRead.ts'],"plan:16384}","plan:16384,organization:organizationCap}")
 after['projectionRegistry.ts']=once(before['projectionRegistry.ts'],"import {parseMvpDiagnostics}","import {parseOrganization} from '../organization/organizationProjection';\nimport {parseMvpDiagnostics}")
 after['projectionRegistry.ts']=once(after['projectionRegistry.ts'],"plan:parsePlanProjection}","plan:parsePlanProjection,organization:parseOrganization}")
 after['AgentDirectory.tsx']=once(before['AgentDirectory.tsx'],"import AgentRoleProfile", "import OrganizationReadback from '../organization/OrganizationReadback';\nimport AgentRoleProfile")
 after['AgentDirectory.tsx']=once(after['AgentDirectory.tsx'],"  <div className={styles.filters}>","  <OrganizationReadback/>\n  <div className={styles.filters}>")
 files={path:after[n] for n,(path,_) in PINS.items()}
 for n in ('organizationProjection.ts','organizationProxy.ts','OrganizationReadback.tsx'):
  files['features/organization/'+n]=(HERE/'frontend'/n).read_text()
 # Deliberately deny until existing authenticated server composition is provided.
 files['app/api/demo/organization/route.ts']="import {readOrganizationProxy} from '../../../../features/organization/organizationProxy';\nimport {localBackendPort} from '../../../../features/mvp/localBackend';\nexport const dynamic='force-dynamic';\nexport async function GET(request:Request){\n try{return await readOrganizationProxy(request,localBackendPort());}\n catch{return Response.json({mode:'D0_ORGANIZATION_READ_HOLD'},{status:503,headers:{'Cache-Control':'no-store'}});}\n}\n"
 diff=[]
 for path,new in sorted(files.items()):
  old=next((before[n] for n,(p,_) in PINS.items() if p==path),'')
  if old==new:continue
  target=PREFIX+path
  if not old: diff.extend([f'diff --git a/{target} b/{target}\n','new file mode 100644\n'])
  diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+target if old else '/dev/null',tofile='b/'+target))
 return files,''.join(diff)
if __name__=='__main__':
 files,patch=build();(HERE/'PRODUCT_REVIEW.patch').write_text(patch)
 out=HERE/'staged'
 for path,value in files.items():
  p=out/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
 print('4/4 U3A base blob pins verified; 3 modified, 4 added; hook unchanged; patch NOT applied to product')
