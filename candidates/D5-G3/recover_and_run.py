"""Reconstruct exact D5-G2 backend from an existing D5-C checkout and the 4-file G2 delta.
No network, installation, PostgreSQL, migration, or product activation. Uses the original G2 runner.
"""
from pathlib import Path
from hashlib import sha1, sha256
import argparse
import json
import subprocess
import sys
import tempfile
from importlib.metadata import version, PackageNotFoundError

BASE_COMMIT = '9b66592ff67638e0a1504d327c6cf95ef4d7ac21'
TARGET_COMMIT = '9ca667e816dac269084ef8f62051da5fe458eb12'
BASE_MANIFEST = '981a13fc226184dc3a911ae0d94e0042285ff302'
TARGET_MANIFEST = '15e446e4d14c95d81d1e152efa2e8cb11122b3e3'
RUNNER = 'candidates/D5-G2/run_regression.py'
RUNNER_BLOB = 'f7df7e5cc0e6cd8f42e7320d76c55e3b06e8dec5'
BACKEND = 'ai-company-os-backend/'
DELTA = {
    BACKEND+'app/core/iam_session.py': ('f3c37428acd475e09c228bce47d534d6584cd944',15424,'f2850117721cad5d8b5f0d981a8562da8f81359fae9aa9b28c46b63b8b3193e3'),
    BACKEND+'app/core/transaction/intent_authority.py': ('b28788f46a39c282d79d29c4abd817ed5fc9de99',9184,'2230e1e11f6483e092085c329f233c2ea01d800e3adbf466367f25a49bbb1eb1'),
    BACKEND+'tests/test_iam_authority_d5g2.py': ('16bfc7013ae77cdcf437227b9fb6ac8a9a69d08c',11216,'d3ee505241afee5255080ce046bd078d76e9e12dce8c1c438f1cf228b2f1f043'),
    BACKEND+'tests/test_iam_session_d5g1.py': ('6be21cfdcaf7408d7d17b5848966bb7f6772581e',4691,'9f5361d9da2b2757a35bb0cdce9aeb1f5804483a0468f60c69abdc0235072ecc'),
}
DDL = {
    'database/0192/candidate_event_outbox_fence.sql':'6e4780bf9f267c0926b40d582d5afdbd6faa543c',
    'database/0193/candidate_run_head.sql':'180924e97ee1f31fa27332941a41e37fdf73017e',
    'database/0194/candidate_transition_roles.sql':'7b5d374bb7973b283e4fcfa0d796ed6128ef9d27',
}


def require(ok, label):
    if not ok:
        raise ValueError(label)


