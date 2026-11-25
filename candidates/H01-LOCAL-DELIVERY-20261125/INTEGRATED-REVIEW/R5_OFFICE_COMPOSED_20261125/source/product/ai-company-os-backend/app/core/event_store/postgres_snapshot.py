"""Disposable D0 PostgreSQL plan readback. No write or runtime authority.
The factory must return a fresh, exclusively owned psycopg-compatible connection.
Connection identity and independent pin custody remain external trust boundaries.
"""
from app.core.event_store.plan_history_review import PlanHistoryReview, inspect_plan_history

_CONFIG = 'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY'
_CHECK = ("SELECT current_database(), current_setting('transaction_isolation'), "
          "current_setting('transaction_read_only'), rolsuper, rolbypassrls "
          "FROM pg_catalog.pg_roles WHERE rolname=current_user")


def _check_context(cursor):
    cursor.execute(_CHECK)
    row = cursor.fetchone()
    if (not isinstance(row, (tuple, list)) or len(row) != 5
            or not isinstance(row[0], str) or not row[0].startswith('aicos_d0_')
            or tuple(row[1:]) != ('repeatable read', 'on', False, False)
            or type(row[3]) is not bool or type(row[4]) is not bool
            or cursor.fetchone() is not None):
        raise ValueError('D0_PG_SNAPSHOT_CONTEXT_HOLD')
    return tuple(row)


def read_plan_snapshot(connect, plan, expected_revision, pins, *, exclusive_budget_anchors=None, require_terminal_anchors=False):
    """Return historical sample evidence only after clean rollback and close.

    Never commit, retry, switch to a weaker isolation level, reuse an open
    transaction, or return a partial projection after cleanup errors.
    A dedicated connection factory and trusted disposable local deployment
    are required; the database-name/role guard is not an authorization system.
    """
    result = PlanHistoryReview('D0_PG_SNAPSHOT_HOLD')
    db = None
    try:
        if type(require_terminal_anchors) is not bool: raise ValueError("D0_ANCHOR_MODE_HOLD")
        db = connect()
        # psycopg TransactionStatus.IDLE == 0; unknown status fails closed.
        status = db.info.transaction_status
        if db.autocommit is not False or isinstance(status, bool) or not isinstance(status, int) or status != 0:
            raise ValueError('D0_PG_SNAPSHOT_FRESH_CONNECTION_HOLD')
        with db.cursor() as cursor:
            cursor.execute(_CONFIG)
            cursor.execute("SET LOCAL statement_timeout='5s'")
            cursor.execute("SET LOCAL lock_timeout='2s'")
            before = _check_context(cursor)
            reviewed = inspect_plan_history(cursor, plan, expected_revision, pins,
                                            exclusive_budget_anchors=exclusive_budget_anchors)
            if require_terminal_anchors and reviewed.structural_match:
                from app.core.event_store.terminal_anchor import verify_plan_anchors
                verify_plan_anchors(cursor, expected_revision, pins)
            if _check_context(cursor) != before:
                raise ValueError('D0_PG_SNAPSHOT_CONTEXT_CHANGED')
        result = reviewed
    except Exception:
        result = PlanHistoryReview('D0_PG_SNAPSHOT_HOLD')
    finally:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                result = PlanHistoryReview('D0_PG_SNAPSHOT_CLEANUP_HOLD')
            finally:
                try:
                    db.close()
                except Exception:
                    result = PlanHistoryReview('D0_PG_SNAPSHOT_CLEANUP_HOLD')
    return result
