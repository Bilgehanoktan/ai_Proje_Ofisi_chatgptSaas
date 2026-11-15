"""Exercise existing 0188 CLI, readers, schema and compiled loopback proxy.
Run only against an isolated reviewed checkout; no provider or actual agent calls.
"""
import json
import hashlib
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from contextlib import closing
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'product/ai-company-os-backend'
FRONTEND = ROOT / 'product/ai-company-os-frontend'
URL = 'http://127.0.0.1:8000/demo/v1/task-budget/sample-projection'


def checked(*args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True, capture_output=True, timeout=30).stdout


def run():
    # Refuse to use an existing service. A concurrent bind can still fail; verify pair identity.
    with socket.socket() as s:
        s.bind(('127.0.0.1', 8000))
    with tempfile.TemporaryDirectory(prefix='aicos-pair-0189-') as tmp:
        root = Path(tmp); ts = root/'ts'
        checked('tsc','--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--outDir',str(ts),'features/mvp/taskBudgetProjection.ts','app/api/demo/task-budget/route.ts',cwd=FRONTEND)
        read_code = ('import json,sys; from app.core.development_review.task_budget_snapshot import read_task_budget_snapshot; '
                     'print(json.dumps(read_task_budget_snapshot(sys.argv[1],sys.argv[2]),sort_keys=True))')
        schema_code = ('import json,sys; from jsonschema import Draft202012Validator; '
                       's=json.load(open("contracts/source/task.budget.snapshot.schema.json")); '
                       'Draft202012Validator.check_schema(s); Draft202012Validator(s).validate(json.loads(sys.argv[1]))')
        for outcome, phase, amounts in [('reserved','RESERVED',(100,0,900)),('known','SETTLED_SAMPLE',(0,60,940)),('unknown','UNKNOWN_HOLD',(100,0,900))]:
            directory = root/outcome
            raw = checked(sys.executable,'-m','app.core.development_review.paired_demo','--directory',str(directory),'--outcome',outcome,cwd=BACKEND)
            w=directory/'demo.workbench.d0.sqlite'; a=directory/'demo.admission.d0.sqlite'
            x=json.loads(raw); reopened=json.loads(checked(sys.executable,'-c',read_code,str(w),str(a),cwd=BACKEND))
            checked(sys.executable,'-c',schema_code,raw,cwd=BACKEND)
            actual=tuple(x['budget'][k] for k in ('sample_reserved_minor','sample_observed_minor','sample_remaining_minor'))
            if x!=reopened or x['budget']['phase']!=phase or actual!=amounts or x['workbench_event_seq']!=5 or x['research_event_seq']!=3 or any(x[k] is not False for k in ('dispatch_allowed','spend_allowed','release_ready','authoritative')):
                raise RuntimeError('PAIR_CLI_READBACK_HOLD')
            print(f'PASS CLI {outcome}, schema and reopen: {phase} {actual}')
        # Last pair is UNKNOWN. Fixed local proxy target, isolated router only.
        env={**os.environ,'AICOS_D0_WORKBENCH_DB':str(w),'AICOS_D0_ADMISSION_DB':str(a)}
        server_code=('from fastapi import FastAPI; from app.api.task_budget_projection import router; '
                     'import uvicorn; app=FastAPI(); app.include_router(router); '
                     'uvicorn.run(app,host="127.0.0.1",port=8000,log_level="warning")')
        proc=subprocess.Popen([sys.executable,'-c',server_code],cwd=BACKEND,env=env)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def http():
            try:
                with opener.open(URL,timeout=2) as r: return r.status,json.load(r)
            except urllib.error.HTTPError as e: return e.code,json.load(e)
        def proxy():
            route=json.dumps(str(ts/'app/api/demo/task-budget/route.js'))
            code=f'const {{GET}}=require({route}); GET().then(async r=>console.log(JSON.stringify([r.status,await r.json()]))).catch(e=>{{console.error(e);process.exit(1)}})'
            return json.loads(checked('node','-e',code,cwd=FRONTEND))
        try:
            for _ in range(50):
                if proc.poll() is not None: raise RuntimeError('PAIR_SERVER_EXITED')
                try: http(); break
                except OSError: time.sleep(.1)
            else: raise RuntimeError('PAIR_SERVER_START_HOLD')
            before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (w,a)]
            if proc.poll() is not None or http()!=(200,x) or proxy()!=[200,x]: raise RuntimeError('PAIR_HTTP_HOLD')
            if before!=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (w,a)]: raise RuntimeError('PAIR_GET_MUTATED')
            print('PASS actual HTTP and compiled proxy 200; both file hashes unchanged')
            with closing(sqlite3.connect(a)) as db,db: db.execute('UPDATE sample_pair SET pair_id=?',(uuid4().hex,))
            if http()[0]!=503 or proxy()[0]!=503: raise RuntimeError('PAIR_MISMATCH_NOT_DENIED')
            print('PASS cross-pair actual HTTP and proxy 503')
        finally:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)


if __name__ == '__main__':
    run()
