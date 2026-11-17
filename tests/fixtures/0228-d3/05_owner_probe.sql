-- Trusted admin on disposable fixture only: FORCE RLS denies even the non-login owner.
BEGIN;
SET LOCAL ROLE aicos_d3_owner;
DO $d3$
BEGIN
  IF current_user <> 'aicos_d3_owner' OR EXISTS (SELECT 1 FROM aicos_d3_fixture.run_heads) THEN
    RAISE EXCEPTION 'D3_OWNER_FORCE_RLS_HOLD';
  END IF;
END
$d3$;
ROLLBACK;
