-- 0193 D0 candidate only. Apply only in a disposable isolated schema after review.
-- Depends on 0192 t1_candidate schema; not canonical R03 mapping, no automatic migration.
CREATE TABLE t1_candidate.run_heads (
 tenant_id text NOT NULL CHECK (tenant_id = 'synthetic-tenant'),
 company_id text NOT NULL CHECK (company_id = 'synthetic-company'),
 environment_id text NOT NULL CHECK (environment_id = 'A0_SAMPLE_ONLY'),
 plan_revision text NOT NULL, task_id text NOT NULL, run_id text NOT NULL,
 agent_instance_id text NOT NULL, principal_id text NOT NULL,
 state text NOT NULL CHECK (state IN ('CREATED','QUEUED','ADMITTED','PLANNING','RUNNING','WAITING_APPROVAL','VERIFYING','SUCCEEDED','FAILED','CANCELLED','TIMED_OUT')),
 version bigint NOT NULL CHECK (version >= 0), attempt bigint NOT NULL CHECK (attempt >= 0),
 PRIMARY KEY (tenant_id,company_id,environment_id,run_id)
);
