"""Exact original SQLite DDL and D4 Request; direct synthetic seed, not Store/Core run."""
from dataclasses import replace
from hashlib import sha1
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

HERE=Path(__file__).resolve().parent
SRC=HERE/'owner_sources'
PINS={'schema.sql':'32b7609b18e8a53420f17d23f4b53544e7f6f6ad','operations.sql':'3443f6581eb3a8d3894aea0b620f2b8d6dba9b2a','app/core/transaction/identity_binding.py':'e1e977880324664bb359eee3286223a796878f44'}
for path,expected in PINS.items():
    raw=(SRC/path).read_bytes()
    assert sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected
sys.path[:0]=[str(HERE),str(SRC)]
from assignment_lifecycle import *

K=(*SCOPE,'a'*64); PROJECT='demo-project'; PLAN='sha256:'+'b'*64
R=Request(SCOPE,PROJECT,PLAN,'research','demo-run-a','demo-agent-worker-a','demo-principal-a','f'*64,2,3)
P=AssignmentPin(R,K[-1],1,'c'*64,'d'*64,2,'2'*64,'1'*64,'worker-a','research',0,1,'7'*64,1,'8'*64,1,'9'*64)
A=ApprovalObservation('ACCEPT','demo-decision-a','demo-issuer','demo-custody',5,15)
V=ApprovalObservation('REVOKE','demo-decision-v','demo-issuer','demo-custody',11,30)

