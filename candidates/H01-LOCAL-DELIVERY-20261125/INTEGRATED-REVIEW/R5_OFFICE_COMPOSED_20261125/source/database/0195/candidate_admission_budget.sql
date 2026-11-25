-- D0 disposable candidate only, after 0192/0193/0194. No canonical grant or spend.
CREATE UNIQUE INDEX d0_unique_plan_task ON t1_candidate.run_heads(tenant_id,company_id,environment_id,plan_revision,task_id);
CREATE TABLE t1_candidate.sample_budgets (
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
CREATE TABLE t1_candidate.run_admissions (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, admission_id text NOT NULL, transaction_ref text NOT NULL,
 request_digest text NOT NULL, lease_id text NOT NULL, grant_id text NOT NULL, budget_id text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 UNIQUE(tenant_id,company_id,environment_id,admission_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id) REFERENCES t1_candidate.run_heads(tenant_id,company_id,environment_id,run_id)
);
CREATE TABLE t1_candidate.sample_reservations (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, budget_id text NOT NULL, budget_revision bigint NOT NULL,
 amount_minor bigint NOT NULL CHECK(amount_minor>0), currency text NOT NULL,
 request_digest text NOT NULL, transaction_ref text NOT NULL,
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id) REFERENCES t1_candidate.run_admissions(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,budget_id) REFERENCES t1_candidate.sample_budgets(tenant_id,company_id,environment_id,budget_id)
);
