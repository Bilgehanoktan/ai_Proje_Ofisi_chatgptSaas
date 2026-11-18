"""Verify pinned parent bytes and execute local disposable tests. No network/PG/product.
Does not rerun W5-J original 170 tests or owner-specific D4/D5/ORG acceptance.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from fixture_patch import write_fixture

HERE=Path(__file__).resolve().parent
PINS=(('R1',9,'4620e3f6ec33041d4bce192d92a4a99b7036683c9ae4de94978de56bf327ee25'),
      ('R2',10,'7d374aa372f44a343732895a7baed1bd4d04d7dc80d60ab09501c1bb831b7b0b'),
      ('R3',12,'6a2fbe13d95e98ebc607465f77bbc09046d147978fe1947fb60b978ed612edac'))
PATCHED_SHA='b9bde3fa7b41cdca720737543225d2236ed1ac58b4bd9bf76f1a1ccd96a3c3f7'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('DUPLICATE_MANIFEST_KEY')
        out[k]=v
    return out

def verify(root):
    count=0
    for name,n,pin in PINS:
        p=root/('W5-J2-'+name);raw=(p/'SOURCE_MANIFEST.json').read_bytes()
        if sha(raw)!=pin: raise ValueError('MANIFEST_PIN_HOLD')
        m=json.loads(raw,object_pairs_hook=unique)
        if len(m)!=n: raise ValueError('MANIFEST_COUNT_HOLD')
        for f,e in m.items():
            if Path(f).name!=f or f in ('.','..') or (p/f).is_symlink(): raise ValueError('MANIFEST_PATH_HOLD')
            data=(p/f).read_bytes()
            if len(data)!=e['bytes'] or sha(data)!=e['sha256']: raise ValueError('SOURCE_PIN_HOLD')
            count+=1
    return count

def run_group(root,paths,names,count,label):
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(str(x) for x in paths),PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run([sys.executable,'-B','-m','unittest','-v',*names],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out=result.stdout.decode('utf-8',errors='strict'); print(f'=== {label} ==='); print(out,end='')
    ids=[line.split(' ... ')[0] for line in out.splitlines() if line.endswith(' ... ok')]
    if result.returncode or len(ids)!=count or len(set(ids))!=count or not re.search(rf'^Ran {count} tests? in ',out,re.M) or not re.search(r'^OK\s*$',out,re.M):
        raise ValueError('EXACT_TEST_COUNT_OR_RESULT_HOLD:'+label)

if __name__=='__main__':
    root=HERE.parent
    print('PARENT_MANIFEST_VERIFIED',verify(root))
    with tempfile.TemporaryDirectory(prefix='w5-r4-') as tmp:
        stage=Path(tmp)
        # Copy only verified source/test inputs; keep relative structure expected by R3 tests.
        c=stage/'candidates';c.mkdir()
        for name,n,pin in PINS:
            src=root/('W5-J2-'+name);dst=c/src.name;dst.mkdir()
            m=json.loads((src/'SOURCE_MANIFEST.json').read_bytes())
            for f in m: shutil.copyfile(src/f,dst/f)
            shutil.copyfile(src/'SOURCE_MANIFEST.json',dst/'SOURCE_MANIFEST.json')
        d=c/HERE.name;d.mkdir()
        for f in ('fixture_patch.py','operation_contract.py','test_operation_contract.py','test_partial_close.py'): shutil.copyfile(HERE/f,d/f)
        r1=c/'W5-J2-R1';r2=c/'W5-J2-R2';r3=c/'W5-J2-R3'
        run_group(stage,[r1,r2,r3],['test_checkpoint','test_terminal_diagnostic','test_allocation_fixture','test_membership_review','test_physical_constraints'],121,'ORIGINAL R1-R3')
        run_group(stage,[r1,r2,r3,d],['test_operation_contract','test_partial_close'],56,'R4 NEW')
        patched=stage/'patched';patched.mkdir()
        generated=write_fixture(r2/'allocation_fixture.py',patched/'allocation_fixture.py')
        if generated!=PATCHED_SHA: raise ValueError('PATCHED_FIXTURE_PIN_HOLD')
        run_group(stage,[patched,r1,r2],['test_allocation_fixture'],48,'R2 COMPATIBILITY ON R4 FIXTURE (OVERLAP)')
        print('PASS: 177 UNIQUE CASES; 225 EXECUTIONS INCLUDING 48 COMPATIBILITY RERUNS; PG NOT_RUN')
