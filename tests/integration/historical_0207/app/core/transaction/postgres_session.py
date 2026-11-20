"""0192/0193 PostgreSQL transaction transport; no default connection or authority."""
from contextlib import contextmanager
from app.core.transaction.port import CommitReceipt


class CommitOutcomeUnknown(RuntimeError):
    """Commit was attempted; reconcile persisted evidence, never blindly retry."""


class PostgresSession:
    def __init__(self, cursor, mapping):
        self.cursor = cursor
        self.mapping = mapping

    def lock_and_validate(self, intent):
        self.mapping.lock_and_validate(self.cursor, intent)

    def write_role(self, role, intent):
        self.mapping.write_role(self.cursor, role, intent)

    def verify_write_set(self, intent, roles) -> CommitReceipt:
        return self.mapping.verify_write_set(self.cursor, intent, roles)

    def lock_transition(self, intent):
        return self.mapping.lock_transition(self.cursor, intent)

    def write_transition_role(self, role, intent, before, target):
        self.mapping.write_transition_role(self.cursor, role, intent, before, target)

    def read_transition(self, intent):
        return self.mapping.read_transition(self.cursor, intent)


@contextmanager
def postgres_transaction(connect, mapping):
    """Dedicated psycopg-compatible connection; explicit trusted mapping required.

    Before COMMIT, errors rollback. COMMIT errors have unknown outcome: never
    imply rollback reversed them. Cleanup errors must not hide the original error.
    """
    connection = connect()
    commit_attempted = False
    active_error = False
    try:
        if connection.autocommit:
            raise ValueError("T1_AUTOCOMMIT_FORBIDDEN")
        with connection.cursor() as cursor:
            yield PostgresSession(cursor, mapping)
        commit_attempted = True
        try:
            connection.commit()
        except Exception as exc:
            raise CommitOutcomeUnknown("T1_COMMIT_OUTCOME_UNKNOWN") from exc
    except BaseException:
        active_error = True
        if not commit_attempted:
            try:
                connection.rollback()
            except Exception:
                pass
        raise
    finally:
        try:
            connection.close()
        except Exception as exc:
            if not active_error:
                # Commit completed but cleanup failed: preserve uncertainty semantics
                # for callers; independent readback is required before any retry.
                raise CommitOutcomeUnknown("T1_CLOSE_AFTER_COMMIT_RECONCILE") from exc
