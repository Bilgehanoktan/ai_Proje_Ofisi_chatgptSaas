"""Actual local schema inventory and deterministic SQL candidate tests; no PG calls."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import re
import unittest
import pg_preflight as p


class PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = p.load()
        cls.sql, cls.inv = p.render(cls.sources)

    def test_exact_parent_pins(self):
        self.assertEqual(len(self.sources),2)

    def test_changed_reference_rejected(self):
        with TemporaryDirectory() as tmp:
            for name,src in zip(p.PINS,self.sources):
                (Path(tmp)/name).write_text(src+'\n',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'):
                p.load(tmp)

    def test_unpinned_render_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_PIN_HOLD'):
            p.render((self.sources[0]+'\n',self.sources[1]))

    def test_all_twelve_tables(self):
        self.assertEqual(set(self.inv),set(p.TABLES))
        self.assertEqual(len(self.inv),12)

    def test_every_pk_scope(self):
        for row in self.inv.values(): self.assertEqual(row['pk'][:3],['t','c','e'])

    def test_every_fk_scope(self):
        self.assertEqual(sum(len(r['foreign_keys']) for r in self.inv.values()),18)
        for row in self.inv.values():
            for fk in row['foreign_keys']:
                self.assertEqual(fk['from'][:3],fk['to'][:3])
                self.assertEqual(fk['from'][:3],['t','c','e'])

    def test_every_unique_scope(self):
        for row in self.inv.values():
            for key in row['unique']: self.assertEqual(key[:3],['t','c','e'])

    def test_cross_scope_fk_mutation_denied(self):
        bad=self.sources[0].replace('REFERENCES org_revision(t,c,e,rev)','REFERENCES org_revision(c,t,e,rev)',1)
        with self.assertRaisesRegex(ValueError,'FK_SCOPE_HOLD'):
            p.inventory((bad,self.sources[1]))

    def test_all_enable_force(self):
        self.assertEqual(self.sql.count(' ENABLE ROW LEVEL SECURITY;'),12)
        self.assertEqual(self.sql.count(' FORCE ROW LEVEL SECURITY;'),12)

    def test_policy_counts(self):
        self.assertEqual(self.sql.count('CREATE POLICY org_select'),12)
        self.assertEqual(self.sql.count('CREATE POLICY org_insert'),12)
        self.assertEqual(self.sql.count('CREATE POLICY org_update'),1)
        self.assertNotIn('FOR DELETE',self.sql)

    def test_scope_independent_axes(self):
        a,*others=p.WRITERS.values()
        self.assertEqual([sum(x!=y for x,y in zip(a,b)) for b in others],[1,1,1])

    def test_scope_uses_session_identity(self):
        for line in self.sql.splitlines():
            if line.startswith('CREATE POLICY'):
                self.assertIn('current_user = session_user',line)
                self.assertNotIn('current_setting',line)
                self.assertNotIn(p.UNMAPPED,line)
                self.assertNotIn(p.OWNER,line)

    def test_reader_has_no_write(self):
        for line in self.sql.splitlines():
            if 'GRANT INSERT' in line or 'GRANT UPDATE' in line or 'FOR INSERT' in line or 'FOR UPDATE' in line:
                self.assertNotIn(p.READER,line)

    def test_only_head_revision_update(self):
        grants=[s for s in self.sql.splitlines() if s.startswith('GRANT UPDATE')]
        self.assertEqual(len(grants),1)
        self.assertIn('UPDATE (rev) ON TABLE aicos_org_r4.org_head',grants[0])
        self.assertFalse(any(r['runtime_delete'] for r in self.inv.values()))

    def test_database_and_roles_fail_closed(self):
        self.assertIn('ORG_FIXTURE_DATABASE_HOLD',self.sql)
        self.assertIn('ORG_DATABASE_OWNER_HOLD',self.sql)
        self.assertIn('NOT rolcanlogin AND NOT rolsuper AND NOT rolbypassrls',self.sql)
        self.assertIn('ORG_ROLE_MEMBERSHIP_HOLD',self.sql)
        self.assertNotIn('CREATE ROLE',self.sql)
        self.assertNotIn('SECURITY DEFINER',self.sql)

    def test_no_sqlite_dialect_left(self):
        self.assertNotIn('PRAGMA',self.sql)
        self.assertNotIn('STRICT;',self.sql)
        self.assertIn('seq BIGINT',self.sql)
        self.assertEqual(self.sql.count('DEFERRABLE INITIALLY DEFERRED'),2)
        self.assertEqual(self.sql.count('REFERENCES aicos_org_r4.'),18)

    def test_determinism(self):
        self.assertEqual(p.render(self.sources),(self.sql,self.inv))

    def test_fresh_output_and_hold(self):
        with TemporaryDirectory() as tmp:
            out=Path(tmp)/'new'
            report=p.generate(out)
            self.assertEqual(json.loads((out/'PREFLIGHT_REPORT.json').read_text()),json.loads(json.dumps(report)))
            self.assertEqual(report['pg'],'NOT_RUN')
            self.assertFalse(report['dispatch_allowed'])
            with self.assertRaises(FileExistsError): p.generate(out)


if __name__=='__main__': unittest.main()
