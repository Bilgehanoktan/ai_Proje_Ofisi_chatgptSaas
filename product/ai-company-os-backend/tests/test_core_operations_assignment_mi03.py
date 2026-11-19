"""MI03 GATE-02: original persisted Core Research + original ORG OperationsStore.

D0 isolated SQLite readback only. No role issuer, actual IAM credential, protected
COMMIT, PostgreSQL, production data, provider, grant, dispatch or authorization.
Run ONLY on exact reviewed 553-product-file MI03-GATE03 candidate checkout.
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
from unittest import TestCase

from test_canonical_research_0224 import ResearchFixture, RESEARCH_REVISION, SQLiteCursorShim, SCOPE
from app.core.transaction.intent_identity import derive_request
from app.core.development_review.research_slice import inspect_research_slice
from app.core.event_store.company_coordination import Member
from assignment_lifecycle import AssignmentPin, ApprovalObservation, ZERO
from durable_ops import (OperationsStore, HistoryPin, TaskPin, initialize_assignment_ops)
from operations import ProjectTeam
from org_model import Org, Seat, Unit
from persistence import Scope
from staffing import Staffing, Definition, Instance, Binding


class ActualCoreOperationsAssignmentTests(TestCase):
    """Use original persisted SQL reader and original ORG Store; no mock readers."""

    def setUp(self):
        self.f = ResearchFixture(self)  # original Core fixture owns temp cleanup
        self.org_path = self.f.path.with_name('org_assignment_d0.sqlite')
        initialize_assignment_ops(self.org_path)  # CREATE ONLY fresh disposable file
        self.store = OperationsStore(self.org_path, Scope(*SCOPE))
        tenant, company, _ = SCOPE
        self.staffing = Staffing(
            Org(tenant, company, (
                Unit(company, 'company', None),
                Unit('ops', 'department', company),
            ), (
                Seat('manager', 'ops', 'orchestrator'),
                Seat('lead', 'ops', 'orchestrator', 'manager'),
            )),
            (Definition('d-manager', 'orchestrator'), Definition('d-lead', 'orchestrator')),
            (Instance('demo-agent-manager', 'd-manager', tenant, company),
             Instance('demo-agent-plan', 'd-lead', tenant, company)),
            (Binding('manager', 'demo-agent-manager'), Binding('lead', 'demo-agent-plan')),
        )
        self.head = self.store.record(self.staffing, None)
        self.team = ProjectTeam(tenant, company, self.staffing.revision(),
                                self.f.project, 'manager', ('manager', 'lead'))
        self.team_sha = self.store.create_team(self.head, self.team)
        task = TaskPin(Scope(*SCOPE), self.f.project, RESEARCH_REVISION,
                       'plan', 'orchestrator')
        self.history = self.store.append_proposal(self.head, task, task,
                                                   'manager', 'lead', 'delegation',
                                                   HistoryPin(0, ZERO))
        self.member = next(m for m in self.f.members if m.task_id == 'plan')
        self.intent = self.f.admit
        self.request = derive_request(self.intent, self.member, SCOPE,
                                      self.member.principal_id)
        with closing(self.store._connect()) as db:
            db.execute('BEGIN')
            row = db.execute(
                'SELECT seq,staffing_digest FROM org_revision WHERE t=? AND c=? AND e=? AND rev=?',
                (*SCOPE, self.head)).fetchone()
        self.assertEqual(row[0], 1)
        self.pin = AssignmentPin(
            self.request, self.head, row[0], row[1], self.team_sha,
            self.history.count, self.history.head, self.history.head,
            'lead', 'orchestrator', 0,
            1, '7' * 64, 1, '8' * 64, 1, '9' * 64,
        )
        self.accept = ApprovalObservation('ACCEPT', 'demo-decision-accept',
                                          'demo-issuer', 'demo-custody', 5, 15)
        self.revoke = ApprovalObservation('REVOKE', 'demo-decision-revoke',
                                          'demo-issuer', 'demo-custody', 11, 30)
        self.args = dict(
            plan=self.f.plan, expected_revision=RESEARCH_REVISION,
            project_id=self.f.project, pins=self.f.pins(),
            members=self.f.members, pool=self.f.pool,
            events=self.f.history, anchor=self.f.anchor,
        )

    def count(self):
        with closing(sqlite3.connect(self.org_path)) as db:
            return db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone()[0]

    def call(self, action, *, pin=None, approval=None, now=10,
             expected_sha=ZERO, principal=None, member=None, core_args=None,
             revoke=False):
        """Pass an original, consistent Core SQLite cursor to the exact owner API."""
        with closing(sqlite3.connect(self.f.path)) as db:
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            with SQLiteCursorShim(db) as c:
                kw = dict(core_cursor=c,
                          core_args=self.args if core_args is None else core_args,
                          intent=self.intent,
                          member=self.member if member is None else member,
                          member_scope=SCOPE,
                          principal=self.member.principal_id if principal is None else principal)
                p = self.pin if pin is None else pin
                if action == 'write':
                    return self.store.record_assignment_review(
                        p, self.accept if approval is None else approval,
                        now, expected_sha, revoke=revoke, **kw)
                if action == 'read':
                    return self.store.assignment_review(p, expected_sha, now, **kw)
                raise AssertionError('INVALID_TEST_ACTION')

    def check_hold(self, review, expected_state=None, *, matched=True):
        self.assertEqual(review.decision, 'HOLD')
        self.assertEqual(review.structural_match, matched)
        if expected_state is not None:
            self.assertEqual(review.state, expected_state)
        self.assertFalse(review.authoritative or review.dispatch_allowed or
                         review.commit_allowed or review.retry_allowed)

    def test_original_core_reader_positive_before_write(self):
        with closing(sqlite3.connect(self.f.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with SQLiteCursorShim(db) as c:
                result = inspect_research_slice(c, **self.args)
        self.assertTrue(result.structural_match, result.reason)
        self.assertEqual(result.decision, 'HOLD')
        self.assertEqual(result.freshness, 'HISTORICAL_SAMPLE')
        self.assertEqual(next(t.version for t in result.tasks if t.task_id == 'plan'), 0)
        self.assertFalse(result.dispatch_allowed or result.release_ready)
        self.assertEqual(self.count(), 0)

    def test_real_core_and_operations_positive_commit_readback(self):
        before_core = self.f.path.read_bytes()
        first = self.call('write')
        self.check_hold(first, 'ACCEPTED_D0')
        self.assertEqual((first.revision, self.count()), (1, 1))
        second = self.call('read', expected_sha=first.assignment_sha)
        self.check_hold(second, 'ACCEPTED_D0')
        self.assertEqual(second.assignment_sha, first.assignment_sha)
        self.assertEqual(self.f.path.read_bytes(), before_core)
        with closing(sqlite3.connect(self.org_path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM op_notice WHERE state != ?',
                                        ('HOLD',)).fetchone(), (0,))

    def test_wrong_principal_no_write(self):
        with self.assertRaises(ValueError):
            self.call('write', principal='demo-unrelated-principal')
        self.assertEqual(self.count(), 0)

    def test_stale_core_version_no_write(self):
        with self.assertRaises(ValueError):
            self.call('write', pin=replace(self.pin, core_version=1))
        self.assertEqual(self.count(), 0)

    def test_role_mismatch_no_write(self):
        with self.assertRaises(ValueError):
            self.call('write', pin=replace(self.pin, task_role='research'))
        self.assertEqual(self.count(), 0)

    def test_member_principal_drift_no_write(self):
        with self.assertRaises(ValueError):
            self.call('write', member=replace(self.member, principal_id='demo-forged'))
        self.assertEqual(self.count(), 0)

    def test_cross_scope_no_write(self):
        forged = replace(self.pin, request=replace(self.request,
                         scope=('synthetic-other', SCOPE[1], SCOPE[2])))
        with self.assertRaises(ValueError):
            self.call('write', pin=forged)
        self.assertEqual(self.count(), 0)

    def test_revocation_holds_and_no_reaccept(self):
        first = self.call('write')
        revoked = self.call('write', approval=self.revoke, now=12,
                            expected_sha=first.assignment_sha, revoke=True)
        self.check_hold(revoked, 'REVOKED_D0')
        after = self.call('read', expected_sha=revoked.assignment_sha, now=13)
        self.check_hold(after, 'REVOKED_D0')
        with self.assertRaises(ValueError):
            self.call('write', expected_sha=revoked.assignment_sha)
        self.assertEqual(self.count(), 2)

    def test_persisted_core_drift_revokes_readback_match(self):
        first = self.call('write')
        with closing(sqlite3.connect(self.f.path)) as db, db:
            db.execute('UPDATE run_heads SET version=1 WHERE task_id=?', ('plan',))
        actual = self.call('read', expected_sha=first.assignment_sha)
        self.check_hold(actual, 'READ_UNAVAILABLE_HOLD', matched=False)
        self.assertEqual(self.count(), 1)

    def test_absent_core_cursor_fails_closed(self):
        # Store must NOT silently bypass real Core; no fixture boolean substitutes.
        with self.assertRaises(Exception):
            self.store.record_assignment_review(
                self.pin, self.accept, 10, ZERO, core_cursor=None,
                core_args=self.args, intent=self.intent, member=self.member,
                member_scope=SCOPE, principal=self.member.principal_id)
        self.assertEqual(self.count(), 0)


if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
