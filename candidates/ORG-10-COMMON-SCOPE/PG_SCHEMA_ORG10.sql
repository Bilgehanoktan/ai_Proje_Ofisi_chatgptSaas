-- ORG-10: proposed common-scope PostgreSQL 17 fixture; NOT_RUN; DO NOT APPLY to product.
-- Precreate a dedicated database and five reviewed roles. No credentials or role grants here.
BEGIN;
DO $guard$
BEGIN
 IF current_database() <> 'aicos_org10_disposable' OR current_setting('cluster_name') <> 'aicos_org10_disposable' OR current_setting('port') <> '55436' OR current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999 OR current_user <> 'org10_admin' OR host(inet_server_addr()) IS DISTINCT FROM '127.0.0.1' OR host(inet_client_addr()) IS DISTINCT FROM '127.0.0.1' OR current_user <> session_user OR NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=current_user AND rolsuper) THEN RAISE EXCEPTION 'ORG10_DISPOSABLE_ADMIN_REQUIRED'; END IF;
 IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_database d JOIN pg_catalog.pg_roles r ON r.oid=d.datdba WHERE d.datname=current_database() AND r.rolname='aicos_org10_owner') THEN RAISE EXCEPTION 'ORG10_OWNER_REQUIRED'; END IF;
 IF (SELECT count(*) FROM pg_catalog.pg_roles WHERE rolname IN ('aicos_org10_owner','aicos_org10_writer_a','aicos_org10_writer_b','aicos_org10_reader_a','aicos_org10_unmapped')) <> 5 OR EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname IN ('aicos_org10_owner','aicos_org10_writer_a','aicos_org10_writer_b','aicos_org10_reader_a','aicos_org10_unmapped') AND (rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication OR rolinherit OR (rolname='aicos_org10_owner' AND rolcanlogin) OR (rolname<>'aicos_org10_owner' AND NOT rolcanlogin))) OR EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid=m.member OR r.oid=m.roleid WHERE r.rolname IN ('aicos_org10_owner','aicos_org10_writer_a','aicos_org10_writer_b','aicos_org10_reader_a','aicos_org10_unmapped')) THEN RAISE EXCEPTION 'ORG10_ROLE_BOUNDARY'; END IF;
END $guard$;
SET LOCAL ROLE aicos_org10_owner;
CREATE SCHEMA aicos_org10_fixture AUTHORIZATION aicos_org10_owner;
REVOKE ALL ON SCHEMA aicos_org10_fixture FROM PUBLIC;
SET LOCAL search_path=pg_catalog, aicos_org10_fixture;

CREATE TABLE aicos_org10_fixture.org_revision (
 t TEXT NOT NULL, c TEXT NOT NULL, e TEXT NOT NULL, rev TEXT NOT NULL,
 seq BIGINT NOT NULL CHECK(seq>0), prev TEXT, staffing_digest TEXT NOT NULL,
 prev_staffing TEXT, PRIMARY KEY(t,c,e,rev), UNIQUE(t,c,e,seq),
 FOREIGN KEY(t,c,e,prev) REFERENCES aicos_org10_fixture.org_revision(t,c,e,rev),
 CHECK((seq=1 AND prev IS NULL AND prev_staffing IS NULL) OR (seq>1 AND prev IS NOT NULL AND prev_staffing IS NOT NULL))
);
CREATE TABLE aicos_org10_fixture.org_head (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,
 PRIMARY KEY(t,c,e), FOREIGN KEY(t,c,e,rev) REFERENCES aicos_org10_fixture.org_revision(t,c,e,rev)
);
CREATE TABLE aicos_org10_fixture.org_unit (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('company','division','department','team')),parent TEXT,
 PRIMARY KEY(t,c,e,rev,id), FOREIGN KEY(t,c,e,rev) REFERENCES aicos_org10_fixture.org_revision(t,c,e,rev),
 FOREIGN KEY(t,c,e,rev,parent) REFERENCES aicos_org10_fixture.org_unit(t,c,e,rev,id) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE aicos_org10_fixture.org_position (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,
 unit TEXT NOT NULL,role TEXT NOT NULL,manager TEXT,
 PRIMARY KEY(t,c,e,rev,id), UNIQUE(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev,unit) REFERENCES aicos_org10_fixture.org_unit(t,c,e,rev,id),
 FOREIGN KEY(t,c,e,rev,manager) REFERENCES aicos_org10_fixture.org_position(t,c,e,rev,id) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE aicos_org10_fixture.org_definition_ref (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,role TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,id), UNIQUE(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev) REFERENCES aicos_org10_fixture.org_revision(t,c,e,rev)
);
CREATE TABLE aicos_org10_fixture.org_instance_ref (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,definition TEXT NOT NULL,role TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,id), UNIQUE(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev,definition,role) REFERENCES aicos_org10_fixture.org_definition_ref(t,c,e,rev,id,role)
);
CREATE TABLE aicos_org10_fixture.org_binding (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,seat TEXT NOT NULL,instance TEXT NOT NULL,role TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,seat), UNIQUE(t,c,e,rev,instance),
 FOREIGN KEY(t,c,e,rev,seat,role) REFERENCES aicos_org10_fixture.org_position(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev,instance,role) REFERENCES aicos_org10_fixture.org_instance_ref(t,c,e,rev,id,role)
);
CREATE TABLE aicos_org10_fixture.org_notice (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,
 digest TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind='ORG_REVISION_RECORDED_D0'),
 state TEXT NOT NULL CHECK(state='HOLD'), PRIMARY KEY(t,c,e,rev),
 FOREIGN KEY(t,c,e,rev) REFERENCES aicos_org10_fixture.org_revision(t,c,e,rev)
);



