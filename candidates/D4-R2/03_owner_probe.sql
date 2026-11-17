-- Trusted disposable admin only; verify FORCE RLS even under owner identity.
DO $guard$ BEGIN
 IF current_database() <> 'aicos_d4_0229' OR current_setting('cluster_name') <> 'aicos_d4_0229_disposable'
 OR current_setting('port') <> '55434' OR current_setting('server_version_num') <> '170012'
 OR inet_server_addr() IS DISTINCT FROM '127.0.0.1'::inet
 OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper)
 THEN RAISE EXCEPTION 'D4_DISPOSABLE_ADMIN_ONLY'; END IF;
END $guard$;
BEGIN;
SET LOCAL ROLE aicos_d4_owner;
DO $probe$ DECLARE t text; n bigint; BEGIN
 FOREACH t IN ARRAY ARRAY['events','outbox','fences','run_heads','run_leases','run_mutations','run_audit','sample_budgets','run_admissions','sample_reservations','run_lease_renewals','sample_settlements','terminal_command_anchors','company_run_membership','company_stream_heads','company_event_order'] LOOP
 EXECUTE format('SELECT count(*) FROM t1_candidate.%I',t) INTO n;
 IF n <> 0 THEN RAISE EXCEPTION 'D4_OWNER_VISIBLE: %',t; END IF;
 END LOOP;
 BEGIN
 INSERT INTO t1_candidate.company_stream_heads VALUES ('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',99);
 RAISE EXCEPTION 'D4_OWNER_INSERT_ALLOWED';
 EXCEPTION WHEN insufficient_privilege THEN NULL;
 END;
END $probe$;
ROLLBACK;
