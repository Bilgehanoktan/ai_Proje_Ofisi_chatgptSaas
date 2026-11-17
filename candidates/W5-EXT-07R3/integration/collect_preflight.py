"""Read-only full Git inventory collection for the exact repository preflight.
Use after authenticated fetch on an isolated clone; never merges or updates refs.
"""
import argparse, hashlib, importlib.util, json, subprocess
from pathlib import Path

PIN='e8f492a2a6fe27a1b971c0900d4e21bd4c9b8760'
BASE='ba20cd64eba0f09390818c294ae8894fab9a3acf'


def git(repo,*args):
    return subprocess.check_output(['git','-C',str(repo),*args])


def commit(repo,ref):
    return git(repo,'rev-parse','--verify',ref+'^{commit}').decode('ascii').strip()


def inventory(repo,sha):
    blobs,modes={},{}
    for row in git(repo,'ls-tree','-r','-z',sha).split(b'\0'):
        if not row:continue
        meta,name=row.split(b'\t',1);mode,kind,oid=meta.decode('ascii').split(' ')
        path=name.decode('utf-8',errors='strict')
        if path in modes:raise ValueError('DUPLICATE_PATH')
        if kind!='blob':raise ValueError('NON_BLOB_TREE_ENTRY_HOLD: '+path)
        if mode not in ('100644','100755'):raise ValueError('UNSUPPORTED_MODE_HOLD: '+path)
        blobs[path]=oid;modes[path]=mode
    return blobs,modes


def load_exact(path):
    raw=path.read_bytes()
    if path.is_symlink() or hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=PIN:raise ValueError('PREFLIGHT_SOURCE_PIN_HOLD')
    spec=importlib.util.spec_from_file_location('canonical_preflight',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def collect(repo,local,refs,engine,output):
    if not refs or len(set(refs))!=len(refs):raise ValueError('REF_SET_HOLD')
    if output.resolve().is_relative_to(repo.resolve()):raise ValueError('OUTPUT_INSIDE_SOURCE_HOLD')
    head=commit(repo,local);heads={ref:commit(repo,ref) for ref in refs}
    l,lm=inventory(repo,head);output.mkdir(parents=True,exist_ok=False)
    results=[]
    for i,(ref,h) in enumerate(heads.items(),1):
        ancestors=git(repo,'merge-base','--all',head,h).decode('ascii').splitlines()
        if len(ancestors)!=1:raise ValueError('AMBIGUOUS_MERGE_BASE_HOLD')
        a=ancestors[0];b,bm=inventory(repo,a);r,rm=inventory(repo,h)
        result=engine.compare(b,l,r)
        mode_changes=[p for p in sorted(set(bm)|set(lm)|set(rm)) if len({x for x in (bm.get(p),lm.get(p),rm.get(p)) if x is not None})>1]
        d=output/f'{i:02d}';d.mkdir()
        for name,value in [('base',b),('local',l),('incoming',r),('modes',{'base':bm,'local':lm,'incoming':rm}),('review',result)]:
            (d/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        results.append({'ref':ref,'head':h,'ancestor':a,'counts':[len(b),len(l),len(r)],'manual_count':result['manual_count'],'case_collisions':result['case_collisions'],'mode_changes':mode_changes,'merge_authorized':False})
    if commit(repo,local)!=head or any(commit(repo,r)!=h for r,h in heads.items()):raise ValueError('REF_ADVANCED_HOLD')
    result={'local':head,'status':'REVIEW_REQUIRED','results':results,'merge_authorized':False,'remote_heads_are_not_atomic_locks':True}
    (output/'PREFLIGHT_REPORT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--ref',action='append',required=True);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    repo=a.repo.resolve()
    if commit(repo,'HEAD')!=BASE or git(repo,'status','--porcelain','--untracked-files=all'):raise ValueError('CLEAN_EXT06_CHECKOUT_HOLD')
    engine=load_exact(repo/'scripts/parallel_preflight.py');collect(repo,'HEAD',a.ref,engine,a.output.resolve())
