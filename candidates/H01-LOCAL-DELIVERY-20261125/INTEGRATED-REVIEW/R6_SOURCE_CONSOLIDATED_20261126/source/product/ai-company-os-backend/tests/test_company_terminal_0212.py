"""Original company and terminal decorators composed with original T1 on SQLite.
No live authority, PostgreSQL lock/RLS, or production acceptance.
"""
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sqlite3
from unittest import TestCase
import test_admission_mapping_0195 as base
from test_transition_mapping_0194 import PLAN, obs, SQLiteConnectionShim, SQLiteCursorShim
from test_terminal_anchor_lifecycle_0203 import SnapshotConnection
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import transition_digest
from app.core.transaction.port import LogicalT1Coordinator
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.postgres_admission_mapping import D0PostgresAdmissionMapping
from app.core.transaction.postgres_lifecycle_mapping import (AdmissionBinding, LifecycleSpec,
    D0AdmissionBoundTransitionMapping, D0PostgresLifecycleMapping, lifecycle_digest, FAILURE)
from app.core.transaction.postgres_transition_mapping import transaction_ref
from app.core.event_store.company_coordination import (SCOPE, Member, Allocation, Pool, CompanyEvent,
    CompanyCoordinatedMapping, inspect_company)
from app.core.event_store.history_readback import OrdinaryPin, LifecyclePin
from app.core.event_store.plan_history_review import RunHistoryPin, inspect_plan_history
from app.core.event_store.retained_history import ReferenceStore, ReferenceReader, reference_bytes, history_reference
from app.core.event_store.terminal_anchor import TerminalAnchorMapping, verify_plan_anchors
from app.core.event_store.signed_history import Checkpoint, ExternalPin, TerminalClaim, checkpoint_bytes, terminal_bytes, review_signed_snapshot
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class CompanyTerminalTests(TestCase):
    def setUp(self):
        f=base.ClaimTests();f.setUp();self.addCleanup(f.doCleanups);self.f=f;self.path=f.path
        self.initial=base.spec_for();self.admit=base.intent_for(self.initial);self.binding=AdmissionBinding(self.initial,self.admit)
        self.clock=replace(base.CLOCK,now_tick=11)
        self.members=tuple(Member('project-a',r.scope.plan_revision,r.scope.task_id,r.scope.run_id,
                                  r.scope.agent_instance_id,r.scope.principal_id,r.version) for r in (obs(t) for t in 'abcq'))
        b=base.BUDGET;self.pool=Pool(b.budget_id,b.currency,b.limit_minor,b.revision,b.policy_epoch,b.witness_epoch,b.source_digest,(Allocation('project-a',100),))
        self.history=();self.commands=();self.before=self.initial.before;self.lease=self.initial.lease;self.budget=b
        self.archive=ReferenceStore(self.path.with_name('references.sqlite'));self.reader=ReferenceReader(self.archive.path)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('PRAGMA foreign_keys=ON')
            for f in ('0196L/candidate_lease_settlement.sql','0203T/terminal_command_anchors.sql','0204C/company_event_order.sql'):
                db.executescript((base.ROOT/'database'/f).read_text().replace('t1_candidate.',''))
            for m in self.members:db.execute('INSERT INTO company_run_membership VALUES (?,?,?,?,?,?,?,?,?,?)',(*SCOPE,*m.row()))
            db.execute('INSERT INTO company_stream_heads VALUES (?,?,?,0)',SCOPE)

    def event(self,i,kind,budget_rev=None,amount=0):
        return CompanyEvent(len(self.history)+1,'project-a',i.scope.run_id,i.expected_version+1,
            transaction_ref(i),i.request_digest,kind,() if not self.history else (self.history[-1].transaction_ref,),budget_rev,amount)

    def execute(self,mapping,i,event,transition=None,unknown=False,record=True):
        mapping=CompanyCoordinatedMapping(mapping,self.members,self.pool,self.history,event)
        c=LogicalT1Coordinator(lambda:postgres_transaction(lambda:SQLiteConnectionShim(self.path,unknown),mapping))
        r=c.commit(i) if transition is None else c.commit_transition(i,*transition)
        if record:self.history+=event,
        return r

    def admission(self):
        i=self.admit;e=self.event(i,'D0_RUN_ADMISSION',0,self.initial.amount_minor)
        self.execute(D0PostgresAdmissionMapping(PLAN,self.initial,lambda:base.CLOCK),i,e)
        self.before=replace(self.before,state=RunState.ADMITTED,version=1)
        self.budget=replace(self.budget,revision=1,outstanding_minor=20)

    def ordinary(self,target):
        b=self.before;l=self.lease;v=b.version
        i=LogicalIntent(b.scope,Operation.STATE_MUTATION,v,transition_digest(b,target),'ordinary-'+str(v),'ordinary-idem-'+str(v),l.grant_id,l.lease_id,None,2,3)
        e=self.event(i,'D0_RUN_TRANSITION')
        self.execute(D0AdmissionBoundTransitionMapping(self.binding,l,lambda:self.clock),i,e,(b,target))
        self.commands+=OrdinaryPin(i,b,target,l),
        self.before=replace(b,state=target,version=v+1)

    def renewal(self):
        l=self.lease;n=replace(l,lease_version=l.lease_version+1,heartbeat_revision=l.heartbeat_revision+1,heartbeat_tick=11,expires_tick=31)
        s=LifecycleSpec(self.before,l,self.binding,self.budget,n)
        i=LogicalIntent(s.before.scope,Operation.STATE_MUTATION,s.before.version,lifecycle_digest(s),'renew','renew-idem',l.grant_id,l.lease_id,s.budget.budget_id,2,3,True)
        self.execute(D0PostgresLifecycleMapping(s,lambda:self.clock),i,self.event(i,'D0_LEASE_RENEWAL',self.budget.revision))
        self.commands+=LifecyclePin(i,s),;self.lease=n;self.before=replace(self.before,version=self.before.version+1)
        self.budget=replace(self.budget,revision=self.budget.revision+1)

    def terminal(self):
        l=self.lease;s=LifecycleSpec(self.before,l,self.binding,self.budget,outcome=FAILURE)
        i=LogicalIntent(s.before.scope,Operation.TERMINAL,s.before.version,lifecycle_digest(s),'terminal','terminal-idem',l.grant_id,l.lease_id,s.budget.budget_id,2,3,True)
        pin=LifecyclePin(i,s);key=self.archive.put(reference_bytes('terminal-command-v1',pin))
        return TerminalAnchorMapping(s,lambda:self.clock,self.reader,key),i,self.event(i,'D0_RUN_FAILURE',self.budget.revision,20),pin

    def chain(self):
        self.admission();self.ordinary(RunState.RUNNING);self.renewal();self.ordinary(RunState.VERIFYING)

    def company(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('PRAGMA query_only=ON');db.execute('BEGIN')
            with SQLiteCursorShim(db) as c:return inspect_company(c,self.members,self.pool,self.history)

    def dump(self):
        with closing(sqlite3.connect(self.path)) as db:
            tables=db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            return tuple((t,tuple(db.execute('SELECT * FROM '+t+' ORDER BY 1,2,3').fetchall())) for t, in tables)

    def pins(self):
        return tuple(RunHistoryPin(obs(t),self.binding if t=='a' else None,self.commands if t=='a' else ()) for t in 'abcq')

    def signed(self):
        pins=self.pins();rev=self.initial.before.scope.plan_revision;last=self.commands[-1]
        key=self.archive.put(reference_bytes('terminal-command-v1',last));h=self.archive.put(history_reference(PLAN,rev,pins,(base.BUDGET,)))
        claim=TerminalClaim(last.intent.scope.run_id,key,transaction_ref(last.intent),FAILURE)
        c=Checkpoint(*SCOPE,rev,h,'demo-iv','iv-key',1,2,3,4,10,20,(claim,))
        signer=Ed25519PrivateKey.generate();pub=signer.public_key().public_bytes_raw()
        pin=ExternalPin(sha256(checkpoint_bytes(c)).hexdigest(),sha256(pub).hexdigest(),c.issuer,c.key_id,1,2,3,4,rev,False,tuple(sorted({p.initial.scope.principal_id for p in pins})))
        return review_signed_snapshot(self.reader,lambda:SnapshotConnection(self.path),PLAN,rev,pins,c,pin,pub,signer.sign(checkpoint_bytes(c)),((claim.run_id,signer.sign(terminal_bytes(c,claim))),),15,anchors=(base.BUDGET,),require_terminal_anchors=True)

    def test_full_admission_renewal_terminal_signed_company(self):
        self.chain();m,i,e,p=self.terminal();self.execute(m,i,e);self.commands+=p,
        r=self.company();self.assertTrue(r.structural_match);self.assertEqual((r.event_count,r.pool_revision,r.outstanding_minor),(5,3,0))
        s=self.signed();self.assertTrue(s.signature_match and s.atomic_anchor_match);self.assertEqual(s.history.event_count,5)
        self.assertFalse(s.independent_verified or s.dispatch_allowed or s.replay_allowed)

    def test_anchor_failure_rolls_back_company_and_budget(self):
        self.chain();m,i,e,p=self.terminal()
        self.f.update("CREATE TRIGGER reject_anchor BEFORE INSERT ON terminal_command_anchors BEGIN SELECT RAISE(ABORT,'injected'); END")
        before=self.dump()
        with self.assertRaises(sqlite3.IntegrityError):self.execute(m,i,e)
        self.assertEqual(self.dump(),before);self.assertTrue(self.company().structural_match)

    def test_company_failure_rolls_back_terminal_anchor_and_budget(self):
        self.chain();m,i,e,p=self.terminal()
        self.f.update("CREATE TRIGGER reject_company BEFORE INSERT ON company_event_order BEGIN SELECT RAISE(ABORT,'injected'); END")
        before=self.dump()
        with self.assertRaises(sqlite3.IntegrityError):self.execute(m,i,e)
        self.assertEqual(self.dump(),before);self.assertTrue(self.company().structural_match)

    def test_unknown_terminal_commit_exact_readback(self):
        self.chain();m,i,e,p=self.terminal()
        with self.assertRaises(CommitOutcomeUnknown):self.execute(m,i,e,unknown=True)
        self.history+=e,;self.commands+=p,
        self.assertTrue(self.company().structural_match);self.assertTrue(self.signed().atomic_anchor_match)
        before=self.dump()
        with self.assertRaises(ValueError):self.execute(self.terminal()[0],i,e)
        self.assertEqual(self.dump(),before)

    def test_project_cap_before_admission(self):
        self.pool=replace(self.pool,allocations=(Allocation('project-a',19),))
        before=self.dump()
        with self.assertRaisesRegex(ValueError,'PROJECT_CAP'):self.admission()
        self.assertEqual(self.dump(),before)

    def test_company_tamper_rejects_terminal_before_write(self):
        self.chain();m,i,e,p=self.terminal();self.f.update('UPDATE company_event_order SET predecessors=\'[]\' WHERE sequence=2');before=self.dump()
        self.assertFalse(self.company().structural_match)
        with self.assertRaisesRegex(ValueError,'PREIMAGE'):self.execute(m,i,e)
        self.assertEqual(self.dump(),before)
