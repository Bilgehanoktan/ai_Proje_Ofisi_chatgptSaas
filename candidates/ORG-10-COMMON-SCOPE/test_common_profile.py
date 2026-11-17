"""Actual local source/contract tests, and fake-DB boundary tests; no PostgreSQL."""
from pathlib import Path
from dataclasses import replace
import ast, hashlib, os, re, tempfile, unittest
from derive_common import (source, derive, verify_generated, PINS, SCHEMA, DATABASE,
                           CLUSTER, PORT, SCOPE, CONTROL, ROLES, TABLES, names, exact)
from pg_transaction import run, Hold, WRITERS, READERS, R3Read
from pg_operations import PgOperations
from test_pg_protocol import Fake

HERE=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('ORG10_SOURCE_ROOT',HERE.parents[1])).resolve()

class DerivedSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=source(ROOT); cls.generated=derive(cls.original)
        cls.ddl=cls.generated['PG_SCHEMA_ORG10.sql'].decode()
        cls.boot=cls.generated['bootstrap_roles.sql'].decode()
        cls.runner=cls.generated['run_pg_acceptance.py'].decode()
    def test_01_original_pins(self): self.assertEqual(len(self.original),6)
    def test_02_exact_output(self): self.assertEqual(verify_generated(HERE,self.generated),6)
    def test_03_tables(self):
        self.assertEqual(re.findall(r'CREATE TABLE '+SCHEMA+r'\.([a-z_]+)',self.ddl),list(TABLES))
    def test_04_table_constraints_unchanged(self):
        a=names(self.original['PG_SCHEMA_R4.sql']); b=self.ddl
        self.assertEqual(a[a.index('CREATE TABLE '):a.index('GRANT USAGE ON SCHEMA')],b[b.index('CREATE TABLE '):b.index('GRANT USAGE ON SCHEMA')])
    def test_05_policy_count_and_commands(self):
        found=re.findall(r'CREATE POLICY (\w+) ON '+SCHEMA+r'\.(\w+) FOR (\w+)',self.ddl)
        self.assertEqual(len(found),25)
        self.assertEqual(set(found),{(p,t,c) for t in TABLES for p,c in (('org_read','SELECT'),('org_insert','INSERT'))}|{('org_head_update','org_head','UPDATE')})
    def test_06_force_all(self):
        for t in TABLES:
            for mode in ('ENABLE','FORCE'):
                self.assertEqual(self.ddl.count(f'ALTER TABLE {SCHEMA}.{t} {mode} ROW LEVEL SECURITY;'),1)
    def test_07_policy_predicates(self):
        a,b,r=ROLES[1:4]
        expr=f"((current_user = session_user AND ((session_user IN ('{a}','{r}') AND (t,c,e)=('{SCOPE[0]}','{SCOPE[1]}','{SCOPE[2]}')) OR (session_user='{b}' AND (t,c,e)=('{CONTROL[0]}','{CONTROL[1]}','{CONTROL[2]}')))))"
        lines=[line for line in self.ddl.splitlines() if line.startswith('CREATE POLICY ')]
        for line in lines:
            self.assertIn(expr,line)
            self.assertEqual(line.count(expr),2 if 'org_head_update' in line else 1)
            if 'FOR SELECT' not in line:
                self.assertNotIn(r,line.split(' USING ')[0].split(' WITH CHECK ')[0])
    def test_08_grants(self):
        grants=[line for line in self.ddl.splitlines() if line.startswith('GRANT ')]
        self.assertEqual(len(grants),26)
        self.assertEqual([line for line in grants if 'UPDATE' in line],[f'GRANT UPDATE (rev) ON {SCHEMA}.org_head TO {ROLES[1]}, {ROLES[2]};'])
        self.assertFalse(any('PUBLIC' in line or 'GRANT ALL' in line or 'GRANT DELETE' in line for line in grants))
        for t in TABLES:
            self.assertIn(f'GRANT SELECT ON {SCHEMA}.{t} TO {ROLES[1]}, {ROLES[2]}, {ROLES[3]};',grants)
            self.assertIn(f'GRANT INSERT ON {SCHEMA}.{t} TO {ROLES[1]}, {ROLES[2]};',grants)
    def test_09_new_namespace_only(self):
        for text in (self.ddl,self.boot,self.generated['pg_transaction.py'].decode()):
            self.assertNotIn('aicos_org_r4_',text); self.assertNotIn('aicos_org_r5_',text)
            self.assertNotIn('ORG_R4_SAMPLE_ONLY',text)
    def test_10_fresh_local_guards(self):
        for text in (self.ddl,self.boot):
            for token in (CLUSTER,str(PORT),'org10_admin','server_version_num','inet_client_addr()','inet_server_addr()','127.0.0.1','session_user','rolsuper'):
                self.assertIn(token,text)
        self.assertIn("rolname<>current_user AND left(rolname,3)<>'pg_'",self.boot)
        self.assertIn("datname NOT IN ('postgres','template0','template1')",self.boot)
    def test_11_bootstrap_roles(self):
        roles=re.findall(r'CREATE ROLE (\w+) (NOLOGIN|LOGIN) NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;',self.boot)
        self.assertEqual(roles,[(r,'NOLOGIN' if i==0 else 'LOGIN') for i,r in enumerate(ROLES)])
        self.assertIn(f'REVOKE CONNECT,TEMPORARY ON DATABASE {DATABASE} FROM PUBLIC;',self.boot)
        self.assertEqual(self.boot.count('\\password '),4)
    def test_12_no_reimplemented_ops(self):
        self.assertEqual(self.generated['pg_operations.py'],self.original['pg_operations.py'].encode())
    def test_13_runner_ids(self):
        ids=re.findall(r"check\('(PG\d\d_[A-Z_]+)'",self.runner)
        orig=re.findall(r"check\('(PG\d\d_[A-Z_]+)'",self.original['run_pg_acceptance.py'])
        self.assertEqual(ids[:26],orig); self.assertEqual(len(ids),31); self.assertEqual(len(set(ids)),31)
        self.assertEqual(ids[26:],['PG27_TENANT_ONLY','PG28_OLD_SCOPE_A','PG29_OLD_SCOPE_B','PG30_REVERSE_SCOPE_READ','PG31_ACL_MATRIX'])
    def test_14_runner_no_automatic_install(self):
        self.assertIn('args.port!=55436',self.runner); self.assertIn('not args.execute_disposable',self.runner)
        self.assertIn("metadata.version('psycopg')!='3.3.9'",self.runner)
        self.assertIn('verify_generated(Path(__file__).resolve().parent',self.runner)
        self.assertNotIn('subprocess',self.runner)
    def test_15_all_python_parse(self):
        for n,b in self.generated.items():
            if n.endswith('.py'): ast.parse(b)
    def test_16_tamper_output(self):
        with tempfile.TemporaryDirectory() as d:
            for n,b in self.generated.items(): (Path(d)/n).write_bytes(b)
            (Path(d)/'pg_transaction.py').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'GENERATED_SOURCE_HOLD'):verify_generated(d,self.generated)
    def test_17_tamper_original(self):
        with tempfile.TemporaryDirectory() as d:
            for path in PINS:
                p=Path(d)/'candidates'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/'candidates'/path).read_bytes())
            (Path(d)/'candidates/ORG-05R4/PG_SCHEMA_R4.sql').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'ORIGINAL_SOURCE_PIN_HOLD'): source(d)
    def test_18_no_fuzzy_patch(self):
        for value in ('missing','twice twice'):
            with self.assertRaisesRegex(ValueError,'DERIVATION_TARGET_HOLD'):exact(value,'twice','x')

