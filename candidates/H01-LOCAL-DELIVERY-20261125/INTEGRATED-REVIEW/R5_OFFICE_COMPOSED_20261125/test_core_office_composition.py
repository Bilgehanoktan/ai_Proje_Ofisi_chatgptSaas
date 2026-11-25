"""D0 review-only cross-module checks. Calls exact product functions, not HTTP."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from app.core.office import validate_layout
from app.core.orchestrator.engine import canonical_plan, preview_plan
from app.core.event_store.ledger import replay_preview

SAMPLE=json.loads(Path('fixtures/core.preview.json').read_text(encoding='utf-8'))
EXPECTED=json.loads(Path('fixtures/core.plan.projection.json').read_text(encoding='utf-8'))

def compose(sample):
    # Same function sequence as core_preview in exact PR47 demo.py; no API import.
    validate_layout(sample['layout'])
    return preview_plan(sample['plan']), replay_preview(sample['events'],sample['layout'])

class CoreOfficeComposition(unittest.TestCase):
    def setUp(self):
        self.sample=deepcopy(SAMPLE)
    def test_exact_original_projection_and_replay(self):
        plan, event=compose(self.sample)
        self.assertEqual(canonical_plan(self.sample['plan']),EXPECTED)
        self.assertEqual(plan['waves'],EXPECTED['waves'])
        self.assertEqual((event['freshness'],event['last_seq'],event['selected_floor'],event['selected_station']),('SAMPLE',3,'floor-2',None))
        self.assertEqual(event['results'],['SAMPLE_APPENDED']*3)
        self.assertEqual(self.sample,SAMPLE)
    def test_no_dispatch_release_persistence(self):
        plan,event=compose(self.sample)
        self.assertEqual(plan['admission'],'DENY')
        self.assertFalse(plan['dispatch_allowed'] or plan['release_ready'] or event['persistent'] or event['verified'])
        self.assertTrue(all(t['run_id'] is None and t['state']=='HOLD' for t in plan['tasks']))
    def test_gap_clears_selection(self):
        self.sample['events'].pop(1)
        _,event=compose(self.sample)
        self.assertEqual(event['freshness'],'RESYNC_REQUIRED')
        self.assertEqual((event['selected_floor'],event['selected_station']),(None,None))
        self.assertIn('SEQUENCE_GAP_OR_OLD',event['results'])
    def test_wrong_tenant_clears_selection(self):
        self.sample['events'][1]['tenant_id']='other'
        _,event=compose(self.sample)
        self.assertEqual(event['freshness'],'RESYNC_REQUIRED')
        self.assertEqual((event['selected_floor'],event['selected_station']),(None,None))
        self.assertIn('SCOPE_OR_LAYOUT_MISMATCH',event['results'])
    def test_invalid_station_clears_selection(self):
        self.sample['events'][1]['station_id']='station-not-present'
        _,event=compose(self.sample)
        self.assertEqual(event['freshness'],'RESYNC_REQUIRED')
        self.assertEqual((event['selected_floor'],event['selected_station']),(None,None))
        self.assertIn('PAYLOAD_INVALID',event['results'])
    def test_malformed_layout_blocks_composition(self):
        self.sample['layout']['floors'][0]['rooms'][0]['w']=10**12
        with self.assertRaisesRegex(ValueError,'^ROOM_OVERLAP_OR_BOUNDS$'):
            compose(self.sample)
    def test_duplicate_event_no_extra_selection(self):
        self.sample['events'].insert(2,deepcopy(self.sample['events'][1]))
        _,event=compose(self.sample)
        self.assertEqual((event['freshness'],event['last_seq'],event['selected_floor']),('SAMPLE',3,'floor-2'))
        self.assertIn('DUPLICATE_IGNORED',event['results'])
