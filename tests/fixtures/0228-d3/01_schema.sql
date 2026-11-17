-- 0228 D3-R1 FIXTURE ONLY. Exact D0 derivation; not migration or canonical mapping.
-- Run connected to aicos_d3_0228 as trusted disposable administrator.
BEGIN;
SET LOCAL ROLE aicos_d3_owner;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
-- 0192 candidate only; do not apply to production. R03 mapping HOLD.
CREATE SCHEMA aicos_d3_fixture AUTHORIZATION aicos_d3_owner;
CREATE TABLE aicos_d3_fixture.events (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version > 0),
 event_id text NOT NULL, event_type text NOT NULL, request_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id,version),
 UNIQUE(tenant_id,company_id,environment_id,run_id,event_id),
 UNIQUE(tenant_id,company_id,environment_id,run_id,event_id,request_digest)
);
CREATE TABLE aicos_d3_fixture.outbox (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, event_id text NOT NULL, request_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id,event_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,event_id,request_digest)
 REFERENCES aicos_d3_fixture.events(tenant_id,company_id,environment_id,run_id,event_id,request_digest)
);
CREATE TABLE aicos_d3_fixture.fences (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 effect_key text NOT NULL, idempotency_key text NOT NULL, request_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,effect_key),
 UNIQUE(tenant_id,company_id,environment_id,idempotency_key)
);

-- 0193 D0 candidate only. Apply only in a disposable isolated schema after review.
-- Depends on 0192 aicos_d3_fixture schema; not canonical R03 mapping, no automatic migration.
CREATE TABLE aicos_d3_fixture.run_heads (
 tenant_id text NOT NULL ,
 company_id text NOT NULL ,
 environment_id text NOT NULL ,
 plan_revision text NOT NULL, task_id text NOT NULL, run_id text NOT NULL,
 agent_instance_id text NOT NULL, principal_id text NOT NULL,
 state text NOT NULL CHECK (state IN ('CREATED','QUEUED','ADMITTED','PLANNING','RUNNING','WAITING_APPROVAL','VERIFYING','SUCCEEDED','FAILED','CANCELLED','TIMED_OUT')),
 version bigint NOT NULL CHECK (version >= 0), attempt bigint NOT NULL CHECK (attempt >= 0),
 CHECK ((tenant_id,company_id,environment_id) IN (('synthetic-tenant-a','synthetic-company-a','D3_SAMPLE_ONLY'),('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY'))),
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id)
);

-- D0 only; apply after 0192 and 0193 candidates in a disposable isolated database.
-- No authority, RLS, migration, admission, renewal or budget mapping is established.
CREATE TABLE aicos_d3_fixture.run_leases (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, plan_revision text NOT NULL, task_id text NOT NULL,
 agent_instance_id text NOT NULL, principal_id text NOT NULL,
 lease_id text NOT NULL, grant_id text NOT NULL,
 lease_version bigint NOT NULL CHECK (lease_version > 0),
 heartbeat_revision bigint NOT NULL CHECK (heartbeat_revision >= 0),
 fence bigint NOT NULL CHECK (fence > 0), policy_epoch bigint NOT NULL CHECK (policy_epoch >= 0),
 witness_epoch bigint NOT NULL CHECK (witness_epoch >= 0),
 expires_tick bigint NOT NULL, heartbeat_tick bigint NOT NULL CHECK (heartbeat_tick >= 0 AND heartbeat_tick < expires_tick),
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY (tenant_id,company_id,environment_id,run_id) REFERENCES aicos_d3_fixture.run_heads(tenant_id,company_id,environment_id,run_id)
);
CREATE TABLE aicos_d3_fixture.run_mutations (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK (version > 0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 before_state text NOT NULL, after_state text NOT NULL, attempt bigint NOT NULL CHECK (attempt >= 0),
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id,version),
 UNIQUE (tenant_id,company_id,environment_id,transaction_ref),
 FOREIGN KEY (tenant_id,company_id,environment_id,run_id) REFERENCES aicos_d3_fixture.run_heads(tenant_id,company_id,environment_id,run_id)
);
CREATE TABLE aicos_d3_fixture.run_audit (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK (version > 0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 effect_key text NOT NULL, idempotency_key text NOT NULL, grant_ref text NOT NULL, lease_ref text NOT NULL,
 policy_epoch bigint NOT NULL, witness_epoch bigint NOT NULL, lease_fence bigint NOT NULL CHECK (lease_fence > 0),
 lease_digest text NOT NULL,
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id,version),
 FOREIGN KEY (tenant_id,company_id,environment_id,run_id,version) REFERENCES aicos_d3_fixture.run_mutations(tenant_id,company_id,environment_id,run_id,version)
);

