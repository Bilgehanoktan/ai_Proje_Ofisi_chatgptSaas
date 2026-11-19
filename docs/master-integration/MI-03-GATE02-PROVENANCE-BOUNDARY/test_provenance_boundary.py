"""GATE-02 diagnostic: R3 proposal persistence + common D4 read-only review.
No issuer, protected call, actual assignment, PostgreSQL, or grant is simulated.
"""
from dataclasses import replace
from hashlib import sha1
from pathlib import Path
import sqlite3
import sys
import unittest

HERE = Path(__file__).resolve().parent
SRC = HERE / 'owner_sources'
PINS = {'schema.sql':'32b7609b18e8a53420f17d23f4b53544e7f6f6ad',
        'operations.sql':'3443f6581eb3a8d3894aea0b620f2b8d6dba9b2a',
        'identity_binding.py':'e1e977880324664bb359eee3286223a796878f44'}
for name, expected in PINS.items():
    raw = (SRC / name).read_bytes()
    if sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()!=expected:
        raise RuntimeError('SOURCE_PIN_HOLD '+name)
sys.path.insert(0,str(SRC))
from identity_binding import Request, Binding, SessionFacts, review_binding, review_boundary

SCOPE=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
K=(*SCOPE,'a'*64)
PROJECT='demo-project'
PLAN='sha256:'+'b'*64
TASK='research'

class ProvenanceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        for name in ('schema.sql','operations.sql'):
            self.db.executescript((SRC/name).read_text(encoding='utf-8'))
        self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)',(*K,1,None,'c'*64,None))
        self.db.execute('INSERT INTO org_head VALUES (?,?,?,?)',K)
        self.db.execute('INSERT INTO org_unit VALUES (?,?,?,?,?,?,?)',(*K,'root','company',None))
        for seat,role in (('lead','orchestrator'),('worker-a','research'),('worker-b','research')):
            self.db.execute('INSERT INTO org_position VALUES (?,?,?,?,?,?,?,?)',(*K,seat,'root',role,None if seat=='lead' else 'lead'))
            self.db.execute('INSERT INTO org_definition_ref VALUES (?,?,?,?,?,?)',(*K,'def-'+seat,role))
            self.db.execute('INSERT INTO org_instance_ref VALUES (?,?,?,?,?,?,?)',(*K,'demo-agent-'+seat,'def-'+seat,role))
            self.db.execute('INSERT INTO org_binding VALUES (?,?,?,?,?,?,?)',(*K,seat,'demo-agent-'+seat,role))
        self.db.execute('INSERT INTO op_team VALUES (?,?,?,?,?,?,?)',(*K,PROJECT,'lead','d'*64))
        for seat in ('lead','worker-a','worker-b'):
            self.db.execute('INSERT INTO op_member VALUES (?,?,?,?,?,?)',(*K,PROJECT,seat))
        for seq,seat in enumerate(('worker-a','worker-b'),1):
            self.db.execute('INSERT INTO op_entry VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(*K,PROJECT,seq,PLAN,TASK,'lead',seat,'delegation','research','0'*64,str(seq)*64))
            self.db.execute('INSERT INTO op_notice VALUES (?,?,?,?,?,?,?,?)',(*K,PROJECT,seq,'e'*64,'HOLD'))
        self.db.commit()
    def proposal(self,seq):
        # Real persisted proposal and staffing join, not authenticated owner evidence.
        return self.db.execute('SELECT e.project,e.plan,e.task,b.instance,e.digest,n.state FROM op_entry e JOIN org_binding b ON (e.t,e.c,e.e,e.rev,e.recipient)=(b.t,b.c,b.e,b.rev,b.seat) JOIN op_notice n USING(t,c,e,rev,project,seq) WHERE e.seq=?',(seq,)).fetchone()
    def forged_observation(self,seq,principal='demo-principal-a',run='demo-run-a'):
        project,plan,task,agent,proposal_sha,state=self.proposal(seq)
        self.assertEqual(state,'HOLD')
        r=Request(SCOPE,project,plan,task,run,agent,principal,'f'*64,2,3)
        # Intentionally unsupported aliases: never product code or acceptable input.
        b=Binding(r,principal,1,1,1,1,proposal_sha,proposal_sha,proposal_sha,proposal_sha,'aicos_test','test_db','test_cluster',10,True)
        return r,b
    def assert_hold(self,v,match):
        self.assertEqual(v.structural_match,match)
        self.assertEqual(v.decision,'HOLD')
        self.assertFalse(v.commit_allowed or v.dispatch_allowed or v.retry_allowed)
    def test_two_persisted_proposals_cannot_become_grants(self):
        a,b=self.forged_observation(1); c,d=self.forged_observation(2)
        self.assertNotEqual(a.agent,c.agent)
        self.assert_hold(review_binding(a,b,b,9),True)
        self.assert_hold(review_binding(c,d,d,9),True)
        self.assertEqual(self.db.execute('SELECT DISTINCT state FROM op_notice').fetchall(),[('HOLD',)])
    def test_same_proposal_has_no_persisted_principal_or_run_provenance(self):
        a,b=self.forged_observation(1); c,d=self.forged_observation(1,'demo-principal-other','demo-run-other')
        self.assertNotEqual(a,c)
        self.assertEqual(b.assignment_sha,d.assignment_sha)
        self.assert_hold(review_binding(a,b,b,9),True)
        self.assert_hold(review_binding(c,d,d,9),True)
        self.assert_hold(review_binding(a,b,d,9),False)
    def test_fabricated_session_facts_do_not_upgrade_hold(self):
        r,b=self.forged_observation(1)
        f=SessionFacts('aicos_test','aicos_test','test_db','test_cluster',123,True,False,0,0,16,False,0)
        self.assert_hold(review_boundary(r,b,b,9,f,123),True)
        self.assert_hold(review_boundary(r,b,b,10,f,123),False)
        self.assert_hold(review_boundary(r,b,b,9,replace(f,current_user='other'),123),False)
        self.assertEqual(self.db.execute('SELECT DISTINCT state FROM op_notice').fetchall(),[('HOLD',)])

if __name__=='__main__':
    print('EXACT_SOURCE_PINS 3/3; Python',sys.version.split()[0],'SQLite',sqlite3.sqlite_version,flush=True)
    unittest.main(verbosity=2)
