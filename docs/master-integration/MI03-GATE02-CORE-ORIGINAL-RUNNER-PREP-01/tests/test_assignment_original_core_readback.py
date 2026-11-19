"""GATE02: Original ResearchSlice reader + original OperationsStore, disposable SQLite.

Requires FULL EXACT backend owner checkout and the seven existing 0192–0204C
DDL files. This test is not a credential issuer or independent acceptance. Never
interpret an ACCEPTED_D0 *historical observation* as a runtime grant.

Reference: original Core 0224 ResearchFixture, ORG-05R3+G8 OperationsStore.
"""
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from app.core.agent_runtime.lifecycle import RunState
from app.core.event_store.company_coordination import Member, SCOPE
from app.core.transaction.review import LogicalIntent, Operation
from app.core.transaction.intent_identity import derive_request
from app.core.development_review.research_slice import ResearchSliceReview
from test_canonical_research_0224 import ResearchFixture
from test_transition_mapping_0194 import SQLiteCursorShim
from durable_ops import initialize_assignment_ops, OperationsStore, TaskPin, HistoryPin, ZERO
from persistence import Scope as OrgScope
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from operations import ProjectTeam
from assignment_lifecycle import AssignmentPin, ApprovalObservation, AssignmentReview


class OriginalCoreAssignmentTests(unittest.TestCase):
    """No mock Core inspector, no monkeypatch, no injected Core readback result."""

    def setUp(self):
        self.core = ResearchFixture(self)
        self.assertTrue(self.core.read().structural_match, 'ORIGINAL_CORE_0224_READBACK_FAILED')
        target = next(x for x in self.core.initials if x.scope.task_id == 'research')
        self.member = next(x for x in self.core.members if x.task_id == 'research')
        self.assertIs(type(self.member), Member)
        self.intent = LogicalIntent(target.scope, Operation.STATE_MUTATION, 0,
                                    'd'*64, 'effect', 'idem', 'grant', 'lease', None, 1, 2)
        self.request = derive_request(self.intent, self.member, SCOPE, target.scope.principal_id)
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.org_path = Path(self.tmp.name) / 'assignment.d0.sqlite'
        initialize_assignment_ops(self.org_path)
        tenant, company, environment = SCOPE
        self.scope = OrgScope(tenant, company, environment)
        self.store = OperationsStore(self.org_path, self.scope)
        self.staff = Staffing(
            Org(tenant, company,
                (Unit(company, 'company', None), Unit('dept', 'department', company),
                 Unit('team', 'team', 'dept')),
                (Seat('lead', 'dept', 'orchestrator'),
                 Seat('worker', 'team', 'research', 'lead'))),
            (Definition('dl', 'orchestrator'), Definition('dw', 'research')),
            (Instance('demo-lead', 'dl', tenant, company),
             Instance(self.request.agent, 'dw', tenant, company)),
            (Binding('lead', 'demo-lead'), Binding('worker', self.request.agent))
        )
        self.org_head = self.store.record(self.staff, None)
        team = ProjectTeam(tenant, company, self.staff.revision(),
                           self.request.project, 'lead', ('lead', 'worker'))
        self.store.create_team(self.org_head, team)
        op_pin = TaskPin(self.scope, self.request.project, self.request.plan_revision,
                         self.request.task, 'research')
        self.history = self.store.append_proposal(self.org_head, op_pin, op_pin,
                                                  'lead', 'worker', 'delegation',
                                                  HistoryPin(0, ZERO))
        with closing(sqlite3.connect(self.org_path)) as db:
            proposal = db.execute('SELECT digest FROM op_entry').fetchone()[0]
            team_digest = db.execute('SELECT team_digest FROM op_team').fetchone()[0]
        self.pin = AssignmentPin(
            self.request, self.org_head, 1, self.staff.revision(), team_digest,
            self.history.count, self.history.head, proposal, 'worker', 'research',
            0, 1, '1'*64, 1, '2'*64, 1, '4'*64
        )
        self.accept = ApprovalObservation('ACCEPT', 'demo-decision-accepted',
                                          'demo-owner-observation', 'demo-custody', 10, 30)
        self.revoke = ApprovalObservation('REVOKE', 'demo-decision-revoked',
                                          'demo-owner-observation', 'demo-custody', 15, 40)
        self.args = dict(plan=self.core.plan,
                         expected_revision=self.request.plan_revision,
                         project_id=self.request.project,
                         pins=self.core.pins(), members=self.core.members,
                         pool=self.core.pool, events=self.core.history,
                         anchor=self.core.anchor)

    def actual_core_cursor(self, db):
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        return SQLiteCursorShim(db)

    def create_assignment(self, *, member=None, args=None, intent=None):
        with closing(sqlite3.connect(self.core.path)) as core_db:
            with self.actual_core_cursor(core_db) as cursor:
                return self.store.record_assignment_review(
                    self.pin, self.accept, 12, ZERO,
                    core_cursor=cursor, core_args=args or self.args,
                    intent=intent or self.intent, member=member or self.member,
                    member_scope=SCOPE, principal=self.request.principal)

    def check_hold(self, value):
        self.assertIs(type(value), AssignmentReview)
        self.assertEqual(value.decision, 'HOLD')
        self.assertFalse(value.authoritative)
        self.assertFalse(value.dispatch_allowed)
        self.assertFalse(value.commit_allowed)
        self.assertFalse(value.retry_allowed)
        return value

    def test_actual_core_positive_store_accept_still_hold(self):
        first = self.create_assignment()
        self.assertEqual((first.state, first.revision), ('ACCEPTED_D0', 1))
        self.check_hold(first)
        with closing(sqlite3.connect(self.core.path)) as core_db:
            with self.actual_core_cursor(core_db) as cursor:
                second = self.store.assignment_review(
                    self.pin, first.assignment_sha, 12,
                    core_cursor=cursor, core_args=self.args,
                    intent=self.intent, member=self.member,
                    member_scope=SCOPE, principal=self.request.principal)
        self.assertEqual(second.state, 'ACCEPTED_D0')
        self.check_hold(second)

    def test_actual_core_wrong_project_rejected_without_write(self):
        wrong = replace(self.member, project_id='demo-unrelated-project')
        with self.assertRaises((ValueError, TypeError)):
            self.create_assignment(member=wrong)
        with closing(sqlite3.connect(self.org_path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(), (0,))

    def test_actual_core_wrong_version_rejected_without_write(self):
        bad = replace(self.intent, expected_version=1)
        with self.assertRaises((ValueError, TypeError)):
            self.create_assignment(intent=bad)
        with closing(sqlite3.connect(self.org_path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(), (0,))

    def test_actual_core_wrong_history_pin_rejected(self):
        wrong = dict(self.args, members=tuple(m for m in self.args['members']
                                               if m.task_id != self.request.task))
        with self.assertRaises((ValueError, TypeError)):
            self.create_assignment(args=wrong)
        with closing(sqlite3.connect(self.org_path)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(), (0,))


if __name__ == '__main__':
    unittest.main(verbosity=2)