-- D0 disposable candidate only, after 0192/0193/0194. No canonical grant or spend.
CREATE UNIQUE INDEX d0_unique_plan_task ON aicos_d3_fixture.run_heads(tenant_id,company_id,environment_id,plan_revision,task_id);
CREATE TABLE aicos_d3_fixture.sample_budgets (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 budget_id text NOT NULL, revision bigint NOT NULL CHECK(revision>=0),
 currency text NOT NULL, limit_minor bigint NOT NULL CHECK(limit_minor>=0),
 outstanding_minor bigint NOT NULL CHECK(outstanding_minor>=0),
 recognized_cost_minor bigint NOT NULL CHECK(recognized_cost_minor>=0),
 unknown_cost boolean NOT NULL, policy_epoch bigint NOT NULL, witness_epoch bigint NOT NULL,
 source_digest text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,budget_id),
 CHECK(outstanding_minor <= limit_minor - recognized_cost_minor)
);
CREATE TABLE aicos_d3_fixture.run_admissions (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, admission_id text NOT NULL, transaction_ref text NOT NULL,
 request_digest text NOT NULL, lease_id text NOT NULL, grant_id text NOT NULL, budget_id text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 UNIQUE(tenant_id,company_id,environment_id,admission_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id) REFERENCES aicos_d3_fixture.run_heads(tenant_id,company_id,environment_id,run_id)
);
CREATE TABLE aicos_d3_fixture.sample_reservations (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, budget_id text NOT NULL, budget_revision bigint NOT NULL,
 amount_minor bigint NOT NULL CHECK(amount_minor>0), currency text NOT NULL,
 request_digest text NOT NULL, transaction_ref text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id) REFERENCES aicos_d3_fixture.run_admissions(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,budget_id) REFERENCES aicos_d3_fixture.sample_budgets(tenant_id,company_id,environment_id,budget_id)
);

-- D0 disposable only; after 0192–0195. R03 HOLD. No production migration.
CREATE TABLE aicos_d3_fixture.run_lease_renewals (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version>0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 old_lease_digest text NOT NULL, new_lease_digest text NOT NULL,
 lease_version bigint NOT NULL CHECK(lease_version>1),
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id,version),
 UNIQUE(tenant_id,company_id,environment_id,run_id,lease_version),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,version)
 REFERENCES aicos_d3_fixture.run_mutations(tenant_id,company_id,environment_id,run_id,version)
 DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE aicos_d3_fixture.sample_settlements (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version>0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 admission_id text NOT NULL, budget_id text NOT NULL,
 released_minor bigint NOT NULL CHECK(released_minor>0),
 recognized_minor bigint NOT NULL CHECK(recognized_minor=0),
 budget_revision bigint NOT NULL CHECK(budget_revision>0),
 lease_digest text NOT NULL, outcome text NOT NULL CHECK(outcome='D0_LOCAL_FAILURE_NO_EFFECT'),
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id) REFERENCES aicos_d3_fixture.sample_reservations(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,version) REFERENCES aicos_d3_fixture.run_mutations(tenant_id,company_id,environment_id,run_id,version) DEFERRABLE INITIALLY DEFERRED
);

REVOKE ALL ON SCHEMA aicos_d3_fixture FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA aicos_d3_fixture FROM PUBLIC;
COMMIT;
