-- D0 only; apply after 0192 and 0193 candidates in a disposable isolated database.
-- No authority, RLS, migration, admission, renewal or budget mapping is established.
CREATE TABLE t1_candidate.run_leases (
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
 FOREIGN KEY (tenant_id,company_id,environment_id,run_id) REFERENCES t1_candidate.run_heads(tenant_id,company_id,environment_id,run_id)
);
CREATE TABLE t1_candidate.run_mutations (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK (version > 0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 before_state text NOT NULL, after_state text NOT NULL, attempt bigint NOT NULL CHECK (attempt >= 0),
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id,version),
 UNIQUE (tenant_id,company_id,environment_id,transaction_ref),
 FOREIGN KEY (tenant_id,company_id,environment_id,run_id) REFERENCES t1_candidate.run_heads(tenant_id,company_id,environment_id,run_id)
);
CREATE TABLE t1_candidate.run_audit (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK (version > 0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 effect_key text NOT NULL, idempotency_key text NOT NULL, grant_ref text NOT NULL, lease_ref text NOT NULL,
 policy_epoch bigint NOT NULL, witness_epoch bigint NOT NULL, lease_fence bigint NOT NULL CHECK (lease_fence > 0),
 lease_digest text NOT NULL,
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id,version),
 FOREIGN KEY (tenant_id,company_id,environment_id,run_id,version) REFERENCES t1_candidate.run_mutations(tenant_id,company_id,environment_id,run_id,version)
);
