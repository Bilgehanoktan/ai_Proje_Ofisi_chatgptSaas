import unittest
from app.core.event_store.sqlite_preview import inspect_sqlite_replay


def row(seq=1, id='e1', **kw):
    return {'seq': seq, 'event_id': id, 'tenant_id': 'synthetic-tenant', 'environment_id': 'A0_SAMPLE_ONLY', **kw}


class TestSqlitePreview(unittest.TestCase):
    def test_readback(self):
        r = inspect_sqlite_replay([row(), row(2, 'e2')])
        self.assertEqual((r['reason'], r['rows']), ('SQLITE_MEMORY_READBACK_ONLY', 2))
        self.assertFalse(r['persistent'] or r['canonical_commit'] or r['dispatch_allowed'])
    def test_duplicate(self):
        self.assertEqual(inspect_sqlite_replay([row(), row(2)])['reason'], 'SQLITE_SAMPLE_ROLLBACK')
    def test_gap(self):
        self.assertIsNone(inspect_sqlite_replay([row(2)])['rows'])
    def test_wrong_scope(self):
        r = row(); r['tenant_id'] = 'other'
        self.assertIsNone(inspect_sqlite_replay([r])['rows'])
    def test_bad_seq(self):
        self.assertIsNone(inspect_sqlite_replay([row(True)])['rows'])
    def test_empty_oversize(self):
        for events in ([], [row()]*101, [row(payload='x'*9000)]):
            self.assertIsNone(inspect_sqlite_replay(events)['rows'])
    def test_non_json(self):
        for payload in (float('nan'), object()):
            self.assertIsNone(inspect_sqlite_replay([row(payload=payload)])['rows'])
    def test_no_persistence(self):
        self.assertEqual(inspect_sqlite_replay([row()]), inspect_sqlite_replay([row()]))
