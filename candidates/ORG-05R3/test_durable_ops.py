import sqlite3, tempfile, unittest
from pathlib import Path
from contextlib import closing
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from persistence import Scope
from operations import ProjectTeam
from office_bridge import OfficeView, Room
from durable_ops import initialize_ops, OperationsStore, TaskPin, HistoryPin, OfficePin, ReadSession, studio_read, ZERO


class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'org.db'; initialize_ops(self.path)
        self.scope=Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY'); t,c,_=self.scope.key()
        self.store=OperationsStore(self.path,self.scope)
        self.s=Staffing(Org(t,c,(Unit(c,'company',None),Unit('a','department',c),Unit('b','department',c)),(Seat('l','a','lead'),Seat('w','a','research','l'),Seat('x','b','research'))),(Definition('dl','lead'),Definition('dr','research')),(Instance('demo-l','dl',t,c),Instance('demo-w','dr',t,c),Instance('demo-x','dr',t,c)),(Binding('l','demo-l'),Binding('w','demo-w'),Binding('x','demo-x')))
        self.rev=self.store.record(self.s,None)
        self.team=ProjectTeam(t,c,self.s.revision(),'demo-project','l',('l','w','x'))
        self.store.create_team(self.rev,self.team)
        self.pin=TaskPin(self.scope,self.team.project,'sha256:'+'a'*64,'plan','research')
        self.empty=HistoryPin(0,ZERO)
        self.office=OfficeView(t,c,'d0-world','layout-r1',(Room('d0-f1/m','d0-f1','MEETING'),),(),())
        self.op=OfficePin(self.scope,self.office.world,self.office.revision())
    def append(self,**kw):
        args=dict(rev=self.rev,observed=self.pin,expected=self.pin,sender='w',recipient='x',kind='handoff',history_pin=self.empty); args.update(kw)
        return self.store.append_proposal(**args)
    def view(self,pin,**kw):
        args=dict(rev=self.rev,project_id=self.team.project,history_pin=pin,office=self.office,office_pin=self.op); args.update(kw); return self.store.combined(**args)
    def count(self,table):
        with closing(sqlite3.connect(self.path)) as db, db: return db.execute('SELECT count(*) FROM '+table).fetchone()[0]
    def test_reopen_handoff(self):
        p=self.append(); self.store=OperationsStore(self.path,self.scope); v=self.view(p,meeting_room='d0-f1/m'); self.assertEqual(v['proposals'][0]['kind'],'handoff'); self.assertTrue(v['meeting_proposed']); self.assertIsNone(v['runtime_binding']); self.assertFalse(v['dispatch_allowed'])
    def test_delegation(self): self.assertEqual(self.append(sender='l',recipient='w',kind='delegation').count,1)
    def test_reverse(self):
        with self.assertRaises(ValueError): self.append(sender='w',recipient='l',kind='delegation')
    def test_stale_revision(self):
        self.store.record(replace(self.s,previous=self.s.revision()),self.rev)
        with self.assertRaises(ValueError): self.append()
        with self.assertRaises(ValueError): self.view(self.empty)
    def test_task_mismatch(self):
        with self.assertRaises(ValueError): self.append(observed=replace(self.pin,task='other'))
    def test_role_mismatch(self):
        p=replace(self.pin,role='qa')
        with self.assertRaises(ValueError): self.append(observed=p,expected=p)
    def test_wrong_environment(self):
        p=replace(self.pin,scope=replace(self.scope,environment='A0_REVIEW_ONLY'))
        with self.assertRaises(ValueError): self.append(observed=p,expected=p)
    def test_duplicate_team(self):
        with self.assertRaises(sqlite3.IntegrityError): self.store.create_team(self.rev,self.team)
    def test_stale_history(self):
        self.append()
        with self.assertRaises(ValueError): self.append()
        self.assertEqual(self.count('op_entry'),1)
    def test_duplicate_proposal(self):
        p=self.append()
        with self.assertRaises(sqlite3.IntegrityError): self.append(history_pin=p)
    def test_notice_rollback(self):
        with closing(sqlite3.connect(self.path)) as db, db: db.execute("CREATE TRIGGER test_fail BEFORE INSERT ON op_notice BEGIN SELECT RAISE(ABORT,'TEST'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.append()
        self.assertEqual(self.count('op_entry'),0); self.assertEqual(self.count('op_notice'),0)
    def test_concurrent(self):
        def run(_):
            try: return self.append().count
            except ValueError as e: return str(e)
        with ThreadPoolExecutor(max_workers=2) as ex: results=list(ex.map(run,range(2)))
        self.assertEqual(sorted(map(str,results)),['1','HISTORY_CAS'])
    def test_cross_scope_fk(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError): db.execute('INSERT INTO op_member VALUES (?,?,?,?,?,?)',('synthetic-other',self.scope.company,self.scope.environment,self.rev,self.team.project,'w'))
    def test_history_tamper(self):
        p=self.append()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DROP TRIGGER op_entry_update'); db.execute("UPDATE op_entry SET task='changed'")
        with self.assertRaises(ValueError): self.view(p)
    def test_notice_tamper(self):
        p=self.append()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DROP TRIGGER op_notice_update'); db.execute("UPDATE op_notice SET digest='bad'")
        with self.assertRaises(ValueError): self.view(p)
    def test_history_truncation(self):
        p=self.append()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute('DROP TRIGGER op_notice_delete'); db.execute('DROP TRIGGER op_entry_delete'); db.execute('DELETE FROM op_notice'); db.execute('DELETE FROM op_entry')
        with self.assertRaises(ValueError): self.view(p)
    def test_office_pin(self):
        with self.assertRaises(ValueError): self.view(self.empty,office_pin=replace(self.op,revision='b'*64))
    def test_office_environment(self):
        with self.assertRaises(ValueError): self.view(self.empty,office_pin=replace(self.op,scope=replace(self.scope,environment='A0_REVIEW_ONLY')))
    def test_api_read(self):
        session=ReadSession(self.scope,'demo-reader',100,'org.preview.read')
        status,body=studio_read(self.path,'opaque',lambda _:session,self.rev,99); self.assertEqual(status,200); self.assertFalse(body['authoritative']); self.assertNotIn('principal',str(body))
    def test_api_denied(self):
        s=ReadSession(self.scope,'demo-reader',100,'org.preview.read')
        for session in (None,replace(s,permission='write'),replace(s,expires=99),replace(s,scope=replace(self.scope,tenant='synthetic-other'))):
            with self.subTest(session=session): self.assertEqual(studio_read(self.path,'opaque',lambda _:session,self.rev,99)[0],403)
    def test_api_resolver_failure(self):
        def broken(_): raise RuntimeError('secret')
        status,body=studio_read(self.path,'opaque',broken,self.rev,99); self.assertEqual(status,403); self.assertNotIn('secret',str(body))

    def test_archived_history_read(self):
        p=self.append(); self.store.record(replace(self.s,previous=self.s.revision()),self.rev)
        self.assertEqual(self.store.history(self.rev,self.team.project,p)[0]['decision'],'HOLD')
        with self.assertRaises(ValueError): self.store.history(self.rev,self.team.project,self.empty)

    def test_combined_schema(self):
        import json
        from jsonschema import Draft202012Validator, ValidationError
        schema=json.loads(Path(__file__).with_name('combined.schema.json').read_text()); Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema); data=self.view(self.append()); validator.validate(data)
        for key,bad in (('authoritative',True),('decision','ALLOW'),('geometry_join','ALLOW'),('runtime_binding','demo-run'),('dispatch_allowed',True)):
            with self.subTest(key=key),self.assertRaises(ValidationError): validator.validate({**data,key:bad})
        with self.assertRaises(ValidationError): validator.validate({**data,'principal_id':'demo-principal'})
