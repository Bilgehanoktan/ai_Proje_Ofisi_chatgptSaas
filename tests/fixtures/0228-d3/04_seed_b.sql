-- Synthetic policy coverage rows, not a coherent lifecycle execution or business outcome.
-- Authenticate directly as aicos_d3_tenant_b; never use SET ROLE to seed.
BEGIN;
INSERT INTO aicos_d3_fixture.events VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1',1,'event-1','D0_RUN_ADMISSION','digest-1');
INSERT INTO aicos_d3_fixture.outbox VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1','event-1','digest-1');
INSERT INTO aicos_d3_fixture.fences VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','effect-1','idem-1','digest-1');
INSERT INTO aicos_d3_fixture.run_heads VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','plan-1','task-1','run-1','agent-1','principal-1','RUNNING',2,0);
INSERT INTO aicos_d3_fixture.run_leases VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1','plan-1','task-1','agent-1','principal-1','lease-1','grant-1',2,1,1,1,1,100,10);
INSERT INTO aicos_d3_fixture.run_mutations VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1',1,'tx-1','digest-1','QUEUED','ADMITTED',0);
INSERT INTO aicos_d3_fixture.run_audit VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1',1,'tx-1','digest-1','effect-1','idem-1','grant-1','lease-1',1,1,1,'lease-digest-1');
INSERT INTO aicos_d3_fixture.sample_budgets VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','budget-1',1,'TRY',100,40,0,false,1,1,'budget-digest-1');
INSERT INTO aicos_d3_fixture.run_admissions VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1','admission-1','tx-1','digest-1','lease-1','grant-1','budget-1');
INSERT INTO aicos_d3_fixture.sample_reservations VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1','budget-1',1,40,'TRY','digest-1','tx-1');
INSERT INTO aicos_d3_fixture.run_lease_renewals VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1',1,'tx-1','digest-1','lease-old','lease-new',2);
INSERT INTO aicos_d3_fixture.sample_settlements VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1',1,'tx-1','digest-1','admission-1','budget-1',40,0,2,'lease-digest-1','D0_LOCAL_FAILURE_NO_EFFECT');
INSERT INTO aicos_d3_fixture.events VALUES ('synthetic-tenant-b','synthetic-company-b','D3_SAMPLE_ONLY','run-1',2,'foreign-only','D3_FIXTURE_ONLY','foreign-only-digest');
COMMIT;
