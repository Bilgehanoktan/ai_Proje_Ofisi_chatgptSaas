"""Exact original 0209/0210/0211 production wrapper, new D0 fixture.
Uses pinned 0194 real SQLite mapping, not original 0213 test fixture or PG.
One deliberate restore residual is reproduced, not a security pass.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from hashlib import sha256
import sqlite3
from threading import Event, Barrier
from unittest import TestCase
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import test_transition_mapping_0194 as base
from app.core.agent_runtime.lifecycle import RunState
from app.core.agent_runtime.transition_command import transition_digest
from app.core.agent_runtime.joint_context import JointContext
from app.core.agent_runtime.memory_witness import (MemoryWitness, D0MemoryWitnessStore,
    MemoryWitnessReader, witness_bytes, witness_sha)
from app.core.transaction.intent_authority import D0IntentAuthority, RootPin, execute_authority_fenced_transition
from app.core.transaction.fenced_transition import D0IntentJournal, intent_pin
from app.core.transaction.witnessed_mapping import binding_digest
from app.core.transaction.postgres_session import CommitOutcomeUnknown
from app.core.transaction.postgres_transition_mapping import verify_transition_rows
from app.engines.memory_engine.retrieval import Node, TombstoneView
from app.engines.memory_engine.runtime_binding import MemoryAclEntry, MemoryAclView
from app.engines.memory_engine.snapshot_store import Snapshot, create_store, publish_snapshot
from app.engines.knowledge_engine.provenance import SourceVersion, ClaimSpan
from app.engines.model_gateway.provider_contract import ProviderKind, ProviderRequest
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.runtime_binding import InvocationEnvelope


class FullChainTests(TestCase):
    def setUp(self):
        self.f = base.MappingTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.before = replace(base.BEFORE, state=RunState.RUNNING)
        self.target = RunState.VERIFYING
        self.f.update("UPDATE run_heads SET state='RUNNING'")
        self.i = replace(base.INTENT, request_digest=transition_digest(self.before, self.target))
        s = self.before.scope; l = base.LEASE; self.clock = base.CLOCK
        self.raw = b'synthetic evidence only'; d = sha256(self.raw).hexdigest()
        node = Node(s, 'source', 'v1', d, ())
        view = TombstoneView(s, 1, 1, (), True)
        acl = MemoryAclView(s, self.before.version, self.before.attempt, l.policy_epoch,
            l.witness_epoch, view.epoch, view.sequence, 1, True,
            (MemoryAclEntry(node.node_id, node.revision, node.digest, 'ALLOW_READ'),))
        source = SourceVersion(s, node.node_id, node.revision, d)
        self.snapshot = Snapshot(self.before, (node,), node.node_id, view, acl, source,
            ClaimSpan(source, 0, len(self.raw), d), self.raw)
        self.memory = self.f.path.with_name('memory.d0.sqlite')
        create_store(self.memory); self.mp = publish_snapshot(self.memory, self.snapshot, None)
        a = AdapterPin(s, 'demo-model', 'v1', 'a'*64, ('demo-tool',), ())
        b = AdapterPin(s, 'demo-fallback', 'v1', 'b'*64, ('demo-tool',), ())
        self.registry = (a,b)
        request = ProviderRequest(s, ProviderKind.SAMPLE, d, ('demo-tool',), (), 64)
        self.context = JointContext(self.mp, InvocationEnvelope(self.before, l, request, a, b,
            'reserve-1', self.i.idempotency_key, 100))
        self.signer = Ed25519PrivateKey.generate(); self.pub = self.signer.public_key().public_bytes_raw()
        self.record = MemoryWitness(s, 1, 1, l.policy_epoch, l.witness_epoch, self.mp, 9, 20)
        self.store = D0MemoryWitnessStore.create(self.f.path.with_name('memory.witness.sqlite'))
        self.witness = self.store.append(self.record, self.signer.sign(witness_bytes(self.record)), self.pub, None)
        self.reader = MemoryWitnessReader(self.store.path)
        self.binding = binding_digest(self.i, self.context, self.registry, self.witness)
        self.journal = D0IntentJournal.create(self.f.path.with_name('run.intent.sqlite'))
        self.pin = intent_pin(self.i, self.binding)
        self.root = RootPin(self.witness.record_sha, self.witness.key_sha, self.witness.recovery_epoch)
        self.authority = D0IntentAuthority.create(self.f.path.with_name('run.authority.sqlite'), self.root)

    def invoke(self, **changes):
        args = dict(authority=self.authority, intent=self.i, context=self.context, registry=self.registry,
            witness=self.witness, expected_binding=self.binding, memory_path=self.memory,
            reader=self.reader, public_key=self.pub, raw=self.raw, journal=self.journal,
            connect=lambda:base.SQLiteConnectionShim(self.f.path), clock=lambda:self.clock)
        args.update(changes)
        return execute_authority_fenced_transition(**args)

    def claims(self):
        with closing(sqlite3.connect(self.authority.path)) as db:
            return db.execute('SELECT count(*) FROM claims').fetchone()[0]

    def review(self, expected):
        r = self.journal.inspect(self.i,self.pin)
        self.assertEqual(r.status,expected)
        for flag in ('dispatch_allowed','release_allowed','retry_allowed','provider_call_allowed','spend_allowed','independent_verified'):
            self.assertIs(getattr(r,flag),False)
        return r

    def committed(self):
        self.assertEqual(self.f.rows(),(('VERIFYING',5,1),(1,1,1,1,1)))
        with closing(sqlite3.connect(self.f.path)) as db:
            db.execute('PRAGMA query_only=ON'); db.execute('BEGIN')
            with base.SQLiteCursorShim(db) as c:
                verify_transition_rows(c,self.i,self.before,self.target,base.LEASE)

    def empty(self):
        self.assertEqual(self.f.rows(),(('RUNNING',4,1),(0,0,0,0,0)))

    def test_full_original_wrapper_commit(self):
        self.assertTrue(self.invoke().historical_match); self.committed()
        self.assertEqual(self.claims(),1); self.review('HISTORICAL')

    def test_restore_journal_t1_but_not_authority_blocks_replay(self):
        t=self.f.path.read_bytes(); j=self.journal.path.read_bytes()
        self.invoke(); self.committed()
        self.f.path.write_bytes(t); self.journal.path.write_bytes(j); self.empty()
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'): self.invoke()
        self.empty(); self.assertEqual(self.claims(),1); self.review('HOLD')

    def test_lost_commit_reply_no_retry(self):
        with self.assertRaises(CommitOutcomeUnknown):
            self.invoke(connect=lambda:base.SQLiteConnectionShim(self.f.path,True))
        self.committed(); self.review('UNKNOWN')
        with self.assertRaisesRegex(ValueError,'ALREADY_CLAIMED'): self.invoke()

    def test_revocation_before_claim_no_writes(self):
        self.authority.publish(self.root,replace(self.root,record_sha='f'*64,recovery_epoch=2))
        with self.assertRaisesRegex(ValueError,'ROOT_HOLD'): self.invoke()
        self.empty(); self.assertEqual(self.claims(),0)

    def test_root_publisher_waits_through_commit(self):
        started,done=Event(),Event(); jobs=[]; outer=self
        def publish():
            started.set(); self.authority.publish(self.root,replace(self.root,record_sha='f'*64,recovery_epoch=2)); done.set()
        with ThreadPoolExecutor(max_workers=1) as pool:
            class C(base.SQLiteConnectionShim):
                def commit(self):
                    jobs.append(pool.submit(publish)); outer.assertTrue(started.wait(1)); outer.assertFalse(done.wait(.1))
                    super().commit(); outer.assertFalse(done.is_set())
            self.invoke(connect=lambda:C(self.f.path)); jobs[0].result(timeout=5)
        self.committed(); self.assertTrue(done.is_set())

    def test_revoked_memory_before_t1_quarantines(self):
        tomb=replace(self.snapshot.tombstone,sequence=2,keys=('source',))
        acl=replace(self.snapshot.acl,tombstone_sequence=2,acl_revision=2)
        publish_snapshot(self.memory,replace(self.snapshot,tombstone=tomb,acl=acl),self.mp)
        with self.assertRaisesRegex(ValueError,'CAS_HOLD'): self.invoke()
        self.empty(); self.review('UNKNOWN'); self.assertEqual(self.claims(),1)

    def test_wrong_signature_key_no_commit(self):
        with self.assertRaisesRegex(ValueError,'WITNESS'):
            self.invoke(public_key=Ed25519PrivateKey.generate().public_key().public_bytes_raw())
        self.empty(); self.review('UNKNOWN')

    def test_expired_lease_quarantine(self):
        with self.assertRaisesRegex(ValueError,'LEASE_EXPIRED'):
            self.invoke(clock=lambda:replace(self.clock,now_tick=20))
        self.empty(); self.review('UNKNOWN')

    def test_concurrent_claim_one_original_commit(self):
        barrier=Barrier(2,timeout=3)
        def attempt():
            barrier.wait()
            try: return self.invoke().status
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs=[pool.submit(attempt) for _ in range(2)]
            self.assertCountEqual([j.result(timeout=5) for j in jobs],['HISTORICAL','D0_AUTHORITY_ALREADY_CLAIMED_HOLD'])
        self.committed(); self.assertEqual(self.claims(),1)

    def test_full_restore_residual_reproduced_not_security_pass(self):
        paths=(self.f.path,self.journal.path,self.authority.path)
        old=[p.read_bytes() for p in paths]
        self.invoke(); self.committed()
        for p,b in zip(paths,old): p.write_bytes(b)
        self.empty()
        self.assertTrue(self.invoke().historical_match)  # D-04 known residual
        self.committed()