class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'org.db'; self.db=self.connect(); self.addCleanup(self.db.close)
        for p in (SRC/'schema.sql',SRC/'operations.sql',DDL): self.db.executescript(p.read_text())
        self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',(*K,1,None,'c'*64,None))
        self.db.execute('INSERT INTO org_head VALUES (?,?,?,?)',K)
        self.db.execute('INSERT INTO org_unit VALUES (?,?,?,?,?,?,?)',(*K,'root','company',None))
        for seat,role in (('lead','orchestrator'),('worker-a','research'),('worker-b','research')):
            self.db.execute('INSERT INTO org_position VALUES (?,?,?,?,?,?,?,?)',(*K,seat,'root',role,None if seat=='lead' else 'lead'))
            self.db.execute('INSERT INTO org_definition_ref VALUES (?,?,?,?,?,?)',(*K,'def-'+seat,role))
            self.db.execute('INSERT INTO org_instance_ref VALUES (?,?,?,?,?,?,?)',(*K,'demo-agent-'+seat,'def-'+seat,role))
            self.db.execute('INSERT INTO org_binding VALUES (?,?,?,?,?,?,?)',(*K,seat,'demo-agent-'+seat,role))
        self.db.execute('INSERT INTO op_team VALUES (?,?,?,?,?,?,?)',(*K,PROJECT,'lead','d'*64))
        for seat in ('lead','worker-a','worker-b'): self.db.execute('INSERT INTO op_member VALUES (?,?,?,?,?,?)',(*K,PROJECT,seat))
        for i,seat in enumerate(('worker-a','worker-b'),1):
            self.db.execute('INSERT INTO op_entry VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(*K,PROJECT,i,PLAN,'research','lead',seat,'delegation','research',str(i-1)*64,str(i)*64))
            self.db.execute('INSERT INTO op_notice VALUES (?,?,?,?,?,?,?,?)',(*K,PROJECT,i,'e'*64,'HOLD'))
    def connect(self):
        db=sqlite3.connect(self.path,isolation_level=None,timeout=3); db.execute('PRAGMA foreign_keys=ON'); return db
    def write(self,p=P,a=A,now=10,prev=ZERO,revoke=False,db=None):
        db=self.db if db is None else db; db.execute('BEGIN IMMEDIATE')
        try:
            result=append_decision(db,p,a,now,prev,revoke=revoke); db.commit(); return result
        except BaseException: db.rollback(); raise
    def read(self,p=P,sha=ZERO,now=10,db=None):
        db=self.db if db is None else db; db.execute('BEGIN')
        try: return inspect_assignment(db,p,sha,now)
        finally: db.rollback()
    def hold(self,r,match=False):
        self.assertEqual(r.structural_match,match); self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.authoritative or r.dispatch_allowed or r.commit_allowed or r.retry_allowed)
    def test_proposal_only(self): self.hold(self.read()); self.assertEqual(self.read().state,'MISSING_HOLD')
    def test_accept_persist_reopen(self):
        a=self.write(); self.hold(a,True); self.assertEqual(a.revision,1)
        with self.connect() as db: self.hold(self.read(sha=a.assignment_sha,db=db),True)
        self.assertEqual(self.db.execute('SELECT DISTINCT state FROM op_notice').fetchall(),[('HOLD',)])
    def test_revoke_persist(self):
        a=self.write(); v=self.write(a=V,now=12,prev=a.assignment_sha,revoke=True)
        self.assertEqual((v.state,v.revision),('REVOKED_D0',2)); self.hold(self.read(sha=v.assignment_sha,now=13),True)
        self.hold(self.read(sha=a.assignment_sha,now=13))
    def test_expiry_clock(self):
        a=self.write(); self.hold(self.read(sha=a.assignment_sha,now=14),True)
        for tick in (4,15,16,True,-1): self.hold(self.read(sha=a.assignment_sha,now=tick))
    def test_cas_stale(self):
        a=self.write(); self.assertRaises(ValueError,self.write,a=V,now=12,revoke=True)
        self.hold(self.read(sha=a.assignment_sha),True)
    def test_no_second_accept(self):
        a=self.write(); self.assertRaises(ValueError,self.write,prev=a.assignment_sha)
    def test_no_reaccept_after_revoke(self):
        a=self.write(); v=self.write(a=V,now=12,prev=a.assignment_sha,revoke=True)
        self.assertRaises(ValueError,self.write,prev=v.assignment_sha)
    def test_no_retarget_same_run(self):
        a=self.write(); p=replace(P,request=replace(R,agent='demo-agent-worker-b'),seat='worker-b',proposal_digest='2'*64)
        self.assertRaises(ValueError,self.write,p=p,prev=a.assignment_sha)
    def test_revoke_requires_exact_original(self):
        a=self.write(); self.assertRaises(ValueError,self.write,p=replace(P,core_version=1),a=V,now=12,prev=a.assignment_sha,revoke=True)
    def test_revoke_after_expiry(self):
        a=self.write(); v=self.write(a=V,now=16,prev=a.assignment_sha,revoke=True); self.hold(v,True)
    def test_invalid_refs(self):
        for field,value in [('org_head','0'*64),('org_sequence',2),('staffing_digest','0'*64),('team_digest','0'*64),('history_count',1),('history_head','0'*64),('proposal_digest','0'*64),('seat','worker-b'),('task_role','qa')]:
            with self.subTest(field=field): self.assertRaises(ValueError,self.write,p=replace(P,**{field:value}))
    def test_invalid_request(self):
        for field,value in [('scope',('synthetic-other',*SCOPE[1:])),('project','demo-other'),('plan_revision','sha256:'+'0'*64),('task','other'),('agent','demo-other'),('principal','real-principal')]:
            with self.subTest(field=field): self.assertRaises(ValueError,self.write,p=replace(P,request=replace(R,**{field:value})))
    def test_independent_pins(self):
        self.assertRaises(ValueError,self.write,p=replace(P,registry_sha=P.proposal_digest))
        self.assertRaises(ValueError,self.write,p=replace(P,membership_revision=True))
    def test_approval_boundary(self):
        for a in (replace(A,action='REVOKE'),replace(A,issuer=R.principal),replace(A,custody=A.issuer),replace(A,decision_ref='real-decision'),replace(A,expires_tick=10),replace(A,issued_tick=11)):
            self.assertRaises(ValueError,self.write,a=a)
    def test_stale_source_read(self):
        a=self.write(); self.db.execute('UPDATE org_head SET rev=rev WHERE t=? AND c=? AND e=?',SCOPE)
        self.db.execute('UPDATE op_team SET team_digest=? WHERE t=? AND c=? AND e=? AND rev=? AND project=?',('0'*64,*K,PROJECT))
        self.hold(self.read(sha=a.assignment_sha)); self.hold(self.write(a=V,now=12,prev=a.assignment_sha,revoke=True),True)
    def test_immutable_rows(self):
        a=self.write()
        for sql in ('UPDATE op_assignment_review SET state=state','DELETE FROM op_assignment_review'):
            self.assertRaises(sqlite3.IntegrityError,self.db.execute,sql)
        self.hold(self.read(sha=a.assignment_sha),True)
    def test_detect_tamper_against_pin(self):
        a=self.write(); self.db.execute('DROP TRIGGER op_assignment_review_no_update'); self.db.execute("UPDATE op_assignment_review SET body='{}'")
        self.hold(self.read(sha=a.assignment_sha))
    def test_rollback(self):
        self.db.execute('BEGIN IMMEDIATE'); append_decision(self.db,P,A,10,ZERO); self.db.rollback(); self.hold(self.read())
    def test_contention(self):
        barrier=Barrier(2)
        def attempt(_):
            db=self.connect()
            try:
                barrier.wait(timeout=5)
                try: return self.write(db=db).state
                except ValueError: return 'HOLD'
            finally: db.close()
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(attempt,range(2)))
        self.assertEqual(sorted(results),['ACCEPTED_D0','HOLD']); self.assertEqual(self.db.execute('SELECT count(*) FROM op_assignment_review').fetchone(),(1,))
    def test_no_transaction(self): self.assertRaises(ValueError,append_decision,self.db,P,A,10,ZERO)

if __name__=='__main__':
    print('EXACT_SOURCE_PINS 3/3; Python',sys.version.split()[0],'SQLite',sqlite3.sqlite_version,flush=True)
    unittest.main(verbosity=2)
