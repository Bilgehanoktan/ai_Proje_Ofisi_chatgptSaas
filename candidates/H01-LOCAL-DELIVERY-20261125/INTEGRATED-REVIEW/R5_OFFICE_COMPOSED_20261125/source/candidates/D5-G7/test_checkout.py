"""Exact owner fixture composition; disposable SQLite only; NOT PostgreSQL."""
from contextlib import closing
from dataclasses import replace
from hashlib import sha1
import json
from pathlib import Path
import secrets
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
PINS = json.loads(Path(__file__).with_name('SOURCE_PINS.json').read_text(encoding='utf-8'))
for rel, expected in PINS.items():
    path = ROOT / rel
    if path.resolve() != path or not path.is_file():
        raise RuntimeError('G6B_PATH_HOLD')
    raw = path.read_bytes()
    if sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != expected:
        raise RuntimeError('G6B_SOURCE_PIN_HOLD')
print(f'G6B_EXACT_SELECTED_PINS: {len(PINS)}/{len(PINS)}', flush=True)
for path in (ROOT/'product/ai-company-os-backend', ROOT/'product/ai-company-os-backend/tests',
             ROOT/'candidates/ORG-05R3', ROOT/'candidates/ORG-06'):
    sys.path.insert(0, str(path))

from test_org_core_checkout import CheckoutTests as OriginalFixture
from test_transition_mapping_0194 import SQLiteCursorShim
from test_admission_mapping_0195 import intent_for
from durable_ops import TaskPin
from app.core.iam_session import D0SessionResolver, SessionRecord, credential_digest
from app.core.transaction.intent_authority import RootPin
from app.core.transaction.identity_binding import Binding
from app.core.transaction.intent_identity import derive_request
from app.core.transaction.identity_fence_review import (
    IdentityReadback, capture_session_reference, session_reference_digest)
from app.core.transaction.org_membership_review import read_current_org_reference, org_reference_digest
from app.core.transaction.core_org_session_review import inspect_core_org_session_reference


class ActualReadbackTests(unittest.TestCase):
    def setUp(self):
        original = OriginalFixture('test_queued_readback')
        self.addCleanup(original.doCleanups)
        original.setUp(); self.original=original; self.f=original.f
        run=next(r for r in self.f.initials if r.scope.task_id=='research')
        member=next(m for m in self.f.members if m.task_id=='research')
        lease=replace(self.f.lease,scope=run.scope,lease_id='lease-research',grant_id='grant-research')
        self.intent=intent_for(replace(self.f.initial,before=run,lease=lease,admission_id='admission-research'))
        self.root=RootPin('a'*64,'b'*64,1); self.now=100; self.secret=secrets.token_urlsafe(32)
        scope=original.scope.key()
        record=SessionRecord('demo-session-research',credential_digest(self.secret),member.principal_id,
                             'AGENT',scope,member.agent_instance_id,100,200)
        self.resolver=D0SessionResolver.bootstrap_durable(self.f.path.with_name('g6b.authority.sqlite'),
                        self.root,(record,),domain='demo-clock',clock=lambda:self.now)
        self.owner_pin=self.resolver.durable_pin
        req=derive_request(self.intent,member,scope,member.principal_id)
        binding=Binding(req,member.principal_id,1,1,1,1,'1'*64,'2'*64,'3'*64,'4'*64,
                        'demo_role','db','cluster',500,True)
        self.initial=IdentityReadback(member,scope,member.principal_id,binding,self.root,300)
        self.session=capture_session_reference(self.resolver,self.secret,self.intent,self.initial,
                       root=self.root,owner_pin=self.owner_pin,domain='demo-clock')
        pin=TaskPin(original.scope,req.project,req.plan_revision,req.task,'research')
        self.history=original.store.append_proposal(original.head,pin,pin,'lead','worker','delegation',original.history)
        self.org=read_current_org_reference(original.store,self.initial,self.session,org_head=original.head,
                    seat='worker',role='research',history_pin=self.history)

    def review(self, **kw):
        o=self.original; f=self.f
        args=dict(resolver=self.resolver,credential=self.secret,intent=self.intent,initial=self.initial,
            session=self.session,session_sha=session_reference_digest(self.session),read_latest=lambda:self.initial,
            plan=f.plan,pins=f.pins(),members=f.members,pool=f.pool,events=f.history,anchor=f.anchor,
            store=o.store,org_reference=self.org,org_sha=org_reference_digest(self.org),org_head=o.head,
            seat='worker',history_pin=self.history,root=self.root,owner_pin=self.owner_pin,domain='demo-clock')
        with closing(sqlite3.connect(f.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as cursor:
                return inspect_core_org_session_reference(cursor,**(args | kw))

    def held(self, r, matched=False):
        self.assertEqual(r.structural_match,matched,r.reason); self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)

    def snapshots(self):
        out=[]
        for path in (self.f.path,self.original.path,self.resolver._authority.path):
            with closing(sqlite3.connect(path)) as db: out.append(tuple(db.iterdump()))
        return tuple(out)

    def test_exact_existing_readers_no_write(self):
        before=self.snapshots(); self.held(self.review(),True); self.assertEqual(self.snapshots(),before)
    def test_persisted_member_tamper(self):
        with closing(sqlite3.connect(self.f.path)) as db,db:
            db.execute("UPDATE company_run_membership SET principal_id='demo-forged' WHERE task_id='research'")
        self.held(self.review())
    def test_forged_role_reference(self):
        org=replace(self.org,role='qa'); self.held(self.review(org_reference=org,org_sha=org_reference_digest(org)))
    def test_wrong_expected_version(self):
        self.held(self.review(intent=replace(self.intent,expected_version=1)))
    def test_current_org_head_drift(self):
        o=self.original; o.store.record(replace(o.staffing,previous=o.staffing.revision()),o.head); self.held(self.review())
    def test_revoked_iam(self):
        self.assertTrue(self.resolver.revoke_local('demo-session-research',expected_revision=1)); self.held(self.review())
    def test_wrong_latest_member(self):
        self.held(self.review(read_latest=lambda:replace(self.initial,member=replace(self.initial.member,principal_id='demo-other'))))


if __name__=='__main__': unittest.main(verbosity=2)
