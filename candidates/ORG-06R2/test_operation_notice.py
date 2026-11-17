"""One extra original-source check; never reruns the 11 inherited tests."""
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import unittest


def main(root):
    root = Path(root).resolve()
    sys.path.insert(0, str(root/'candidates/ORG-06'))
    import test_org_core_checkout as original
    from durable_ops import TaskPin

    class OperationNoticeTests(original.CheckoutTests):
        def test_operation_notice_tamper(self):
            pin = TaskPin(self.scope, self.f.project, original.RESEARCH_REVISION, 'research', 'research')
            history = self.store.append_proposal(self.head, pin, pin, 'lead', 'worker', 'delegation', self.history)
            self.assertEqual(history.count, 1)
            args = dict(task_id='research', seat_id='worker', history_pin=history)
            self.matched(**args)
            # The revision notice is distinct from this operation notice.
            with closing(sqlite3.connect(self.path)) as db, db:
                self.assertEqual(db.execute('SELECT count(*) FROM op_notice').fetchone()[0], 1)
                db.execute('DROP TRIGGER op_notice_update')
                changed = db.execute("UPDATE op_notice SET digest='bad'")
                self.assertEqual(changed.rowcount, 1)
            self.denied(**args)

    suite = unittest.TestSuite([OperationNoticeTests('test_operation_notice_tamper')])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun == 1 and not result.skipped else 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Run only via run_checkout.py with the verified archive')
    sys.exit(main(sys.argv[1]))
