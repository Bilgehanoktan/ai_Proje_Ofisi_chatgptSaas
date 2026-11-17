"""Read-only dedicated PostgreSQL session inspection. No T1 or credential issuer."""
from identity_binding import SessionFacts, Review, review_binding, review_boundary

TABLES=('events','outbox','fences','run_heads','run_leases','run_mutations','run_audit',
        'sample_budgets','run_admissions','sample_reservations','run_lease_renewals',
        'sample_settlements','terminal_command_anchors','company_run_membership',
        'company_stream_heads','company_event_order')
FACTS_SQL="""SELECT session_user, current_user, current_database(), current_setting('cluster_name'),
 pg_backend_pid(), current_setting('row_security')='on',
 (rolsuper OR rolbypassrls OR rolcreaterole OR rolcreatedb OR rolreplication OR rolinherit),
 (SELECT count(*) FROM pg_auth_members WHERE member=r.oid),
 (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='t1_candidate' AND c.relowner=r.oid),
 (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='t1_candidate' AND c.relkind='r' AND c.relrowsecurity AND c.relforcerowsecurity AND c.relname=ANY(%s)),
 has_schema_privilege(current_user,'t1_candidate','CREATE'),
 (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
  WHERE n.nspname='t1_candidate' AND c.relkind='r' AND (has_table_privilege(current_user,c.oid,'TRUNCATE') OR has_table_privilege(current_user,c.oid,'TRIGGER') OR has_table_privilege(current_user,c.oid,'REFERENCES')))
 FROM pg_roles r WHERE r.rolname=session_user"""


def inspect_connection(request, initial, resolve_latest, clock, connect):
    """Trusted composition inputs only; no untrusted HTTP callbacks, no retained session.

    The caller must supply a protected resolver and dedicated connection factory.
    Equality is not proof of provenance or atomic revocation fencing. Even a match
    returns HOLD. A future T1 integration must recheck under the existing authority
    fence on the same transaction through COMMIT; this probe does not do that.
    """
    db=None
    result=Review('D4_PROBE_HOLD')
    try:
        pre=review_binding(request,initial,resolve_latest(),clock())
        if not pre.structural_match:
            return pre
        db=connect()
        if db.autocommit is not False or int(db.info.transaction_status)!=0:
            return Review('D4_DIRTY_OR_AUTOCOMMIT_HOLD')
        pid=db.info.backend_pid
        with db.cursor() as c:
            c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            c.execute(FACTS_SQL,(list(TABLES),))
            row=c.fetchone()
            if row is None or len(row)!=12 or c.fetchone() is not None:
                return Review('D4_FACTS_HOLD')
            facts=SessionFacts(*row)
            c.execute("SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='t1_candidate' AND c.relkind='r' ORDER BY relname")
            if tuple(x[0] for x in c.fetchall())!=tuple(sorted(TABLES)):
                return Review('D4_TABLE_INVENTORY_HOLD')
            result=review_boundary(request,initial,resolve_latest(),clock(),facts,pid)
        db.rollback()
        if int(db.info.transaction_status)!=0:
            result=Review('D4_ROLLBACK_STATE_HOLD')
        return result
    except Exception:
        return Review('D4_PROBE_HOLD')
    finally:
        if db is not None:
            # Dedicated session never returned to a pool. Cleanup failure must not
            # be hidden by an earlier structural match.
            try: db.close()
            except Exception: return Review('D4_CLOSE_HOLD')
