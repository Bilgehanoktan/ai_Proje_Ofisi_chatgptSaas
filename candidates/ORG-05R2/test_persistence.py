import json, sqlite3, tempfile, unittest
from pathlib import Path
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from jsonschema import Draft202012Validator, ValidationError
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from persistence import Scope, Store, initialize

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'org.db'; initialize(self.path)
        self.scope=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
        self.store=Store(self.path,self.scope); self.s=self.fixture(self.scope)
    def fixture(self,scope):
        t,c,_=scope.key()
        return Staffing(Org(t,c,(Unit(c,'company',None),Unit('d','department',c)),(Seat('lead','d','lead'),Seat('worker','d','research','lead'))),(Definition('dl','lead'),Definition('dr','research')),(Instance('demo-l','dl',t,c),Instance('demo-w','dr',t,c)),(Binding('lead','demo-l'),Binding('worker','demo-w')))
    def record(self): return self.store.record(self.s,None)
    def successor(self): return replace(self.s,previous=self.s.revision(),bindings=self.s.bindings[:1])
    def count(self,table):
        with sqlite3.connect(self.path) as db: return db.execute('SELECT count(*) FROM '+table).fetchone()[0]
    def test_reopen(self):
        r=self.record(); got=Store(self.path,self.scope).read(); self.assertEqual(got[0],r); self.assertEqual(got[1][0].revision(),self.s.revision())
    def test_successor(self):
        a=self.record(); b=self.store.record(self.successor(),a); self.assertEqual(self.store.read()[0],b); self.assertEqual(self.store.read(a)[1][1],1); self.assertEqual(self.store.audit(b),2)
    def test_stale_head(self):
        self.record()
        with self.assertRaises(ValueError): self.store.record(self.s,None)
        self.assertEqual(self.count('org_revision'),1)
    def test_wrong_parent(self):
        a=self.record()
        with self.assertRaises(ValueError): self.store.record(replace(self.s,previous='a'*64),a)
        self.assertEqual(self.store.read()[0],a)
    def test_genesis_parent(self):
        with self.assertRaises(ValueError): self.store.record(self.successor(),None)
    def test_cross_tenant(self):
        a=self.record(); other=replace(self.scope,tenant='synthetic-other'); b=Store(self.path,other)
        with self.assertRaises(ValueError): b.read(a)
        with self.assertRaises(ValueError): b.record(self.s,None)
        self.assertNotEqual(b.record(self.fixture(other),None),a)
    def test_cross_company(self):
        a=self.record(); b=Store(self.path,replace(self.scope,company='synthetic-other'))
        with self.assertRaises(ValueError): b.read(a)
    def test_cross_environment(self):
        a=self.record(); b=Store(self.path,replace(self.scope,environment='A0_REVIEW_ONLY'))
        with self.assertRaises(ValueError): b.read(a)
        self.assertNotEqual(b.record(self.s,None),a)
        self.assertEqual(self.store.read()[0],a)
    def test_prod_scope_rejected(self):
        with self.assertRaises(ValueError): Store(self.path,replace(self.scope,environment='PROD'))
    def test_rollback_on_notice_failure(self):
        a=self.record()
        with sqlite3.connect(self.path) as db: db.execute("CREATE TRIGGER fail_notice BEFORE INSERT ON org_notice BEGIN SELECT RAISE(ABORT,'TEST_FAILURE'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.store.record(self.successor(),a)
        self.assertEqual(self.store.read()[0],a)
        for table,n in [('org_revision',1),('org_unit',2),('org_position',2),('org_binding',2),('org_notice',1)]: self.assertEqual(self.count(table),n)
    def test_rollback_after_head_update(self):
        a=self.record()
        with sqlite3.connect(self.path) as db: db.execute("CREATE TRIGGER fail_head AFTER UPDATE ON org_head BEGIN SELECT RAISE(ABORT,'TEST_FAILURE'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.store.record(self.successor(),a)
        self.assertEqual(self.store.read()[0],a); self.assertEqual(self.count('org_notice'),1)
    def test_concurrent_cas(self):
        a=self.record(); s=self.successor()
        def attempt(_):
            try: return Store(self.path,self.scope).record(s,a)
            except ValueError as err: return str(err)
        with ThreadPoolExecutor(max_workers=2) as ex: results=list(ex.map(attempt,range(2)))
        self.assertEqual(results.count('STALE_HEAD'),1); self.assertEqual(self.count('org_revision'),2)
    def test_sql_immutable(self):
        self.record()
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute("UPDATE org_position SET role='qa'")
            with self.assertRaises(sqlite3.IntegrityError): db.execute('DELETE FROM org_notice')
    def test_sql_cross_scope_fk(self):
        a=self.record()
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError): db.execute('INSERT INTO org_head VALUES (?,?,?,?)',('synthetic-other',self.scope.company,self.scope.environment,a))
    def test_sql_role_fk(self):
        a=self.record(); b=self.store.record(self.successor(),a)
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA foreign_keys=ON')
            with self.assertRaisesRegex(sqlite3.IntegrityError,'FOREIGN KEY'): db.execute('INSERT INTO org_binding VALUES (?,?,?,?,?,?,?)',self.scope.key()+(b,'worker','demo-w','lead'))
    def test_mutated_snapshot(self):
        a=self.record()
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER org_position_update'); db.execute("UPDATE org_position SET manager=NULL WHERE id='worker'")
        with self.assertRaises(ValueError): self.store.read(a)
    def test_notice_tamper(self):
        a=self.record()
        with sqlite3.connect(self.path) as db:
            db.execute('DROP TRIGGER org_notice_update'); db.execute("UPDATE org_notice SET digest='bad'")
        with self.assertRaises(ValueError): self.store.read(a)
    def test_head_rewind(self):
        a=self.record(); b=self.store.record(self.successor(),a)
        with sqlite3.connect(self.path) as db: db.execute('UPDATE org_head SET rev=?',(a,))
        with self.assertRaises(ValueError): self.store.audit(b)
    def test_read_only_connection(self):
        self.record(); db=self.store._connect()
        try:
            with self.assertRaises(sqlite3.OperationalError): db.execute('DELETE FROM org_head')
        finally: db.close()
    def test_existing_file_rejected(self):
        with self.assertRaises(FileExistsError): initialize(self.path)
    def test_studio_schema(self):
        a=self.record(); schema=json.loads(Path(__file__).with_name('studio.schema.json').read_text()); Draft202012Validator.check_schema(schema); v=Draft202012Validator(schema); p=self.store.studio_view(a); v.validate(p)
        self.assertNotIn('demo-w',json.dumps(p)); self.assertIsNone(p['runtime_binding']); self.assertFalse(p['dispatch_allowed'])
        for k,bad in [('decision','ALLOW'),('authoritative',True),('identity_owner','VERIFIED'),('geometry_join','ALLOW'),('dispatch_allowed',True),('runtime_binding','demo-run')]:
            with self.subTest(k=k),self.assertRaises(ValidationError): v.validate({**p,k:bad})
        with self.assertRaises(ValidationError): v.validate({**p,'principal_id':'demo-principal'})
    def test_studio_empty(self):
        with self.assertRaises(ValueError): self.store.studio_view('a'*64)
    def test_studio_stale(self):
        a=self.record(); self.store.record(self.successor(),a)
        with self.assertRaises(ValueError): self.store.studio_view(a)
    def test_live_instance_reference_rejected(self):
        s=replace(self.s,instances=(replace(self.s.instances[0],id='actual-l'),self.s.instances[1]),bindings=(Binding('lead','actual-l'),self.s.bindings[1]))
        with self.assertRaises(ValueError): self.store.record(s,None)
    def test_backup_restore_separate_file(self):
        a=self.record(); backup=Path(self.tmp.name)/'backup.db'
        with sqlite3.connect(self.path) as source, sqlite3.connect(backup) as target: source.backup(target)
        b=self.store.record(self.successor(),a); restored=Store(backup,self.scope)
        self.assertEqual(restored.audit(a),1); self.assertEqual(self.store.audit(b),2)
        with self.assertRaises(ValueError): restored.audit(b)
