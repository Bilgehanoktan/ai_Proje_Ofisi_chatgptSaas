"""0192 PostgreSQL transaction transport; no default connection or authority."""
from contextlib import contextmanager
from app.core.transaction.port import CommitReceipt

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

@contextmanager
def postgres_transaction(connect, mapping):
    """Requires a dedicated psycopg-compatible connection and trusted mapping.
    A commit error propagates; caller must reconcile an uncertain outcome.
    """
    connection = connect()
    try:
        if connection.autocommit:
            raise ValueError("T1_AUTOCOMMIT_FORBIDDEN")
        with connection.cursor() as cursor:
            yield PostgresSession(cursor, mapping)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()
