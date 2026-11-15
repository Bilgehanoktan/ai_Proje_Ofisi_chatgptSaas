"""Full-checkout regression: actual existing Workbench writer to new projection."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from app.core.development_review.sandbox_store import Workbench
from app.core.development_review.office_workbench import read_office_workbench, ORDER


class OfficeWorkbenchCLITests(TestCase):
    def test_writer_projection(self):
        fixture=Path(__file__).resolve().parents[1]/'fixtures/core.preview.json'
        plan=json.loads(fixture.read_text(encoding='utf-8'))['plan']
        with TemporaryDirectory() as directory:
            path=Path(directory)/'test.d0.sqlite'
            wb=Workbench(path,plan); wb.create()
            self.assertEqual(read_office_workbench(path)['sample_event_count'],0)
            for i,task in enumerate(ORDER,1):
                fence=wb.lease(task,'demo-holder',i,10)
                self.assertEqual(wb.observe(task,'demo-holder',fence,i,'demo-command-'+task),'SAMPLE_OBSERVED')
                x=read_office_workbench(path)
                self.assertEqual(x['sample_event_count'],i)
                self.assertEqual(x['geometry_join'],'HOLD')
                self.assertFalse(x['dispatch_allowed'])
            self.assertEqual([r['observed'] for r in x['roles']],[1,1,2,1])
