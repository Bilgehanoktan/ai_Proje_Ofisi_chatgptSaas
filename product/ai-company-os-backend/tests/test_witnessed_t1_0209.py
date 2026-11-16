"""Original T1 coordinator/session + disposable SQL stand-in mapping; not PG evidence."""
from contextlib import closing, contextmanager
from dataclasses import replace
import sqlite3
from unittest import TestCase
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import transition_digest
from app.core.transaction.review import LogicalIntent, Operation, required_roles
from app.core.transaction.port import LogicalT1Coordinator, CommitReceipt
from app.core.transaction.postgres_session import postgres_transaction, CommitOutcomeUnknown
from app.core.transaction.witnessed_mapping import WitnessedTransitionMapping, binding_digest
from app.engines.memory_engine.snapshot_store import publish_snapshot
import test_memory_witness_0209 as fixture


class FixtureConnection:
    autocommit = False

    def __init__(self, path, unknown=False):
        self.db = sqlite3.connect(path)
        self.db.execute('BEGIN IMMEDIATE')
        self.unknown = unknown

    @contextmanager
    def cursor(self):
        with closing(self.db.cursor()) as c:
            yield c

    def commit(self):
        self.db.commit()
        if self.unknown:
            raise OSError('fixture lost commit response')

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()


class FixtureMapping:
    """Minimal local SQL stand-in; original coordinator controls transaction and roles."""
    def __init__(self, before, fault=None):
        self.before = before
        self.fault = fault

    def lock_and_validate(self, c, i):
        if c.execute('SELECT version FROM run').fetchone() != (i.expected_version,):
            raise ValueError('FIXTURE_CAS')

    def lock_transition(self, c, i):
        return self.read_transition(c, i)

    def write_transition_role(self, c, role, i, before, target):
        c.execute('INSERT INTO roles VALUES (?,?)', (role, i.request_digest))
        if role == 'HEAD':
            c.execute('UPDATE run SET state=?,version=?', (target.value, before.version+1))
        if self.fault:
            self.fault(role)

    def read_transition(self, c, i):
        state, version = c.execute('SELECT state,version FROM run').fetchone()
        return replace(self.before, state=RunState(state), version=version)

    def verify_write_set(self, c, i, roles):
        if set(c.execute('SELECT role,digest FROM roles')) != {(r, i.request_digest) for r in roles}:
            raise ValueError('FIXTURE_ROLES')
        return CommitReceipt('demo-tx', i.expected_version+1, i.request_digest)


