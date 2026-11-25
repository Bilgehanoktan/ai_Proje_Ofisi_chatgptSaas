"""Candidate SQL primitives, called only inside a T1-owned transaction.
No schema installation, dispatch, or independent commit.
"""
from app.core.transaction.review import valid_intent

def append_event(cursor, intent, event_id, event_type):
    if not valid_intent(intent):
        raise ValueError("EVENT_INTENT_INVALID")
    s = intent.scope
    cursor.execute(
        "INSERT INTO t1_candidate.events (tenant_id, company_id, environment_id, run_id, version, event_id, event_type, request_digest) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (s.tenant_id,s.company_id,s.environment_id,s.run_id,intent.expected_version+1,event_id,event_type,intent.request_digest))

def insert_outbox(cursor, intent, event_id):
    s = intent.scope
    cursor.execute(
        "INSERT INTO t1_candidate.outbox (tenant_id, company_id, environment_id, run_id, event_id, request_digest) VALUES (%s,%s,%s,%s,%s,%s)",
        (s.tenant_id,s.company_id,s.environment_id,s.run_id,event_id,intent.request_digest))

def reserve_fence(cursor, intent):
    s = intent.scope
    cursor.execute(
        "INSERT INTO t1_candidate.fences (tenant_id, company_id, environment_id, effect_key, idempotency_key, request_digest) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING request_digest",
        (s.tenant_id,s.company_id,s.environment_id,intent.effect_key,intent.idempotency_key,intent.request_digest))
    if cursor.fetchone() is None:
        # Never repeat an effect on conflict; reconciliation is separate.
        raise ValueError("FENCE_CONFLICT_RECONCILE")
