-- 0192 candidate only; do not apply to production. R03 mapping HOLD.
CREATE SCHEMA t1_candidate;
CREATE TABLE t1_candidate.events (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version > 0),
 event_id text NOT NULL, event_type text NOT NULL, request_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id,version),
 UNIQUE(tenant_id,company_id,environment_id,run_id,event_id),
 UNIQUE(tenant_id,company_id,environment_id,run_id,event_id,request_digest)
);
CREATE TABLE t1_candidate.outbox (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, event_id text NOT NULL, request_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id,event_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,event_id,request_digest)
 REFERENCES t1_candidate.events(tenant_id,company_id,environment_id,run_id,event_id,request_digest)
);
CREATE TABLE t1_candidate.fences (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 effect_key text NOT NULL, idempotency_key text NOT NULL, request_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,effect_key),
 UNIQUE(tenant_id,company_id,environment_id,idempotency_key)
);
