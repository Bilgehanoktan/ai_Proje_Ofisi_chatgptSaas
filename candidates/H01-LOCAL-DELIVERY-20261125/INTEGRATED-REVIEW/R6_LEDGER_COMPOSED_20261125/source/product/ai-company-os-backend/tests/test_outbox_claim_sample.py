from contextlib import closing
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from app.core.development_review.atomic_sample import AtomicSample
from app.core.development_review.outbox_claim_sample import OutboxReviewSample


class OutboxReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'case.review.atomic.d0.sqlite'
        self.store=OutboxReviewSample(self.path)
        self.store.create()
        self.store.renew('demo-owner',None,1,10)
        self.store.observe('demo-command','demo-owner',1,2,0)

    def claim(self):
        return self.store.claim_review('demo-command','demo-reviewer',3,5)

    def unknown(self):
        self.claim()
        self.store.mark_unknown('demo-command','demo-reviewer',1,4)

    def test_initial_hold(self):
        x=self.store.inspect_review('demo-command')
        self.assertEqual(x['phase'],'LOCAL_HOLD')
        self.assertFalse(x['dispatch_allowed'])
        self.assertFalse(x['retry_allowed'])

    def test_concurrent_claim(self):
        def attempt(who):
            try: return self.store.claim_review('demo-command',who,3,5)
            except ValueError: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(attempt,['demo-a','demo-b'])),[1,None])

    def test_expiry_and_fence(self):
        self.assertEqual(self.claim(),1)
        self.assertEqual(self.store.claim_review('demo-command','demo-other',8,5),2)
        with self.assertRaises(ValueError): self.store.mark_unknown('demo-command','demo-reviewer',1,9)

    def test_clock_regression(self):
        with self.assertRaises(ValueError): self.store.claim_review('demo-command','demo-reviewer',1,5)

    def test_unknown_persists(self):
        self.unknown()
        reopened=OutboxReviewSample(self.path)
        self.assertEqual(reopened.inspect_review('demo-command')['phase'],'UNKNOWN_HOLD')
        with self.assertRaisesRegex(ValueError,'NO_BLIND_RETRY'): reopened.claim_review('demo-command','demo-other',100,5)

    def test_readback_not_resolution(self):
        self.unknown()
        self.assertEqual(self.store.record_readback('demo-command',1,'a'*64),'READBACK_HOLD')
        x=OutboxReviewSample(self.path).inspect_review('demo-command')
        self.assertEqual(x['readback_sha'],'a'*64)
        for k in ('reconciled','dispatch_allowed','retry_allowed','provider_called','release_ready'): self.assertFalse(x[k])
        with self.assertRaises(ValueError): self.store.claim_review('demo-command','demo-other',100,5)

    def test_readback_idempotency(self):
        self.unknown()
        self.store.record_readback('demo-command',1,'a'*64)
        self.assertEqual(self.store.record_readback('demo-command',1,'a'*64),'DUPLICATE_IGNORED')
        with self.assertRaises(ValueError): self.store.record_readback('demo-command',1,'b'*64)

    def test_readback_requires_unknown_and_generation(self):
        self.claim()
        with self.assertRaises(ValueError): self.store.record_readback('demo-command',1,'a'*64)
        self.store.mark_unknown('demo-command','demo-reviewer',1,4)
        with self.assertRaises(ValueError): self.store.record_readback('demo-command',2,'a'*64)

    def test_bound_to_audit(self):
        with closing(sqlite3.connect(self.path)) as db, db: db.execute('DELETE FROM audit')
        with self.assertRaises(ValueError): self.claim()

    def test_wrong_profile(self):
        with self.assertRaises(ValueError): AtomicSample(self.path).snapshot()
        with self.assertRaises(ValueError): OutboxReviewSample(self.path,tenant='other')

    def test_readback_rollback(self):
        self.unknown()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TRIGGER fail_readback BEFORE UPDATE ON local_review BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.store.record_readback('demo-command',1,'a'*64)
        self.assertEqual(self.store.inspect_review('demo-command')['phase'],'UNKNOWN_HOLD')

    def test_outbox_stays_deny(self):
        self.unknown()
        self.store.record_readback('demo-command',1,'a'*64)
        with closing(sqlite3.connect(self.path)) as db, db: self.assertEqual(db.execute('SELECT status FROM outbox').fetchall(),[('DENY',)])
