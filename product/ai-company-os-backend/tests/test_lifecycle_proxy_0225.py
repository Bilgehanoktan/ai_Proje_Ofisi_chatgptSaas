"""Real loopback ASGI HTTP -> exact compiled frontend proxy/parser -> Studio HOLD.
Diagnostic TS subset, not a Next build, React mount, or browser acceptance.
"""
from contextlib import closing
from pathlib import Path
import os
import socket
import sqlite3
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import uvicorn
from test_lifecycle_db_http_0225 import make_app, write_fixture

FRONTEND=Path(__file__).resolve().parents[2]/'ai-company-os-frontend'
NODE_CHECK=r'''
const assert=require('node:assert/strict'),path=require('node:path');
const out=process.argv[1],version=Number(process.argv[2]),mode=process.argv[3];
const {GET}=require(path.join(out,'app/api/demo/shared-snapshot/route.js'));
const {parseSharedReplay}=require(path.join(out,'features/data/sharedSnapshot.js'));
const {readPlanProjection}=require(path.join(out,'features/core-review/planProjection.js'));
const {reviewStudioEvidence}=require(path.join(out,'features/mvp/studioContext.js'));
(async()=>{
 const req=new Request('http://localhost/api/demo/shared-snapshot',{headers:mode==='resume'?{'Last-Event-ID':'1'}:{}});
 const r=await GET(req);assert.equal(r.headers.get('cache-control'),'no-store');
 if(mode!=='good'){assert.equal(r.status,503);assert.deepEqual(await r.json(),{mode:'D0_SHARED_SNAPSHOT_HOLD'});return;}
 assert.equal(r.status,200);const sample=await parseSharedReplay(await r.text());
 assert.equal(sample.snapshot_seq,version);assert.equal(sample.prefix.head_version,version);
 assert.equal(sample.prefix.timeline.length,version);assert.equal(sample.project_id,null);assert.equal(sample.world_id,null);
 assert.equal(sample.prefix.dispatch_allowed,false);
 const plan=readPlanProjection();assert.equal(plan.ok,true);
 const studio=reviewStudioEvidence(plan.plan,{kind:'task',id:'research'},sample);
 assert.equal(studio.reason,'PLAN_REVISION_MISMATCH');assert.equal(studio.joinAllowed,false);
 assert.equal(studio.assignment,null);assert.equal(studio.observation.runId,'demo-a');
 assert.equal(studio.observation.sequence,version);
 console.log(JSON.stringify({version,proxy:r.status,studio:studio.reason,digest:sample.digest}));
})().catch(e=>{console.error(e);process.exitCode=1});
'''


class LifecycleProxyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.tmp.cleanup)
        cls.root=Path(cls.tmp.name);cls.out=cls.root/'compiled';cls.path=cls.root/'lifecycle-prefix.d0.sqlite'
        sources=['app/api/demo/shared-snapshot/route.ts','features/core-review/planProjection.ts','features/mvp/studioContext.ts']
        if not (FRONTEND/'node_modules/@types/node').is_dir():
            declaration=cls.root/'process.d.ts'
            declaration.write_text('declare const process: {env: Record<string,string|undefined>};\n',encoding='utf-8')
            sources.append(str(declaration))
        subprocess.run([os.environ.get('AICOS_TSC','tsc'),'--target','ES2022','--lib','ESNext,DOM','--strict',
            '--module','commonjs','--esModuleInterop','--resolveJsonModule','--rootDir',str(FRONTEND),
            '--outDir',str(cls.out),*sources],cwd=FRONTEND,check=True,timeout=30)
        sock=socket.socket();cls.addClassCleanup(sock.close)
        for port in range(18325,18355):
            try:sock.bind(('127.0.0.1',port));break
            except OSError:continue
        else:raise RuntimeError('no loopback test port')
        sock.listen(128);cls.port=port
        cls.env=patch.dict(os.environ,{'AICOS_D0_LIFECYCLE_PREFIX_DB':str(cls.path)});cls.env.start();cls.addClassCleanup(cls.env.stop)
        cls.server=uvicorn.Server(uvicorn.Config(make_app(),log_level='error',lifespan='off'))
        cls.thread=threading.Thread(target=cls.server.run,kwargs={'sockets':[sock]},daemon=True)
        cls.thread.start();cls.addClassCleanup(cls.stop_server)
        deadline=time.monotonic()+5
        while not cls.server.started and cls.thread.is_alive() and time.monotonic()<deadline:time.sleep(.02)
        if not cls.server.started:raise RuntimeError('loopback ASGI startup failed')
    @classmethod
    def stop_server(cls):
        cls.server.should_exit=True;cls.thread.join(5)
        if cls.thread.is_alive():raise RuntimeError('loopback ASGI did not stop')
    def setUp(self):
        if self.path.exists():self.path.unlink()
    def check(self,version,mode='good'):
        if version:write_fixture(self.path,version)
        if mode=='tamper':
            with closing(sqlite3.connect(self.path)) as db,db:db.execute("UPDATE run_heads SET principal_id='demo-forged' WHERE task_id='a'")
        p=subprocess.run([os.environ.get('AICOS_NODE','node'),'-e',NODE_CHECK,str(self.out),str(version),mode],
            env={**os.environ,'AICOS_D0_BACKEND_PORT':str(self.port)},capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        if p.stdout:print(p.stdout.strip(),flush=True)
    def test_prefix_one(self):self.check(1)
    def test_prefix_two(self):self.check(2)
    def test_prefix_three(self):self.check(3)
    def test_prefix_four(self):self.check(4)
    def test_tampered_database_proxy_hold(self):self.check(3,'tamper')
    def test_missing_database_proxy_hold(self):self.check(0,'missing')
    def test_resume_denied(self):self.check(2,'resume')