def blob(data):
    return sha1(b'blob '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()


def read(root, relative):
    p = root / relative
    require(p.is_relative_to(root) and p.resolve() == p and p.is_file(), 'SOURCE_PATH_HOLD '+relative)
    return p.read_bytes()


def verify_delta(root):
    """Read the exact 4 G2 files and unchanged G2 runner; reject any drift."""
    data = {}
    for key,(pin,size,digest) in DELTA.items():
        raw = read(root,'product/'+key)
        require((blob(raw),len(raw),sha256(raw).hexdigest()) == (pin,size,digest), 'DELTA_PIN_HOLD '+key)
        data[key] = raw
    runner = read(root,RUNNER)
    require(blob(runner) == RUNNER_BLOB,'RUNNER_PIN_HOLD')
    return data,runner


def rebuild_manifest(raw):
    """Reproduce the exact GitHub G2 manifest, not a relaxed or synthetic manifest."""
    require(blob(raw) == BASE_MANIFEST,'BASE_MANIFEST_HOLD')
    m = json.loads(raw)
    files = m['files']
    require(len(files) == 392 and sum(k.startswith(BACKEND) for k in files) == 237,'BASE_INVENTORY_HOLD')
    existing = [k for k in DELTA if k in files]
    require(existing == [BACKEND+'app/core/transaction/intent_authority.py'],'DELTA_PREIMAGE_HOLD')
    require(files[existing[0]] == {'bytes':7835,'sha256':'1f9e3c675062601be45e933be9ce21e9cb11fa88f8abf545df54336afab7a392'},'AUTHORITY_PREIMAGE_HOLD')
    for key,(_,size,digest) in DELTA.items():
        files[key] = {'bytes':size,'sha256':digest}
    m['files'] = dict(sorted(files.items()))
    m['doc_revision'] = 'D5-G2'
    m['status'] = 'D0_ISOLATED_IAM_AUTHORITY_COMPONENT_TESTED_NOT_ACTIVATED'
    m['parent_git_commit'] = '78da1ae5da98e40c256824b53558811dc412704c'
    m['parent_source_manifest_blob'] = '40136a75e9bda468a5661932e94cf276707a81f8'
    m['source_git_commit'] = None
    m['source_git_commit_note'] = 'Current commit cannot self-reference; exact branch commit and readback. Three product entries changed; remaining entries retained.'
    result = (json.dumps(m,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    require(len(m['files'])==395 and sum(k.startswith(BACKEND) for k in m['files'])==240,'TARGET_INVENTORY_HOLD')
    require(blob(result) == TARGET_MANIFEST,'TARGET_MANIFEST_HOLD')
    return result


def stage_exact(base, delta, stage):
    """Read and verify original backend + DDL; never modify original files."""
    original = read(base,'product/SOURCE_MANIFEST.json')
    target = rebuild_manifest(original)
    patches,runner = verify_delta(delta)
    entries = {k:v for k,v in json.loads(original)['files'].items() if k.startswith(BACKEND)}
    def put(relative,data):
        dest = stage / relative
        require(dest.is_relative_to(stage),'STAGE_PATH_HOLD')
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:
            f.write(data)
    for key,v in entries.items():
        raw = read(base,'product/'+key)
        require((len(raw),sha256(raw).hexdigest()) == (v['bytes'],v['sha256']),'BASE_FILE_HOLD '+key)
        if key not in patches:
            put('product/'+key,raw)
    for key,raw in patches.items():
        put('product/'+key,raw)
    for relative,pin in DDL.items():
        raw = read(base,relative)
        require(blob(raw)==pin,'DDL_PIN_HOLD '+relative)
        put(relative,raw)
    put('product/SOURCE_MANIFEST.json',target)
    put(RUNNER,runner)
    # Exact G2 manifest validates all staged backend bytes, including all 4 delta files.
    target_entries = {k:v for k,v in json.loads(target)['files'].items() if k.startswith(BACKEND)}
    for key,v in target_entries.items():
        raw = read(stage,'product/'+key)
        require((len(raw),sha256(raw).hexdigest())==(v['bytes'],v['sha256']),'STAGED_FILE_HOLD '+key)
    return {'base_backend_verified':len(entries),'delta_files_verified':len(patches),'unchanged_backend':236,
            'ddl_verified':len(DDL),'target_backend_verified':len(target_entries),'target_manifest_blob':blob(target),
            'runner_blob':blob(runner),'scope':'exact selected backend closure; not a full product checkout'}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',required=True,help='Extracted original D5-C root containing product/SOURCE_MANIFEST.json')
    p.add_argument('--delta',default=str(Path(__file__).resolve().parents[2]),help='Extracted G2/G3 delta root')
    p.add_argument('--out',required=True,help='Fresh evidence directory; must not already exist')
    args = p.parse_args(argv)
    base,delta,out = (Path(x).resolve() for x in (args.base,args.delta,args.out))
    require(not out.is_relative_to(base) and not out.is_relative_to(delta),'EVIDENCE_PATH_HOLD')
    out.mkdir(parents=True,exist_ok=False)
    report = {'base_commit':BASE_COMMIT,'target_commit':TARGET_COMMIT,'status':'BLOCKED','tests':'NOT_RUN','exit_code':2}
    try:
        require(version('cryptography')=='46.0.4','CRYPTOGRAPHY_HOLD')
        with tempfile.TemporaryDirectory(prefix='d5g3-recover-') as td:
            stage = Path(td).resolve()
            report['verified'] = stage_exact(base,delta,stage)
            print('SOURCE_VERIFIED:',json.dumps(report['verified']),flush=True)
            result = subprocess.run([sys.executable,'-I','-B',str(stage/RUNNER),str(stage)],cwd=stage,
                                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False)
            (out/'regression.log').write_bytes(result.stdout)
            print(result.stdout.decode('utf-8',errors='replace'),end='',flush=True)
            log = result.stdout.decode('utf-8',errors='replace').splitlines()
            complete = any(line.startswith('Ran 50 tests in ') for line in log) and 'OK' in log
            report['log_sha256'] = sha256(result.stdout).hexdigest()
            report['runner_exit_code'] = result.returncode
            report['exit_code'] = 0 if result.returncode == 0 and complete else 1
            report['status'] = 'PASS_SELECTED_D0_REGRESSION' if report['exit_code']==0 else 'FAIL_OR_INCOMPLETE'
            report['tests'] = '50/50 PASS' if report['exit_code']==0 else 'REVIEW_RAW_LOG'
    except (ValueError,OSError,KeyError,TypeError,PackageNotFoundError) as e:
        report['blocker'] = str(e)
        print('REGRESSION_BLOCKED:',e,flush=True)
    finally:
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        (out/'exit_code.txt').write_text(str(report['exit_code'])+'\n',encoding='ascii')
    return report['exit_code']


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError,OSError) as e:
        print('REGRESSION_BLOCKED:',e)
        sys.exit(2)