class ProfileBoundary(unittest.TestCase):
    def test_common_scope_exact(self):
        self.assertEqual(WRITERS,{ROLES[1]:SCOPE,ROLES[2]:CONTROL});self.assertEqual(READERS[ROLES[3]],SCOPE)
        self.assertEqual(PgOperations(lambda:None,SCOPE).scope,SCOPE)
    def test_old_scopes_refused_before_connect(self):
        for t,c in [('synthetic-tenant-a','synthetic-company-a'),('synthetic-tenant-b','synthetic-company-b')]:
            with self.assertRaisesRegex(Hold,'PG_SCOPE'):
                run(lambda:self.fail('connected'),(t,c,'ORG_R4_SAMPLE_ONLY'),True,lambda d:None)
    def test_each_axis_refused_before_connect(self):
        for scope in ((CONTROL[0],SCOPE[1],SCOPE[2]),(SCOPE[0],CONTROL[1],SCOPE[2]),(SCOPE[0],SCOPE[1],'ORG_R4_SAMPLE_ONLY')):
            with self.assertRaisesRegex(Hold,'PG_SCOPE'):run(lambda:self.fail('connected'),scope,False,lambda d:None)
    def test_port_mismatch(self):
        for port in ('55433','55434','55435','5432'):
            d=Fake();d.row=(*d.row[:15],port)
            with self.assertRaisesRegex(Hold,'PG_PORT'):run(lambda:d,SCOPE,True,lambda db:self.fail())
            self.assertNotIn('commit',d.calls)
    def test_socket_mismatch(self):
        d=Fake();d.row=(*d.row[:9],None,*d.row[10:])
        with self.assertRaisesRegex(Hold,'PG_LOCAL_ONLY'):run(lambda:d,SCOPE,True,lambda db:self.fail())
    def test_control_scope_own_role(self):
        d=Fake(False);d.row=(d.row[0],ROLES[2],ROLES[2],*d.row[3:])
        self.assertEqual(run(lambda:d,CONTROL,False,lambda db:1),1)
        self.assertNotIn('commit',d.calls)
    def test_control_scope_cannot_read_common(self):
        d=Fake(False);d.row=(d.row[0],ROLES[2],ROLES[2],*d.row[3:])
        with self.assertRaisesRegex(Hold,'PG_SCOPE_ROLE'):run(lambda:d,SCOPE,False,lambda db:self.fail())
    def test_port_drift_rollback(self):
        d=Fake()
        def changed(db): db.row=(*db.row[:15],'55435'); return 1
        with self.assertRaisesRegex(Hold,'PG_PORT'):run(lambda:d,SCOPE,True,changed)
        self.assertEqual(d.calls[-2:],['rollback','close'])
