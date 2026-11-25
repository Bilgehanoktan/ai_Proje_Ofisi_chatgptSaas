-- D0 disposable only; after 0192–0195. R03 HOLD. No production migration.
CREATE TABLE t1_candidate.run_lease_renewals (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version>0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 old_lease_digest text NOT NULL, new_lease_digest text NOT NULL,
 lease_version bigint NOT NULL CHECK(lease_version>1),
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id,version),
 UNIQUE(tenant_id,company_id,environment_id,run_id,lease_version),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,version)
 REFERENCES t1_candidate.run_mutations(tenant_id,company_id,environment_id,run_id,version)
 DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE t1_candidate.sample_settlements (
 tenant_id text NOT NULL, company_id text NOT NULL, environment_id text NOT NULL,
 run_id text NOT NULL, version bigint NOT NULL CHECK(version>0),
 transaction_ref text NOT NULL, request_digest text NOT NULL,
 admission_id text NOT NULL, budget_id text NOT NULL,
 released_minor bigint NOT NULL CHECK(released_minor>0),
 recognized_minor bigint NOT NULL CHECK(recognized_minor=0),
 budget_revision bigint NOT NULL CHECK(budget_revision>0),
 lease_digest text NOT NULL, outcome text NOT NULL CHECK(outcome='D0_LOCAL_FAILURE_NO_EFFECT'),
 PRIMARY KEY(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id) REFERENCES t1_candidate.sample_reservations(tenant_id,company_id,environment_id,run_id),
 FOREIGN KEY(tenant_id,company_id,environment_id,run_id,version) REFERENCES t1_candidate.run_mutations(tenant_id,company_id,environment_id,run_id,version) DEFERRABLE INITIALLY DEFERRED
);