class WitnessedT1Tests(TestCase):
    def setUp(self):
        self.w = fixture.MemoryWitnessTests()
        self.w.setUp()
        self.addCleanup(self.w.doCleanups)
        f = self.w.b.f
        self.before = f.run
        self.target = RunState.VERIFYING
        self.intent = LogicalIntent(f.scope, Operation.STATE_MUTATION, f.run.version,
            transition_digest(f.run, self.target), 'effect-1', self.w.j.envelope.idempotency_key,
            f.lease.grant_id, f.lease.lease_id, None, f.lease.policy_epoch, f.lease.witness_epoch)
        self.binding = binding_digest(self.intent, self.w.j.context, self.w.b.registry, self.w.latest)
        self.db = self.w.path.with_name('t1.db')
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute('CREATE TABLE run(state TEXT,version INTEGER)')
            db.execute('INSERT INTO run VALUES (?,?)', (f.run.state.value, f.run.version))
            db.execute('CREATE TABLE roles(role TEXT PRIMARY KEY,digest TEXT)')
        self.initial = self.dump()

    def dump(self):
        with closing(sqlite3.connect(self.db)) as db:
            return (tuple(db.execute('SELECT * FROM run')), tuple(db.execute('SELECT * FROM roles ORDER BY role')))

    def adapter(self, fault=None, observe=None, **changes):
        w, f = self.w, self.w.b.f
        args = dict(mapping=FixtureMapping(f.run, fault), context=w.j.context,
                    registry=w.b.registry, witness=w.latest, expected_binding=self.binding,
                    memory_path=w.b.store.path, reader=w.reader, public_key=w.pub, raw=w.j.raw,
                    observe=observe or (lambda c: (f.lease, f.clock, w.latest)))
        args.update(changes)
        return WitnessedTransitionMapping(**args)

    def coordinator(self, adapter, unknown=False):
        return LogicalT1Coordinator(lambda: postgres_transaction(lambda: FixtureConnection(self.db, unknown), adapter))

    def execute(self, adapter=None, unknown=False):
        return self.coordinator(adapter or self.adapter(), unknown).commit_transition(self.intent, self.before, self.target)

    def test_original_coordinator_and_session_commit(self):
        receipt = self.execute()
        self.assertEqual(receipt.committed_version, self.before.version+1)
        run, roles = self.dump()
        self.assertEqual(run, (('VERIFYING', self.before.version+1),))
        self.assertEqual({r[0] for r in roles}, required_roles(self.intent))

    def test_wrong_binding_rolls_back(self):
        with self.assertRaisesRegex(ValueError, 'BINDING'):
            self.execute(self.adapter(expected_binding='0'*64))
        self.assertEqual(self.dump(), self.initial)

    def test_generic_commit_disallowed(self):
        with self.assertRaisesRegex(ValueError, 'TRANSITION_ONLY'):
            self.coordinator(self.adapter()).commit(self.intent)
        self.assertEqual(self.dump(), self.initial)

    def test_revocation_during_roles_rolls_back(self):
        b = self.w.b
        def fault(role):
            if role == 'EVENT':
                publish_snapshot(b.store.path, b.store.revoke(), b.pin)
        with self.assertRaisesRegex(ValueError, 'CAS_HOLD'):
            self.execute(self.adapter(fault=fault))
        self.assertEqual(self.dump(), self.initial)

    def test_witness_update_during_roles_rolls_back(self):
        w = self.w
        def fault(role):
            if role == 'AUDIT':
                w.append(w.next(recovery_epoch=2), w.latest.record_sha)
        with self.assertRaisesRegex(ValueError, 'WITNESS'):
            self.execute(self.adapter(fault=fault))
        self.assertEqual(self.dump(), self.initial)

    def test_external_latest_reference_changes(self):
        w, f = self.w, self.w.b.f
        calls = []
        def observe(c):
            calls.append(1)
            pin = w.latest if len(calls)==1 else replace(w.latest, record_sha='f'*64)
            return f.lease, f.clock, pin
        with self.assertRaisesRegex(ValueError, 'LATEST_HOLD'):
            self.execute(self.adapter(observe=observe))
        self.assertEqual(self.dump(), self.initial)

    def test_clock_expiry_at_postcheck(self):
        w, f = self.w, self.w.b.f
        calls = []
        def observe(c):
            calls.append(1)
            clock = f.clock if len(calls)==1 else replace(f.clock, now_tick=95)
            return f.lease, clock, w.latest
        with self.assertRaisesRegex(ValueError, 'CONTEXT_HOLD'):
            self.execute(self.adapter(observe=observe))
        self.assertEqual(self.dump(), self.initial)

    def test_bad_intent_ref(self):
        for changes in (dict(idempotency_key='other'), dict(grant_ref='other'), dict(lease_ref='other'),
                        dict(budget_ref='other'), dict(lease_or_budget_changes=True)):
            with self.assertRaises(ValueError):
                binding_digest(replace(self.intent, **changes), self.w.j.context, self.w.b.registry, self.w.latest)

    def test_unknown_commit_preserves_rows_no_retry(self):
        adapter = self.adapter()
        with self.assertRaises(CommitOutcomeUnknown):
            self.execute(adapter, unknown=True)
        self.assertEqual(self.dump()[0], (('VERIFYING', self.before.version+1),))
        before = self.dump()
        with self.assertRaises(ValueError):
            self.execute(adapter)
        self.assertEqual(self.dump(), before)

    def test_role_error_rolls_back(self):
        def fault(role):
            if role == 'AUDIT':
                raise RuntimeError('fault')
        with self.assertRaises(RuntimeError):
            self.execute(self.adapter(fault=fault))
        self.assertEqual(self.dump(), self.initial)
