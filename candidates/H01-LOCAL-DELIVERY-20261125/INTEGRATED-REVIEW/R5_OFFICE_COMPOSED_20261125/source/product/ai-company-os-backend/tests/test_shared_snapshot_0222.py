import hashlib
import json
import unittest
from app.core.development_review.lifecycle_prefix_wire import prefix_wire
from app.core.development_review.shared_snapshot import build_shared_replay, canonical


class SharedReplayTests(unittest.TestCase):
    def test_all_prefixes(self):
        for version in range(1, 5):
            with self.subTest(version=version):
                wire = prefix_wire(version)
                frames = build_shared_replay(wire).strip().split('\n\n')
                rows = [json.loads(f.split('\ndata: ')[1]) for f in frames]
                snap = rows[0]
                digest = snap.pop('digest')
                self.assertEqual(hashlib.sha256(canonical(snap).encode('ascii')).hexdigest(), digest)
                self.assertIsNone(snap['project_id'])
                self.assertIsNone(snap['world_id'])
                self.assertEqual(snap['snapshot_seq'], version)
                self.assertEqual(rows[1:-1], [{'digest': digest, 'sequence': i, 'entry': e}
                    for i, e in enumerate(wire['timeline'], 1)])
                self.assertEqual(rows[-1], {'digest': digest, 'sequence': version})
                self.assertFalse(snap['prefix']['authoritative'])

    def test_tampered_scope(self):
        for key, value in [('tenant','other'), ('policy_epoch',3), ('agent_instance_id','other'), ('dispatch_allowed',True)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                build_shared_replay({**prefix_wire(2), key: value})

    def test_tampered_timeline(self):
        wire = prefix_wire(4)
        wire['timeline'][1]['version'] = 3
        with self.assertRaises(ValueError):
            build_shared_replay(wire)

    def test_unproven_project(self):
        with self.assertRaises(ValueError):
            build_shared_replay({**prefix_wire(2), 'project_id':'p'})

    def test_invalid_version(self):
        for version in [0, 5, True, '2', None]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                build_shared_replay({'head_version':version})

    def test_deterministic(self):
        self.assertEqual(build_shared_replay(prefix_wire(4)), build_shared_replay(prefix_wire(4)))
