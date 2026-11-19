"""D5-G8: owner DDL boundary diagnostics, not actual assignment or PG tests.

Use exact R3 SQLite DDL; direct synthetic fixture seeds, not OperationsStore.
Run from this file's directory or with original repository root as argument.
"""
from contextlib import closing
from hashlib import sha1
from pathlib import Path
import sqlite3
import sys
import unittest

HERE = Path(__file__).resolve().parent
ROOT = Path(sys.argv.pop(1)).resolve() if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None
DDL = ROOT / 'candidates/ORG-05R3' if ROOT else HERE / 'owner_sources'
PINS = {'schema.sql': '32b7609b18e8a53420f17d23f4b53544e7f6f6ad',
        'operations.sql': '3443f6581eb3a8d3894aea0b620f2b8d6dba9b2a'}
for name, expected in PINS.items():
    raw = (DDL / name).read_bytes()
    if sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest() != expected:
        raise RuntimeError('D5G8_OWNER_DDL_PIN_HOLD')

SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
K = (*SCOPE, 'a'*64)
PROJECT = 'demo-project'
PLAN = 'sha256:'+'b'*64
TASK = 'research'


class AssignmentGapTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        for name in PINS:
            self.db.executescript((DDL / name).read_text(encoding='utf-8'))
        self.assertEqual(self.db.execute('PRAGMA foreign_keys').fetchone(), (1,))
        self.db.execute('INSERT INTO org_revision VALUES (?,?,?,?,?,?,?,?)', (*K,1,None,'c'*64,None))
        self.db.execute('INSERT INTO org_head VALUES (?,?,?,?)', K)
        self.db.execute('INSERT INTO org_unit VALUES (?,?,?,?,?,?,?)', (*K,'root','company',None))
        for seat, role in (('lead','orchestrator'),('worker-a','research'),('worker-b','research')):
            self.db.execute('INSERT INTO org_position VALUES (?,?,?,?,?,?,?,?)', (*K,seat,'root',role,None if seat=='lead' else 'lead'))
            self.db.execute('INSERT INTO org_definition_ref VALUES (?,?,?,?,?,?)', (*K,'def-'+seat,role))
            self.db.execute('INSERT INTO org_instance_ref VALUES (?,?,?,?,?,?,?)', (*K,'demo-agent-'+seat,'def-'+seat,role))
            self.db.execute('INSERT INTO org_binding VALUES (?,?,?,?,?,?,?)', (*K,seat,'demo-agent-'+seat,role))
        self.db.execute('INSERT INTO op_team VALUES (?,?,?,?,?,?,?)', (*K,PROJECT,'lead','d'*64))
        for seat in ('lead','worker-a','worker-b'):
            self.db.execute('INSERT INTO op_member VALUES (?,?,?,?,?,?)', (*K,PROJECT,seat))
        self.db.commit()

    def columns(self, table):
        return tuple(r[1] for r in self.db.execute('PRAGMA table_info('+table+')'))

    def proposal(self, seq, recipient, role='research'):
        self.db.execute('INSERT INTO op_entry VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (*K,PROJECT,seq,PLAN,TASK,'lead',recipient,'delegation',role,'0'*64,str(seq)*64))
        self.db.execute('INSERT INTO op_notice VALUES (?,?,?,?,?,?,?,?)', (*K,PROJECT,seq,'e'*64,'HOLD'))

    def test_exact_twelve_tables_no_assignment_or_role_registry(self):
        actual = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(actual, {'org_revision','org_head','org_unit','org_position',
            'org_definition_ref','org_instance_ref','org_binding','org_notice',
            'op_team','op_member','op_entry','op_notice'})

    def test_proposal_schema_does_not_retain_principal_run_or_role_revision(self):
        self.assertEqual(self.columns('op_entry'), ('t','c','e','rev','project','seq','plan','task',
            'sender','recipient','kind','role','previous','digest'))
        self.assertTrue({'principal','run','role_revision','assignment_revision','assignment_digest',
            'registry_revision','expires_tick','issuer'}.isdisjoint(self.columns('op_entry')))

    def test_staffing_occupancy_is_not_task_assignment(self):
        self.assertEqual(self.columns('org_binding'), ('t','c','e','rev','seat','instance','role'))
        self.assertEqual(self.db.execute('SELECT count(*) FROM org_binding').fetchone(),(3,))
        self.assertEqual(self.db.execute('SELECT count(*) FROM op_entry').fetchone(),(0,))

    def test_multiple_proposals_for_same_task_are_valid_schema_rows(self):
        self.proposal(1,'worker-a'); self.proposal(2,'worker-b'); self.db.commit()
        rows = self.db.execute('SELECT task,recipient FROM op_entry ORDER BY seq').fetchall()
        self.assertEqual(rows, [(TASK,'worker-a'),(TASK,'worker-b')])
        self.assertEqual(self.db.execute('SELECT DISTINCT state FROM op_notice').fetchall(), [('HOLD',)])

    def test_same_proposal_duplicate_is_rejected(self):
        self.proposal(1,'worker-a')
        with self.assertRaises(sqlite3.IntegrityError): self.proposal(2,'worker-a')

    def test_wrong_recipient_role_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError): self.proposal(1,'worker-a','qa')

    def test_proposal_cannot_be_promoted_by_notice_state(self):
        self.proposal(1,'worker-a')
        with self.assertRaises(sqlite3.IntegrityError): self.db.execute("UPDATE op_notice SET state='ACTIVE'")
        self.assertEqual(self.db.execute('SELECT state FROM op_notice').fetchall(), [('HOLD',)])


if __name__ == '__main__':
    print('D5G8_OWNER_DDL_PINS: 2/2', flush=True)
    print('PYTHON:', sys.version.split()[0], 'SQLITE:', sqlite3.sqlite_version, flush=True)
    unittest.main(verbosity=2)
