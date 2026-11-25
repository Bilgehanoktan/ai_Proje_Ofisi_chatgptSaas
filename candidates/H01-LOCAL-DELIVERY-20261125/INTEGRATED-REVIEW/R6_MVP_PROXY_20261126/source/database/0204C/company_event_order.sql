-- D0 disposable candidate, after 0196-L. R03/ownership/RLS HOLD. No production migration.
CREATE TABLE t1_candidate.company_run_membership (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 project_id text NOT NULL, plan_revision text NOT NULL, task_id text NOT NULL, run_id text NOT NULL,
 agent_instance_id text NOT NULL, principal_id text NOT NULL,
 initial_version bigint NOT NULL CHECK(initial_version>=0),
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 UNIQUE(tenant_id,company_id,environment_id,project_id,plan_revision,task_id),
 UNIQUE(tenant_id,company_id,environment_id,project_id,run_id)
);
CREATE TABLE t1_candidate.company_stream_heads (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 sequence bigint NOT NULL CHECK(sequence>=0),
 PRIMARY KEY(tenant_id,company_id,environment_id)
);
CREATE TABLE t1_candidate.company_event_order (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 sequence bigint NOT NULL CHECK(sequence>0), project_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version>0),
 transaction_ref text NOT NULL, request_digest text NOT NULL CHECK(length(request_digest)=64),
 predecessors text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,sequence),
 UNIQUE(tenant_id,company_id,environment_id,run_id,version),
 UNIQUE(tenant_id,company_id,environment_id,transaction_ref),
 FOREIGN KEY(tenant_id,company_id,environment_id,project_id,run_id)
 REFERENCES t1_candidate.company_run_membership(tenant_id,company_id,environment_id,project_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,version)
 REFERENCES t1_candidate.events(tenant_id,company_id,environment_id,run_id,version)
 DEFERRABLE INITIALLY DEFERRED
);
