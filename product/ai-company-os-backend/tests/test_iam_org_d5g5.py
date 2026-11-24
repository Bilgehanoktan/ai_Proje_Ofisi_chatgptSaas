"""Actual disposable R3 SQLite + original G4 IAM; no live grant or PG."""
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import closing
import sqlite3
import unittest
import test_iam_identity_d5g4 as g4
from durable_ops import initialize_ops, OperationsStore, TaskPin, HistoryPin, ZERO
from persistence import Scope
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from operations import ProjectTeam
from app.core.transaction.intent_identity import derive_request
from app.core.transaction.identity_fence_review import session_reference_digest
from app.core.transaction.org_membership_review import (
    JOIN_FIELDS, read_current_org_reference, org_reference_digest,
    inspect_org_session_reference,
)


class OrgSessionTests(unittest.TestCase):
    def setUp(self):
        self.f = g4.SessionIdentityTests()
        self.addCleanup(self.f.doCleanups)
        self.f.setUp()
        f = self.f
        f.member = replace(f.member, project_id='demo-project')
        req = derive_request(f.intent, f.member, f.initial.scope, f.initial.principal)
        f.initial = replace(f.initial, member=f.member, binding=replace(f.initial.binding, request=req))
        f.ref = f.capture()
        f.sha = session_reference_digest(f.ref)
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.db = Path(temp.name)/'org.sqlite'
        initialize_ops(self.db)
        self.scope = Scope(*f.initial.scope)
        t,c,_ = self.scope.key()
        self.store = OperationsStore(self.db, self.scope)
        self.staff = Staffing(Org(t,c,(Unit(c,'company',None),Unit('dept','department',c),Unit('team','team','dept')),
            (Seat('lead','dept','orchestrator'),Seat('worker','team','research','lead'))),
            (Definition('dl','orchestrator'),Definition('dw','research')),
            (Instance('demo-lead','dl',t,c),Instance(req.agent,'dw',t,c)),
            (Binding('lead','demo-lead'),Binding('worker',req.agent)))
        self.head = self.store.record(self.staff,None)
        self.team = ProjectTeam(t,c,self.staff.revision(),req.project,'lead',('lead','worker'))
        self.store.create_team(self.head,self.team)
        pin = TaskPin(self.scope,req.project,req.plan_revision,req.task,'research')
        self.history = self.store.append_proposal(self.head,pin,pin,'lead','worker',
                          'delegation',HistoryPin(0,ZERO))
        self.org = self.capture()
        self.org_sha = org_reference_digest(self.org)

    def capture(self, **kw):
        f = self.f
        args = dict(org_head=self.head,seat='worker',role='research',history_pin=self.history) | kw
        return read_current_org_reference(self.store,f.initial,f.ref,**args)

    def review(self, **kw):
        f = self.f
        args = dict(store=self.store,org_reference=self.org,org_sha=self.org_sha,
                    org_head=self.head,seat='worker',role='research',history_pin=self.history,
                    root=f.root,owner_pin=f.pin,domain='demo-clock') | kw
        latest = args.pop('latest',lambda:f.initial)
        secret = args.pop('secret',f.secrets[0])
        return inspect_org_session_reference(f.resolver,secret,f.intent,f.initial,f.ref,f.sha,latest,**args)

    def denied(self, value):
        self.assertFalse(value.structural_match)
        self.assertEqual(value.decision,'HOLD')
        self.assertFalse(value.commit_allowed or value.dispatch_allowed or value.retry_allowed)

    def test_exact_current_readback(self):
        self.assertEqual(len(JOIN_FIELDS),17)
        self.assertEqual(len(self.org.join),17)
        self.assertEqual(self.org.join[3:6],(self.head,1,self.staff.revision()))
        self.assertEqual(self.org.join[-1],self.f.ref.request.intent_sha)
        self.assertEqual(self.org.unit,'team')
        self.assertEqual(self.org.department,'dept')
        result=self.review()
        self.assertTrue(result.structural_match)
        self.assertEqual(result.decision,'HOLD')
        self.assertFalse(result.commit_allowed or result.dispatch_allowed or result.retry_allowed)

    def test_wrong_seat(self):
        self.denied(self.review(seat='lead'))

    def test_wrong_role(self):
        self.denied(self.review(role='qa'))

    def test_stale_head(self):
        self.store.record(replace(self.staff,previous=self.staff.revision()),self.head)
        self.denied(self.review())

    def test_missing_proposal(self):
        self.denied(self.review(history_pin=HistoryPin(0,ZERO)))

    def test_wrong_scope(self):
        other=OperationsStore(self.db,replace(self.scope,environment='A0_REVIEW_ONLY'))
        self.denied(self.review(store=other))

    def test_wrong_org_digest(self):
        self.denied(self.review(org_sha='f'*64))
        # Python equality considers True == 1; exact digest must not.
        forged=replace(self.org,join=self.org.join[:4]+(True,)+self.org.join[5:])
        self.denied(self.review(org_reference=forged,org_sha=org_reference_digest(forged)))

    def test_role_revision_drift(self):
        f=self.f
        self.denied(self.review(latest=lambda:replace(f.initial,binding=replace(f.initial.binding,role_revision=2))))

    def test_exact_session(self):
        self.denied(self.review(secret=self.f.secrets[1]))

    def test_revoked_session(self):
        self.assertTrue(self.f.resolver.revoke_local('demo-session-0',expected_revision=1))
        self.denied(self.review())

    def test_team_tamper(self):
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('DROP TRIGGER op_member_delete')
            db.execute("DELETE FROM op_member WHERE seat='worker'")
        self.denied(self.review())

    def test_no_claim_or_org_writes(self):
        self.assertTrue(self.review().structural_match)
        with closing(self.f.resolver._authority._db()) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM claims').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM iam_claim_pins').fetchone()[0],0)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM op_entry').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT count(*) FROM org_revision').fetchone()[0],1)


if __name__ == '__main__':
    unittest.main()
