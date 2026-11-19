"""0192/0193 PostgreSQL transaction transport; no default connection or authority."""
from contextlib import contextmanager
from typing import NoReturn
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

    This legacy path is D0 diagnostic only; it does not enforce strict expiry.
    Protected callers must use protected_postgres_transaction.

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


def require_strict_postgres_commit() -> NoReturn:
    """Pre-claim capability gate for protected callers, with no side effects.

    Call before claim, journal staging, or any protected write. There is no
    supported strict durable COMMIT guarantee for this transport. This is not
    a freshness check or a grant; no caller evidence or configuration enables it.
    """
    raise PermissionError("T1_STRICT_COMMIT_EXPIRY_UNPROVEN_HOLD")


def protected_postgres_transaction(connect, mapping) -> NoReturn:
    """Strict-expiry boundary: no supported PostgreSQL commit guarantee yet.

    Deliberately deny before connection acquisition, mapping access or writes.
    No caller flag, timeout, trigger, clock sample or receipt can enable it.
    Legacy D0 diagnostics are not a substitute for this entry point.
    """
    require_strict_postgres_commit()
    # Even an accidental future preflight return must not enable a transport.
    raise PermissionError("T1_STRICT_COMMIT_TRANSPORT_UNIMPLEMENTED_HOLD")
