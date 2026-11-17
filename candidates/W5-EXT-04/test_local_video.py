import unittest
from hashlib import sha256
from local_video import (fixture_bytes, review, frame_pgm, _parse, HEADER,
                         MARKER, WIDTH, HEIGHT, FIXTURE_ID, MAX_BYTES)


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.raw = fixture_bytes()
        self.req = {'fixture_id': FIXTURE_ID, 'frame_indices': list(range(8))}

    def rejects(self, error, raw=None, request=None):
        with self.assertRaisesRegex(ValueError, '^' + error + '$'):
            review(self.raw if raw is None else raw, self.req if request is None else request)

    def test_metadata(self):
        r = review(self.raw, self.req)
        self.assertEqual((r['width'], r['height'], r['fps'], r['duration_ms'], r['frame_count']), (64, 48, 4, 2000, 8))
        self.assertEqual(r['input_sha256'], sha256(self.raw).hexdigest())

    def test_timestamps(self):
        self.assertEqual([x['timestamp_ms'] for x in review(self.raw, self.req)['observations']], list(range(0, 2000, 250)))

    def test_scene_candidates(self):
        o = review(self.raw, self.req)['observations']
        self.assertEqual([x['frame_index'] for x in o if x['scene_candidate']], [2, 5])
        self.assertEqual([o[2]['changed_pixels_from_previous'], o[5]['changed_pixels_from_previous']], [256, 512])

    def test_geometry(self):
        o = review(self.raw, self.req)['observations']
        self.assertIsNone(o[0]['bright_box_xyxy_exclusive'])
        self.assertEqual(o[2]['bright_box_xyxy_exclusive'], [8, 12, 24, 28])
        self.assertEqual(o[5]['bright_box_xyxy_exclusive'], [36, 12, 52, 28])

    def test_subset_previous_absolute(self):
        self.req['frame_indices'] = [5]
        self.assertEqual(review(self.raw, self.req)['observations'][0]['changed_pixels_from_previous'], 512)

    def test_no_authority(self):
        r = review(self.raw, self.req)
        for k in ('enabled', 'dispatch_allowed', 'provider_called', 'tool_called', 'release_ready', 'independent_verified'):
            self.assertIs(r[k], False)
        self.assertEqual(r['decision'], 'HOLD')
        self.assertEqual(r['design_requirements'], [])

    def test_frame_image(self):
        pgm = frame_pgm(self.raw, 2)
        self.assertEqual(pgm, b'P5\n64 48\n255\n' + _parse(self.raw)[2])
        self.assertEqual(len(pgm), 13 + WIDTH * HEIGHT)

    def test_deterministic(self):
        self.assertEqual(review(self.raw, self.req), review(fixture_bytes(), self.req))

    def test_url_path_key_options(self):
        for k in ('url', 'path', 'api_key', 'cookies', 'engine', 'whisper', 'out_dir', 'network'):
            with self.subTest(k=k):
                self.rejects('REQUEST_SHAPE', request={**self.req, k: 'untrusted'})

    def test_wrong_id(self):
        self.rejects('FIXTURE_ID', request={**self.req, 'fixture_id': 'other'})

    def test_bad_indices(self):
        for v in ([], [8], [-1], [True], [1.0], [2, 1], [1, 1], list(range(9)), '0'):
            with self.subTest(v=v):
                self.rejects('FRAME_SELECTION', request={**self.req, 'frame_indices': v})

    def test_wrong_input_type(self):
        self.rejects('INPUT_LIMIT', raw=bytearray(self.raw))

    def test_oversize(self):
        self.rejects('INPUT_LIMIT', raw=b'x' * (MAX_BYTES + 1))

    def test_modified_fixture(self):
        self.rejects('FIXTURE_BYTES_HOLD', raw=self.raw[:-1] + b'x')

    def test_parser_format(self):
        with self.assertRaisesRegex(ValueError, 'FORMAT_HOLD'):
            _parse(self.raw.replace(b'W64', b'W65', 1))

    def test_parser_marker(self):
        with self.assertRaisesRegex(ValueError, 'FRAME_MARKER'):
            _parse(self.raw.replace(MARKER, b'BROKE\n', 1))

    def test_parser_truncated(self):
        with self.assertRaisesRegex(ValueError, 'TRUNCATED_FRAME'):
            _parse(self.raw[:-1])

    def test_parser_count(self):
        with self.assertRaisesRegex(ValueError, 'FRAME_COUNT'):
            _parse(HEADER)

    def test_parser_frame_limit(self):
        with self.assertRaisesRegex(ValueError, 'FRAME_LIMIT'):
            _parse(self.raw + MARKER + b' ' * (WIDTH * HEIGHT))


if __name__ == '__main__':
    unittest.main()
