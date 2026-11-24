-- D0 disposable candidate only, after 0196-L; canonical R03/ownership HOLD.
-- Apply outside T1 before isolated tests. No backfill and no production migration.
CREATE TABLE t1_candidate.terminal_command_anchors (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 plan_revision text NOT NULL, run_id text NOT NULL,
 version bigint NOT NULL CHECK(version>0), transaction_ref text NOT NULL,
 request_digest text NOT NULL CHECK(length(request_digest)=64),
 command_sha text NOT NULL CHECK(length(command_sha)=64),
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 UNIQUE(tenant_id,company_id,environment_id,transaction_ref),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,version)
 REFERENCES t1_candidate.run_mutations(tenant_id,company_id,environment_id,run_id,version)
 DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id)
 REFERENCES t1_candidate.sample_settlements(tenant_id,company_id,environment_id,run_id)
 DEFERRABLE INITIALLY DEFERRED
);
