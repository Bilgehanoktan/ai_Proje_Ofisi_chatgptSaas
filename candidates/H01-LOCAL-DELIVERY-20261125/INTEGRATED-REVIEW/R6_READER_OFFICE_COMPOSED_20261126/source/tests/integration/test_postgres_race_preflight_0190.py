"""Offline helper checks only; never connects to PostgreSQL."""
import importlib.util
from pathlib import Path
from unittest import TestCase

spec=importlib.util.spec_from_file_location('race',Path(__file__).with_name('postgres_race_0190.py'))
race=importlib.util.module_from_spec(spec); spec.loader.exec_module(race)


class RacePreflight(TestCase):
    def test_write_is_cas_gated(self):
        for case in race.CASES:
            for side in ('a','b'):
                s=race.writer_sql(case,side)
                self.assertIn('AND version=0',s)
                self.assertLess(s.index('IF n=0 THEN RETURN'),s.index('INSERT INTO'))
                for name in ('event','audit','outbox'): self.assertIn('INSERT INTO aicos_d0_candidate.'+name,s)

    def test_readback_winner_and_exact_counts(self):
        for case,(aggregate,_,winner) in race.CASES.items():
            s=race.readback_sql(case,False)
            self.assertIn("e.command_id='"+aggregate+'-'+winner+"'",s)
            self.assertIn('JOIN aicos_d0_candidate.audit',s)
            self.assertIn('JOIN aicos_d0_candidate.outbox',s)
            self.assertIn("state='OBSERVED'",s)
            self.assertIn("state='PENDING'",race.readback_sql(case,True))

    def test_invalid_case_and_side(self):
        with self.assertRaises(KeyError): race.writer_sql('arbitrary','a')
        with self.assertRaises(ValueError): race.writer_sql('commit','x')

    def test_wait_timeout(self):
        with self.assertRaisesRegex(RuntimeError,'PG_RACE_TIMEOUT'):
            race.wait_for(lambda:False,'blocked',timeout=.01)
        race.wait_for(lambda:True,'ready')
