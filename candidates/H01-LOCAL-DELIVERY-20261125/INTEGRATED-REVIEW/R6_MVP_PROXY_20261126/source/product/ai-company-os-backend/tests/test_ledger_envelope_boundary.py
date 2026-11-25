"""D0 ledger JSON type boundary; no persistent or live authority."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest
from app.core.event_store import Event, Ledger, append_preview, replay_preview

SAMPLE = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/core.preview.json').read_text(encoding='utf-8'))
FLOORS = {f['id']: frozenset(s['id'] for s in f['stations']) for f in SAMPLE['layout']['floors']}


class LedgerEnvelopeBoundary(unittest.TestCase):
    def setUp(self):
        self.events = deepcopy(SAMPLE['events'])
        self.first = Event(**self.events[0])
        self.second = Event(**self.events[1])
        self.prefix = append_preview(Ledger(), self.first, FLOORS).ledger

    def test_non_string_event_id_rejected(self):
        for value in (1, True, ['event'], {'id': 'event'}, 1.5):
            with self.subTest(value=value):
                result = append_preview(Ledger(), replace(self.first, event_id=value), FLOORS)
                self.assertEqual((result.status, result.ledger.events, result.ledger.freshness), ('ENVELOPE_INVALID', (), 'RESYNC_REQUIRED'))

    def test_empty_event_id_rejected(self):
        for value in ('', None, 0, False):
            with self.subTest(value=value):
                self.assertEqual(append_preview(Ledger(), replace(self.first, event_id=value), FLOORS).status, 'ENVELOPE_INVALID')

    def test_unhashable_floor_id_rejected(self):
        for value in ([], {'floor': 'floor-1'}, ['floor-1']):
            with self.subTest(value=value):
                self.assertEqual(append_preview(self.prefix, replace(self.second, floor_id=value), FLOORS).status, 'PAYLOAD_INVALID')

    def test_unhashable_kind_rejected(self):
        for value in ([], {}, ['DEMO_STATION_SELECTED']):
            with self.subTest(value=value):
                self.assertEqual(append_preview(self.prefix, replace(self.second, kind=value), FLOORS).status, 'PAYLOAD_INVALID')

    def test_unhashable_station_id_rejected(self):
        for value in ([], {}, ['station-research']):
            with self.subTest(value=value):
                self.assertEqual(append_preview(self.prefix, replace(self.second, station_id=value), FLOORS).status, 'PAYLOAD_INVALID')

    def test_non_string_event_id_clears_selection(self):
        self.events[1]['event_id'] = ['invalid']
        result = replay_preview(self.events, SAMPLE['layout'])
        self.assertEqual(result['results'], ['SAMPLE_APPENDED', 'ENVELOPE_INVALID', 'SNAPSHOT_REQUIRED'])
        self.assertEqual((result['freshness'], result['last_seq'], result['selected_floor'], result['selected_station']), ('RESYNC_REQUIRED', 1, None, None))

    def test_invalid_payload_clears_selection(self):
        self.events[1]['station_id'] = []
        result = replay_preview(self.events, SAMPLE['layout'])
        self.assertEqual(result['results'], ['SAMPLE_APPENDED', 'PAYLOAD_INVALID', 'SNAPSHOT_REQUIRED'])
        self.assertEqual((result['freshness'], result['last_seq'], result['selected_floor'], result['selected_station']), ('RESYNC_REQUIRED', 1, None, None))

    def test_original_replay_unchanged(self):
        result = replay_preview(self.events, SAMPLE['layout'])
        self.assertEqual((result['freshness'], result['last_seq'], result['selected_floor'], result['selected_station']), ('SAMPLE', 3, 'floor-2', None))
        self.assertEqual(result['results'], ['SAMPLE_APPENDED'] * 3)
        self.assertFalse(result['persistent'] or result['verified'])
        self.assertEqual(self.events, SAMPLE['events'])

    def test_duplicate_and_conflict_preserved(self):
        duplicate = append_preview(self.prefix, self.first, FLOORS)
        self.assertEqual((duplicate.status, duplicate.ledger), ('DUPLICATE_IGNORED', self.prefix))
        conflict = append_preview(self.prefix, replace(self.first, floor_id='floor-2'), FLOORS)
        self.assertEqual((conflict.status, conflict.ledger.freshness), ('EVENT_ID_CONFLICT', 'RESYNC_REQUIRED'))

    def test_wrong_scope_and_boolean_seq_preserved(self):
        self.assertEqual(append_preview(Ledger(), replace(self.first, tenant_id='other'), FLOORS).status, 'SCOPE_OR_LAYOUT_MISMATCH')
        self.assertEqual(append_preview(Ledger(), replace(self.first, seq=True), FLOORS).status, 'ENVELOPE_INVALID')
