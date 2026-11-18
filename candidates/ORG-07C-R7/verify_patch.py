"""Recreate the exact pinned R6 patch and exercise Git on a disposable subset, not a full checkout."""
from pathlib import Path
import difflib, hashlib, json, subprocess, tempfile, zipfile, shutil
HERE=Path(__file__).resolve().parent
PREFIX='product/ai-company-os-frontend/'
BASE={'features/data/projectionRead.ts':('projectionRead.ts','5456a3812117d4f4d9503e4875625e58bea0382b'),'features/data/projectionRegistry.ts':('projectionRegistry.ts','ff46b18ad1a20b295066f3e7a3aad1c79dfc07b6'),'features/data/useProjectionRead.ts':('useProjectionRead.ts','73ef76f14855875aa50a7e619214a5311c1393f2'),'features/evidence/AgentDirectory.tsx':('AgentDirectory.tsx','bb3ad084dd62a094363a44e86805f9693400bb30'),'features/mvp/localBackend.ts':('localBackend.ts','9231711d7efb18dd18b68e3322f62337a6477484')}
OUT={'features/data/projectionRead.ts':'fc7ab9b7fb55c871fc2d82a701db89e0945e7aed','features/data/projectionRegistry.ts':'b8d4419253c201741a6f2f5aac31906a9a528110','features/data/useProjectionRead.ts':'73ef76f14855875aa50a7e619214a5311c1393f2','features/evidence/AgentDirectory.tsx':'7104179f6b853548469bc20ba28a7cd3db07ca2d','features/mvp/localBackend.ts':'9231711d7efb18dd18b68e3322f62337a6477484','features/organization/organizationProjection.ts':'cb824d03aa76b45aae3f7f11237f4f6fa82fd96f','features/organization/organizationProxy.ts':'f257f77ca5887b2477bdf3fc3f68e2b37c735eff','features/organization/OrganizationReadback.tsx':'990b06ee2b5adc115547615719610ccc02a66061','app/api/demo/organization/route.ts':'fe445fa4b8fff74eae3def2d9f12d8c93c8e154b','features/organization/organizationOwnerBinding.ts':'9441f5ead5e9b420ee99b0884578e96e5f4b7f51'}
PATCH='3be745832bcdb908625f99164296dff9aa06f928'
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def verify(raw,pin):
 if blob(raw)!=pin:raise ValueError('PIN_HOLD '+pin+' actual '+blob(raw))
 return raw.decode('utf-8')
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('ANCHOR_HOLD')
 return s.replace(a,b)
def generate():
 before={p:verify((HERE/'base'/n).read_bytes(),h) for p,(n,h) in BASE.items()}
 after=dict(before)
 p='features/data/projectionRead.ts';after[p]=once(once(before[p],'export const endpointCaps',"import {organizationCap} from '../organization/organizationProjection';\nexport const endpointCaps"),'plan:16384}','plan:16384,organization:organizationCap}')
 p='features/data/projectionRegistry.ts';after[p]=once(once(before[p],'import {parseMvpDiagnostics}',"import {parseOrganization} from '../organization/organizationProjection';\nimport {parseMvpDiagnostics}"),'plan:parsePlanProjection}','plan:parsePlanProjection,organization:parseOrganization}')
 p='features/evidence/AgentDirectory.tsx';after[p]=once(once(before[p],'import AgentRoleProfile',"import OrganizationReadback from '../organization/OrganizationReadback';\nimport AgentRoleProfile"),'  <div className={styles.filters}>','  <OrganizationReadback/>\n  <div className={styles.filters}>')
 for name in ('organizationProjection.ts','organizationProxy.ts','OrganizationReadback.tsx','organizationOwnerBinding.ts'):
  p='features/organization/'+name;after[p]=verify((HERE/'frontend'/name).read_bytes(),OUT[p])
 p='app/api/demo/organization/route.ts';after[p]=verify((HERE/'frontend'/'route.ts').read_bytes(),OUT[p])
 for p,s in after.items():verify(s.encode(),OUT[p])
 diff=[];binding='features/organization/organizationOwnerBinding.ts'
 for p in sorted(k for k in after if k!=binding)+[binding]:
  old=before.get(p,'');new=after[p]
  if old==new:continue
  target=PREFIX+p
  if not old:diff.extend([f'diff --git a/{target} b/{target}\n','new file mode 100644\n'])
  diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+target if old else '/dev/null',tofile='b/'+target))
 patch=''.join(diff).encode();verify(patch,PATCH)
 return before,after,patch

def main():
 before,after,patch=generate();print('exact base pins',len(before));print('exact output pins',len(after));print('exact patch',blob(patch),sha(patch))
 (HERE/'PRODUCT_REVIEW.patch').write_bytes(patch)
 checks=[]
 with tempfile.TemporaryDirectory(prefix='org07r7-') as d:
  root=Path(d)
  def git(*args,ok=True):
   r=subprocess.run(['git',*args],cwd=root,capture_output=True,text=True)
   if (r.returncode==0)!=ok:raise RuntimeError(str(args)+' '+r.stdout+r.stderr)
   print('git',*args,'exit',r.returncode);return r
  def write(p,s):
   f=root/(PREFIX+p);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(s.encode())
  def inventory():return {p.relative_to(root).as_posix():blob(p.read_bytes()) for p in (root/'product').rglob('*') if p.is_file()}
  git('init','-q');git('config','core.autocrlf','false')
  for p,s in before.items():write(p,s)
  git('add','product');baseline=inventory();f=HERE/'PRODUCT_REVIEW.patch'
  git('apply','--check',str(f));checks.append('full_patch_check')
  git('apply',str(f));checks.append('full_patch_apply')
  if inventory()!={PREFIX+p:h for p,h in OUT.items()}:raise RuntimeError('postimage')
  checks.append('all_output_blobs');print('10/10 output blobs; 3 modified, 5 added, 2 unchanged')
  git('apply','--reverse','--check',str(f));git('apply','--reverse',str(f))
  if inventory()!=baseline:raise RuntimeError('rollback')
  checks.append('exact_reverse')
  # A changed hunk anchor and a new-path collision must not be silently overwritten.
  p='features/data/projectionRead.ts';write(p,before[p].replace('export const endpointCaps','export const differentCaps',1))
  git('apply','--check',str(f),ok=False);checks.append('changed_anchor_rejected');write(p,before[p])
  p='features/organization/organizationOwnerBinding.ts';write(p,'collision\n')
  git('apply','--check',str(f),ok=False);checks.append('new_path_collision_rejected');(root/(PREFIX+p)).unlink()
  if inventory()!=baseline:raise RuntimeError('baseline drift')
  checks.append('baseline_preserved')
  # Reapply and export exact 10-file product subset, for tests of actual route/reader sources.
  git('apply',str(f));staged=HERE/'staged'
  for p in OUT:
   q=staged/p;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/(PREFIX+p),q)
  result={'base':{p:blob(s.encode()) for p,s in before.items()},'outputs':OUT,'patch_blob':PATCH,'patch_sha256':sha(patch),'checks':checks,'scope':'exact 5-file base subset, 10 output files, not full repository checkout','manifest_rows':{PREFIX[8:]+p:{'bytes':len(s.encode()),'sha256':sha(s.encode())} for p,s in after.items()}}
  (HERE/'evidence'/'patch.json').write_text(json.dumps(result,indent=2)+'\n')
 print(len(checks),'checks PASS')
if __name__=='__main__':main()
