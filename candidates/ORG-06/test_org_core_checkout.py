"""Full checkout test candidate: real 0224 Core fixture + original R3 SQLite store.
Run ONLY in a separate checkout with reviewed dependencies. No PG or live agents.
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT/'product'/'ai-company-os-backend'
# Fail before importing if a selected source differs from its retained Git blob.
# This is a selected-source check; it does not replace the exact checkout pin.
for relative, expected in json.loads(Path(__file__).with_name('SOURCE_PINS.json').read_text(encoding='utf-8'))['git_blobs'].items():
    raw = (ROOT/relative).read_bytes()
    actual = hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
    if actual != expected:
        raise RuntimeError('ORG06_SOURCE_PIN_HOLD')
for path in (BACKEND, BACKEND/'tests', ROOT/'candidates'/'ORG-05R3'):
    sys.path.insert(0, str(path))

from test_canonical_research_0224 import ResearchFixture, RESEARCH_REVISION, SQLiteCursorShim, SCOPE
from durable_ops import initialize_ops, OperationsStore, HistoryPin, ZERO
from persistence import Scope
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from operations import ProjectTeam
from org_core_bridge import review_research_binding


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.f = ResearchFixture(self)
        self.path = self.f.path.with_name('organization.sqlite')
        initialize_ops(self.path)
        self.scope = Scope(*SCOPE)
        self.store = OperationsStore(self.path, self.scope)
        t,c,_ = SCOPE
        self.staffing = Staffing(Org(t,c,(Unit(c,'company',None),Unit('ops','department',c)),
            (Seat('lead','ops','orchestrator'),Seat('worker','ops','research','lead'))),
            (Definition('d-lead','orchestrator'),Definition('d-worker','research')),
            (Instance('demo-agent-plan','d-lead',t,c),Instance('demo-agent-research','d-worker',t,c)),
            (Binding('lead','demo-agent-plan'),Binding('worker','demo-agent-research')))
        self.head = self.store.record(self.staffing,None)
        self.team = ProjectTeam(t,c,self.staffing.revision(),self.f.project,'lead',('lead','worker'))
        self.store.create_team(self.head,self.team)
        self.history = HistoryPin(0,ZERO)

    def review(self, **kw):
        args=dict(plan=self.f.plan,expected_revision=RESEARCH_REVISION,project_id=self.f.project,
            pins=self.f.pins(),members=self.f.members,pool=self.f.pool,events=self.f.history,anchor=self.f.anchor,
            store=self.store,org_head=self.head,history_pin=self.history,task_id='plan',seat_id='lead')
        args.update(kw)
        with closing(sqlite3.connect(self.f.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as cursor:
                return review_research_binding(cursor,**args)

    def matched(self, **kw):
        r=self.review(**kw); self.assertTrue(r.structural_match,r.reason)
        self.assertEqual(r.decision,'HOLD'); self.assertFalse(r.authoritative)
        self.assertFalse(r.dispatch_allowed); self.assertIsNone(r.runtime_binding)
        return r

    def denied(self, **kw):
        r=self.review(**kw); self.assertFalse(r.structural_match,r.reason)
        self.assertIsNone(r.task_id); self.assertIsNone(r.project_id); self.assertFalse(r.dispatch_allowed)

    def test_queued_readback(self): self.assertEqual(self.matched().role,'orchestrator')
    def test_admitted_readback(self):
        self.f.admit_root(); self.matched()
    def test_wrong_seat(self): self.denied(seat_id='worker')
    def test_research_seat(self): self.assertEqual(self.matched(task_id='research',seat_id='worker').role,'research')
    def test_stale_head(self):
        self.store.record(replace(self.staffing,previous=self.staffing.revision()),self.head)
        self.denied()
    def test_wrong_history(self): self.denied(history_pin=HistoryPin(1,'a'*64))
    def test_wrong_member(self):
        members=tuple(replace(m,principal_id='demo-forged') if m.task_id=='plan' else m for m in self.f.members)
        self.denied(members=members)
    def test_wrong_environment(self):
        self.denied(store=OperationsStore(self.path,replace(self.scope,environment='A0_REVIEW_ONLY')))
    def test_gate_not_run(self): self.denied(task_id='iv')
    def test_org_notice_tamper(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('DROP TRIGGER org_notice_update'); db.execute("UPDATE org_notice SET digest='bad'")
        self.denied()
    def test_no_db_changes(self):
        def dump(path):
            with closing(sqlite3.connect(path)) as db: return tuple(db.iterdump())
        before=(dump(self.path),dump(self.f.path)); self.matched()
        self.assertEqual(before,(dump(self.path),dump(self.f.path)))

if __name__=='__main__': unittest.main(verbosity=2)
