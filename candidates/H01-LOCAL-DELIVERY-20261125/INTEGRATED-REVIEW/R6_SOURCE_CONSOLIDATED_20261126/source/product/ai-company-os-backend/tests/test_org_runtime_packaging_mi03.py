"""MI03-GATE03: exact owner ORG package can load from backend root without candidate sys.path.
Local synthetic SQLite fixture only; never an execution/permission gate.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from contextlib import closing
import sqlite3
import org_model
import staffing
import operations
import office_bridge
import integration_guard
import persistence
import durable_ops
import assignment_lifecycle
import org_core_bridge

class OrgPackagingTests(TestCase):
    def test_direct_imports_reuse_single_owner_classes(self):
        self.assertIs(durable_ops.Store, persistence.Store)
        self.assertIs(durable_ops.OperationsStore.__mro__[1], persistence.Store)
        self.assertIs(staffing.Org, org_model.Org)
        self.assertTrue(callable(org_core_bridge.review_research_binding))

    def test_exact_colocated_schema_resources(self):
        root = Path(durable_ops.__file__).resolve().parent
        self.assertEqual(Path(persistence.SCHEMA), root / 'schema.sql')
        self.assertEqual(Path(durable_ops.DDL), root / 'operations.sql')
        self.assertEqual(Path(assignment_lifecycle.DDL), root / 'assignment_review.sql')
        for name in ('schema.sql', 'operations.sql', 'assignment_review.sql'):
            self.assertTrue((root / name).is_file())

    def test_fresh_disposable_owner_store_creates_assignment_table(self):
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/'org-lab.sqlite'
            durable_ops.initialize_assignment_ops(path)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='op_assignment_review'").fetchone(), ('op_assignment_review',))
                self.assertEqual(db.execute('SELECT COUNT(*) FROM op_assignment_review').fetchone(),(0,))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='op_assignment_review_no_update'").fetchone(),(1,))

    def test_assignment_review_remains_non_authoritative(self):
        r=assignment_lifecycle.AssignmentReview('HOLD')
        self.assertEqual(r.decision,'HOLD')
        for key in ('authoritative','dispatch_allowed','commit_allowed','retry_allowed'):
            self.assertFalse(getattr(r,key))
