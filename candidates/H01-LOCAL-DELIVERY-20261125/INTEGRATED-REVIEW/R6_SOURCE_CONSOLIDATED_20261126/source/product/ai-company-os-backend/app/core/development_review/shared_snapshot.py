"""Finite historical replay of one verified D0 prefix; never a live event stream."""
import hashlib
import json
from app.core.development_review.lifecycle_prefix_wire import prefix_wire

PROFILE = 'ceo-office.prefix.v1-D0'
MAX_BYTES = 16384


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def build_shared_replay(wire):
    if not isinstance(wire, dict) or canonical(wire) != canonical(prefix_wire(wire.get('head_version'))):
        raise ValueError('D0_SHARED_PREFIX_HOLD')
    snapshot = {'profile': PROFILE, 'source': 'D0_0196L_HISTORICAL_PREFIX',
                'project_id': None, 'world_id': None, 'snapshot_seq': wire['head_version'],
                'prefix': wire}
    digest = hashlib.sha256(canonical(snapshot).encode('ascii')).hexdigest()
    def frame(kind, payload):
        return 'event: '+kind+'\ndata: '+canonical(payload)+'\n\n'
    frames = [frame('snapshot', {**snapshot, 'digest': digest})]
    for item in wire['timeline']:
        frames.append(frame('history', {'digest': digest, 'sequence': item['version'], 'entry': item}))
    frames.append(frame('complete', {'digest': digest, 'sequence': wire['head_version']}))
    result = ''.join(frames)
    if len(result.encode('ascii')) > MAX_BYTES:
        raise ValueError('D0_SHARED_SIZE_HOLD')
    return result
