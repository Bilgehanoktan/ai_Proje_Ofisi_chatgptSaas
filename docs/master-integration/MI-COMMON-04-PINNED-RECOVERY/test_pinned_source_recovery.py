"""Local synthetic tests of the immutable source-recovery helper, not product tests."""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pinned_source_recovery as r


def row(path, data):
    return {'path': path, 'blob': r.git_blob(data), 'bytes': len(data),
            'sha256': hashlib.sha256(data).hexdigest()}


class RecoveryControls(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='mi04-test-')
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cache = self.root/'cache'
        self.cache.mkdir()
        self.stage = self.root/'staged'

    def save(self, data):
        blob = r.git_blob(data)
        (self.cache/blob).write_bytes(data)
        return blob

    def test_git_blob_vector(self):
        self.assertEqual(r.git_blob(b''), 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
        self.assertEqual(r.git_blob(b'abc'), hashlib.sha1(b'blob 3\0abc').hexdigest())

    def test_path_traversal_and_invalid_paths_denied(self):
        for bad in ('../a', '/a', 'a//b', 'a/./b', 'a/../b', 'a\\b', 'C:/a',
                    'a/', 'a\x00b', '', './a'):
            with self.subTest(bad=bad), self.assertRaisesRegex(r.SourceHold,'UNSAFE_PIN_PATH'):
                r.safe_rel(bad)
        self.assertEqual(str(r.safe_rel('product/app/core.py')), 'product/app/core.py')

    def test_duplicate_pin_path_denied(self):
        with self.assertRaisesRegex(r.SourceHold,'DUPLICATE_PIN_PATH'):
            r.normalize([row('a.py',b'A'),row('a.py',b'B')])

    def test_source_hash_and_size_denied(self):
        sha = r.git_blob(b'A')
        for data, size, expected in [(b'B',1,None),(b'A',2,None),
                                     (b'A',1,'0'*64)]:
            with self.subTest(data=data,size=size),self.assertRaises(r.SourceHold):
                r.verify_blob(data,sha,size,expected)
        self.assertEqual(r.verify_blob(b'A',sha,1,hashlib.sha256(b'A').hexdigest()),b'A')

    def test_offline_cache_hit_and_corruption(self):
        sha = self.save(b'A')
        c = r.ExactCache(self.cache, offline=True)
        self.assertEqual(c.read(sha),b'A')
        (self.cache/sha).write_bytes(b'B')
        with self.assertRaisesRegex(r.SourceHold,'BLOB_PIN_MISMATCH'):
            c.read(sha)

    def test_offline_missing_stops_without_network(self):
        c = r.ExactCache(self.cache, offline=True)
        with self.assertRaisesRegex(r.SourceHold,'CACHE_MISS_OFFLINE'):
            c.read(r.git_blob(b'missing'))
        self.assertFalse(self.stage.exists())

    def test_symlink_cache_denied(self):
        sha = self.save(b'A')
        (self.cache/sha).unlink()
        (self.cache/sha).symlink_to(self.root)
        with self.assertRaisesRegex(r.SourceHold,'CACHE_SYMLINK_HOLD'):
            r.ExactCache(self.cache,offline=True).read(sha)

    def test_preexisting_stage_is_never_overwritten(self):
        self.stage.mkdir()
        with self.assertRaisesRegex(r.SourceHold,'DESTINATION_EXISTS_HOLD'):
            r.ensure_fresh(self.stage,self.cache)

    def test_stage_under_cache_denied(self):
        with self.assertRaisesRegex(r.SourceHold,'CACHE_STAGE_OVERLAP_HOLD'):
            r.ensure_fresh(self.cache/'stage',self.cache)

    def test_wrong_remote_response_denied(self):
        sha = r.git_blob(b'actual')
        class Fake:
            def __init__(self, body): self.body=body; self.status=200
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return self.body
        class Opener:
            def open(self,req,timeout):
                self.req=req
                return Fake(json.dumps({'sha':'0'*40,'encoding':'base64',
                    'size':6,'content':base64.b64encode(b'actual').decode()}).encode())
        opener=Opener()
        with self.assertRaisesRegex(r.SourceHold,'GITHUB_BLOB_RESPONSE_HOLD'):
            r.ExactCache(self.cache,token='secret',opener=opener).read(sha)
        self.assertEqual(opener.req.full_url,f'https://api.github.com/repos/{r.REPO}/git/blobs/{sha}')
        self.assertFalse((self.cache/sha).exists())

    def test_original_model_pin_map_allows_optional_sha256(self):
        # The real combined pin map has 28 entries with Git blob+size only.
        raw = json.dumps({f'product/src_{i}.py': {
            'blob': r.git_blob(b'A'), 'bytes': 1,
            **({'sha256': hashlib.sha256(b'A').hexdigest()} if i >= 28 else {})
        } for i in range(114)}, sort_keys=True).encode()
        with patch.dict(r.PIN_BLOBS, {'model':r.git_blob(raw)}):
            rows=r.model_rows(raw)
        self.assertEqual(len(rows),114)
        self.assertEqual(sum(x['sha256'] is None for x in rows),28)

    def test_actual_known_legacy_blob_from_archive(self):
        # Real immutable Git SHA from the previously uploaded project archive.
        known='9d457472970b7f581687ba142d1bf99ba91c7388'
        p=Path('/mnt/data/mi_common_03_work/mm-recovered-blobs')/known
        if not p.exists():self.skipTest('legacy source not mounted')
        data=p.read_bytes()
        self.assertEqual(len(data),59)
        self.assertEqual(r.verify_blob(data,known),data)

    def test_two_separate_canonical_and_history_trees(self):
        # Different bytes for one shared path must *never* be silently merged.
        mm=[row('product/ai-company-os-backend/app/core/runtime.py',b'new'),
            row('candidates/test_model.py',b'test')]
        core=[row('product/ai-company-os-backend/app/core/runtime.py',b'old'),
              row('product/ai-company-os-backend/tests/test_hist.py',b'test')]
        mb=b'model-lock';cb=b'core-lock'
        self.save(mb);self.save(cb)
        for data in (b'new',b'old',b'test'): self.save(data)
        pins={'model':r.git_blob(mb),'core':r.git_blob(cb)}
        with patch.object(r,'PIN_BLOBS',pins),patch.object(r,'model_rows',return_value=mm),\
             patch.object(r,'core_rows',return_value=core):
            # Scope check for actual 26/2 overlap is deliberate; bypass that
            # with one lane to test immutable stage successful recovery.
            report=r.recover(r.ExactCache(self.cache,offline=True),self.stage,('model',),
                pins_override={'model':mb},aux_override={'model':{}})
        self.assertEqual(report['status'],'RECOVERED_NOT_TESTED')
        self.assertEqual((self.stage/'model'/mm[0]['path']).read_bytes(),b'new')
        self.assertFalse((self.stage/'core').exists())
        self.assertEqual(report['test_runs']['model_344'],'NOT_RUN')

    def test_different_historical_overlay_requires_reviewed_count(self):
        m=row('product/x',b'A');c=row('product/x',b'B')
        self.save(b'A');self.save(b'B')
        mb=b'model-lock';cb=b'core-lock';self.save(mb);self.save(cb)
        with patch.object(r,'PIN_BLOBS',{'model':r.git_blob(mb),'core':r.git_blob(cb)}),\
             patch.object(r,'model_rows',return_value=[m]),\
             patch.object(r,'core_rows',return_value=[c]):
            with self.assertRaisesRegex(r.SourceHold,'HISTORICAL_OVERLAY_SCOPE_HOLD'):
                r.recover(r.ExactCache(self.cache,offline=True),self.stage,
                    ('model','core'),pins_override={'model':mb,'core':cb})
        self.assertFalse(self.stage.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
