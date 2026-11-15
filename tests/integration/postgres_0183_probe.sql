-- 0189: append to the pinned 0183 candidate transaction ONLY in a fresh disposable cluster.
-- No canonical schema, effective grant, external effect, or real tenant data.
SET LOCAL statement_timeout = '5s';
SET LOCAL lock_timeout = '2s';
INSERT INTO aicos_d0_candidate.head VALUES ('synthetic-tenant','synthetic-company','probe',0,'PENDING');
INSERT INTO aicos_d0_candidate.lease VALUES ('synthetic-tenant','synthetic-company','probe','demo-holder',1,1,11);
DO $$
BEGIN
  BEGIN
    UPDATE aicos_d0_candidate.head SET version=1,state='OBSERVED' WHERE aggregate_id='probe' AND version=0;
    INSERT INTO aicos_d0_candidate.event VALUES ('synthetic-tenant','synthetic-company','probe','probe-command',1,repeat('a',64));
    INSERT INTO aicos_d0_candidate.audit VALUES ('synthetic-tenant','synthetic-company','probe-command','SAMPLE_ONLY');
    -- Deliberate late failure: DENY is the only valid outbox state.
    INSERT INTO aicos_d0_candidate.outbox VALUES ('synthetic-tenant','synthetic-company','probe-command','ILLEGAL');
    RAISE EXCEPTION 'expected check violation';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  IF (SELECT version FROM aicos_d0_candidate.head WHERE aggregate_id='probe') <> 0
     OR EXISTS (SELECT FROM aicos_d0_candidate.event)
     OR EXISTS (SELECT FROM aicos_d0_candidate.audit)
     OR EXISTS (SELECT FROM aicos_d0_candidate.outbox) THEN
    RAISE EXCEPTION 'rollback incomplete';
  END IF;
  RAISE NOTICE 'PASS 01 late outbox failure rolls back head/event/audit/outbox subtransaction';
END $$;
DO $$
DECLARE n integer;
BEGIN
  UPDATE aicos_d0_candidate.head SET version=1,state='OBSERVED' WHERE aggregate_id='probe' AND version=0;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 1 THEN RAISE EXCEPTION 'CAS initial update failed'; END IF;
  UPDATE aicos_d0_candidate.head SET version=2 WHERE aggregate_id='probe' AND version=0;
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 0 THEN RAISE EXCEPTION 'stale CAS accepted'; END IF;
  RAISE NOTICE 'PASS 02 stale CAS rejected (single session)';
  INSERT INTO aicos_d0_candidate.event VALUES ('synthetic-tenant','synthetic-company','probe','probe-command',1,repeat('a',64));
  INSERT INTO aicos_d0_candidate.audit VALUES ('synthetic-tenant','synthetic-company','probe-command','SAMPLE_ONLY');
  INSERT INTO aicos_d0_candidate.outbox VALUES ('synthetic-tenant','synthetic-company','probe-command','DENY');
  BEGIN
    INSERT INTO aicos_d0_candidate.event VALUES ('synthetic-tenant','synthetic-company','probe','probe-command',2,repeat('b',64));
    RAISE EXCEPTION 'duplicate accepted';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
  RAISE NOTICE 'PASS 03 scoped duplicate command constraint';
  BEGIN
    INSERT INTO aicos_d0_candidate.audit VALUES ('synthetic-tenant','synthetic-company','missing-event','SAMPLE_ONLY');
    RAISE EXCEPTION 'orphan accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL;
  END;
  RAISE NOTICE 'PASS 04 orphan audit FK rejected';
  BEGIN
    UPDATE aicos_d0_candidate.lease SET expires_tick=heartbeat_tick WHERE aggregate_id='probe';
    RAISE EXCEPTION 'invalid lease accepted';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  RAISE NOTICE 'PASS 05 invalid lease expiry rejected';
END $$;
-- Bootstrap is used only to seed fixed fixtures. Probe is explicitly non-owner/non-superuser.
CREATE ROLE aicos_0189_probe NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT USAGE ON SCHEMA aicos_d0_candidate TO aicos_0189_probe;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA aicos_d0_candidate TO aicos_0189_probe;
SET LOCAL ROLE aicos_0189_probe;
DO $$
DECLARE n integer;
BEGIN
  IF current_user <> 'aicos_0189_probe' OR (SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user) THEN
    RAISE EXCEPTION 'probe role not isolated';
  END IF;
  IF EXISTS (SELECT FROM aicos_d0_candidate.head) OR EXISTS (SELECT FROM aicos_d0_candidate.lease)
     OR EXISTS (SELECT FROM aicos_d0_candidate.event) OR EXISTS (SELECT FROM aicos_d0_candidate.audit)
     OR EXISTS (SELECT FROM aicos_d0_candidate.outbox) THEN
    RAISE EXCEPTION 'RLS read leak';
  END IF;
  RAISE NOTICE 'PASS 06 non-owner default-deny read on all five candidate tables';
  BEGIN
    INSERT INTO aicos_d0_candidate.head VALUES ('synthetic-tenant','synthetic-company','blocked',0,'PENDING');
    RAISE EXCEPTION 'RLS insert unexpectedly accepted';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  UPDATE aicos_d0_candidate.head SET version=9 WHERE aggregate_id='probe';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 0 THEN RAISE EXCEPTION 'RLS update leak'; END IF;
  DELETE FROM aicos_d0_candidate.event WHERE command_id='probe-command';
  GET DIAGNOSTICS n = ROW_COUNT;
  IF n <> 0 THEN RAISE EXCEPTION 'RLS delete leak'; END IF;
  RAISE NOTICE 'PASS 07 non-owner default-deny insert/update/delete';
END $$;
RESET ROLE;
DO $$
BEGIN
  IF (SELECT version FROM aicos_d0_candidate.head WHERE aggregate_id='probe') <> 1
     OR (SELECT count(*) FROM aicos_d0_candidate.event) <> 1
     OR (SELECT count(*) FROM aicos_d0_candidate.audit) <> 1
     OR (SELECT count(*) FROM aicos_d0_candidate.outbox) <> 1 THEN
    RAISE EXCEPTION 'fixture changed';
  END IF;
  RAISE NOTICE 'PASS 08 bootstrap readback preserved after denied writes';
END $$;
ROLLBACK;
