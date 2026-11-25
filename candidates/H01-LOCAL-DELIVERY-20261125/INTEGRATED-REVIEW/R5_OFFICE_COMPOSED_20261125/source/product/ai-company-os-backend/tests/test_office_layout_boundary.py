"""Exact D0 fixture, geometry validation only; no live placement."""
from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from app.core.office import validate_layout
from app.engines.office_engine import layout as engine

BASE = json.loads((Path(__file__).resolve().parents[1] / 'fixtures/core.preview.json').read_text(encoding='utf-8'))['layout']


class OfficeLayoutBoundaryTests(TestCase):
    def setUp(self):
        self.layout = deepcopy(BASE)
        self.floor = self.layout['floors'][0]

    def test_original_two_floor_fixture(self):
        self.assertIsNone(validate_layout(self.layout))
        self.assertEqual(self.layout, BASE)
        self.assertIs(validate_layout, engine.validate_layout)

    def test_room_out_of_bounds_before_allocation(self):
        self.floor['rooms'][0]['w'] = 10**12
        with patch.object(engine, 'range', side_effect=AssertionError('range called before bounds check'), create=True):
            with self.assertRaisesRegex(ValueError, '^ROOM_OVERLAP_OR_BOUNDS$'):
                validate_layout(self.layout)

    def test_negative_origin_before_allocation(self):
        self.floor['rooms'][0]['x'] = -1
        with patch.object(engine, 'range', side_effect=AssertionError('range called before bounds check'), create=True):
            with self.assertRaisesRegex(ValueError, '^ROOM_OVERLAP_OR_BOUNDS$'):
                validate_layout(self.layout)

    def test_grid_dimensions_exact_int(self):
        self.layout['width'] = 6.0
        with self.assertRaisesRegex(ValueError, '^LAYOUT_SCOPE_INVALID$'):
            validate_layout(self.layout)

    def test_room_bool_and_float_rejected(self):
        for v in (True, 0.0, '0', None):
            with self.subTest(v=v):
                self.floor['rooms'][0]['x'] = v
                with self.assertRaisesRegex(ValueError, '^ROOM_INVALID$'):
                    validate_layout(self.layout)

    def test_station_non_integer_position(self):
        for v in (False, 0.0, '0', None):
            with self.subTest(v=v):
                self.floor['stations'][0]['x'] = v
                with self.assertRaisesRegex(ValueError, '^STATION_INVALID$'):
                    validate_layout(self.layout)

    def test_walkable_non_integer_or_malformed(self):
        for v in ([0.0, 1], [False, 1], [[], 1], None, [0]):
            with self.subTest(v=v):
                self.floor['walkable'][0] = v
                with self.assertRaisesRegex(ValueError, '^WALKABLE_INVALID$'):
                    validate_layout(self.layout)

    def test_missing_room_field(self):
        del self.floor['rooms'][0]['x']
        with self.assertRaisesRegex(ValueError, '^ROOM_INVALID$'):
            validate_layout(self.layout)

    def test_missing_station_agent_binding(self):
        del self.floor['stations'][0]['agent_instance_id']
        with self.assertRaisesRegex(ValueError, '^STATION_INVALID$'):
            validate_layout(self.layout)

    def test_malformed_floor_collection(self):
        self.layout['floors'] = None
        with self.assertRaisesRegex(ValueError, '^LAYOUT_SCOPE_INVALID$'):
            validate_layout(self.layout)

    def test_existing_overlap_guard(self):
        self.floor['rooms'][1]['x'] = 1
        with self.assertRaisesRegex(ValueError, '^ROOM_OVERLAP_OR_BOUNDS$'):
            validate_layout(self.layout)

    def test_existing_duplicate_floor_guard(self):
        self.layout['floors'][1]['id'] = self.floor['id']
        with self.assertRaisesRegex(ValueError, '^FLOOR_DUPLICATE$'):
            validate_layout(self.layout)

    def test_existing_live_binding_guard(self):
        self.floor['stations'][0]['agent_instance_id'] = 'synthetic-agent'
        with self.assertRaisesRegex(ValueError, '^STATION_INVALID$'):
            validate_layout(self.layout)

    def test_existing_duplicate_walkable_guard(self):
        self.floor['walkable'].append(self.floor['walkable'][0])
        with self.assertRaisesRegex(ValueError, '^WALKABLE_INVALID$'):
            validate_layout(self.layout)