CREATE TABLE aicos_org10_fixture.op_team(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,coordinator TEXT NOT NULL,team_digest TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,project),FOREIGN KEY(t,c,e,rev,coordinator) REFERENCES aicos_org10_fixture.org_binding(t,c,e,rev,seat));
CREATE TABLE aicos_org10_fixture.op_member(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,seat TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,project,seat),FOREIGN KEY(t,c,e,rev,project) REFERENCES aicos_org10_fixture.op_team(t,c,e,rev,project),FOREIGN KEY(t,c,e,rev,seat) REFERENCES aicos_org10_fixture.org_binding(t,c,e,rev,seat));
CREATE TABLE aicos_org10_fixture.op_entry(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,seq BIGINT NOT NULL CHECK(seq>0),plan TEXT NOT NULL,task TEXT NOT NULL,sender TEXT NOT NULL,recipient TEXT NOT NULL,kind TEXT NOT NULL CHECK(kind IN ('delegation','handoff')),role TEXT NOT NULL,previous TEXT NOT NULL,digest TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,project,seq),UNIQUE(t,c,e,rev,project,plan,task,sender,recipient,kind),CHECK(sender<>recipient),FOREIGN KEY(t,c,e,rev,project,sender) REFERENCES aicos_org10_fixture.op_member(t,c,e,rev,project,seat),FOREIGN KEY(t,c,e,rev,project,recipient) REFERENCES aicos_org10_fixture.op_member(t,c,e,rev,project,seat),FOREIGN KEY(t,c,e,rev,recipient,role) REFERENCES aicos_org10_fixture.org_position(t,c,e,rev,id,role));
CREATE TABLE aicos_org10_fixture.op_notice(t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,project TEXT NOT NULL,seq BIGINT NOT NULL,digest TEXT NOT NULL,state TEXT NOT NULL CHECK(state='HOLD'),PRIMARY KEY(t,c,e,rev,project,seq),FOREIGN KEY(t,c,e,rev,project,seq) REFERENCES aicos_org10_fixture.op_entry(t,c,e,rev,project,seq));

GRANT USAGE ON SCHEMA aicos_org10_fixture TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
ALTER TABLE aicos_org10_fixture.org_revision ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_revision FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_revision FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_revision FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_revision FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_revision TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_revision TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_head ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_head FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_head FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_head FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_head FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_head TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_head TO aicos_org10_writer_a, aicos_org10_writer_b;
CREATE POLICY org_head_update ON aicos_org10_fixture.org_head FOR UPDATE TO aicos_org10_writer_a, aicos_org10_writer_b USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY'))))) WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT UPDATE (rev) ON aicos_org10_fixture.org_head TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_unit ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_unit FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_unit FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_unit FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_unit FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_unit TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_unit TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_position ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_position FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_position FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_position FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_position FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_position TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_position TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_definition_ref ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_definition_ref FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_definition_ref FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_definition_ref FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_definition_ref FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_definition_ref TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_definition_ref TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_instance_ref ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_instance_ref FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_instance_ref FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_instance_ref FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_instance_ref FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_instance_ref TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_instance_ref TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_binding ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_binding FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_binding FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_binding FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_binding FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_binding TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_binding TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.org_notice ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.org_notice FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.org_notice FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.org_notice FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.org_notice FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.org_notice TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.org_notice TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.op_team ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.op_team FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.op_team FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.op_team FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.op_team FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.op_team TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.op_team TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.op_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.op_member FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.op_member FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.op_member FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.op_member FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.op_member TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.op_member TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.op_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.op_entry FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.op_entry FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.op_entry FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.op_entry FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.op_entry TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.op_entry TO aicos_org10_writer_a, aicos_org10_writer_b;
ALTER TABLE aicos_org10_fixture.op_notice ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_org10_fixture.op_notice FORCE ROW LEVEL SECURITY;
REVOKE ALL ON aicos_org10_fixture.op_notice FROM PUBLIC, aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a, aicos_org10_unmapped;
CREATE POLICY org_read ON aicos_org10_fixture.op_notice FOR SELECT TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a USING ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
CREATE POLICY org_insert ON aicos_org10_fixture.op_notice FOR INSERT TO aicos_org10_writer_a, aicos_org10_writer_b WITH CHECK ((current_user = session_user AND ((session_user IN ('aicos_org10_writer_a','aicos_org10_reader_a') AND (t,c,e)=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')) OR (session_user='aicos_org10_writer_b' AND (t,c,e)=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')))));
GRANT SELECT ON aicos_org10_fixture.op_notice TO aicos_org10_writer_a, aicos_org10_writer_b, aicos_org10_reader_a;
GRANT INSERT ON aicos_org10_fixture.op_notice TO aicos_org10_writer_a, aicos_org10_writer_b;
COMMIT;
