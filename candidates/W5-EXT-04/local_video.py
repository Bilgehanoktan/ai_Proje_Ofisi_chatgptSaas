"""EXT-04 isolated synthetic Y4M review. No runtime permission or external IO."""
from hashlib import sha256

WIDTH, HEIGHT, FPS, COUNT = 64, 48, 4, 8
MAX_BYTES, MAX_FRAMES = 32768, 8
HEADER = b'YUV4MPEG2 W64 H48 F4:1 Ip A1:1 Cmono\n'
MARKER = b'FRAME\n'
FIXTURE_ID = 'ext04-synthetic-01'


def fixture_bytes():
    """Eight deterministic monochrome frames, no audio or external data."""
    frames = []
    for i in range(COUNT):
        pixels = bytearray([32] * (WIDTH * HEIGHT))
        if i >= 2:
            left = 8 if i < 5 else 36
            for y in range(12, 28):
                pixels[y * WIDTH + left:y * WIDTH + left + 16] = bytes([224]) * 16
        frames.append(MARKER + pixels)
    return HEADER + b''.join(frames)


def _parse(raw):
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('INPUT_LIMIT')
    if not raw.startswith(HEADER):
        raise ValueError('FORMAT_HOLD')
    offset = len(HEADER)
    frames = []
    while offset < len(raw):
        if len(frames) >= MAX_FRAMES:
            raise ValueError('FRAME_LIMIT')
        if raw[offset:offset + len(MARKER)] != MARKER:
            raise ValueError('FRAME_MARKER')
        offset += len(MARKER)
        end = offset + WIDTH * HEIGHT
        if end > len(raw):
            raise ValueError('TRUNCATED_FRAME')
        frames.append(raw[offset:end])
        offset = end
    if len(frames) != COUNT:
        raise ValueError('FRAME_COUNT')
    return tuple(frames)


def _observe(frame, previous, index):
    bright = [i for i, v in enumerate(frame) if v >= 200]
    box = None
    if bright:
        xs, ys = [i % WIDTH for i in bright], [i // WIDTH for i in bright]
        box = [min(xs), min(ys), max(xs) + 1, max(ys) + 1]
    changed = None if previous is None else sum(a != b for a, b in zip(frame, previous))
    return {'frame_index': index, 'timestamp_ms': index * 1000 // FPS,
            'bright_pixels': len(bright), 'bright_box_xyxy_exclusive': box,
            'changed_pixels_from_previous': changed,
            'scene_candidate': changed is not None and changed >= 128,
            'pixel_sha256': sha256(frame).hexdigest()}


def review(raw, request):
    """Only the exact generated fixture; returns observations, not a grant."""
    if type(request) is not dict or set(request) != {'fixture_id', 'frame_indices'}:
        raise ValueError('REQUEST_SHAPE')
    if request['fixture_id'] != FIXTURE_ID:
        raise ValueError('FIXTURE_ID')
    indices = request['frame_indices']
    if (type(indices) is not list or not 1 <= len(indices) <= MAX_FRAMES
            or any(type(i) is not int or not 0 <= i < COUNT for i in indices)
            or indices != sorted(set(indices))):
        raise ValueError('FRAME_SELECTION')
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        raise ValueError('INPUT_LIMIT')
    if raw != fixture_bytes():
        raise ValueError('FIXTURE_BYTES_HOLD')
    frames = _parse(raw)
    observations = [_observe(frames[i], frames[i-1] if i else None, i) for i in indices]
    return {'status': 'SYNTHETIC_OBSERVATIONS_ONLY', 'decision': 'HOLD',
            'enabled': False, 'dispatch_allowed': False, 'provider_called': False,
            'tool_called': False, 'release_ready': False, 'independent_verified': False,
            'input_sha256': sha256(raw).hexdigest(), 'width': WIDTH, 'height': HEIGHT,
            'fps': FPS, 'duration_ms': COUNT * 1000 // FPS, 'frame_count': COUNT,
            'observations': observations, 'audio': 'NOT_SUPPORTED',
            'semantic_understanding': 'NOT_RUN', 'design_requirements': [],
            'design_review_cues': ['Compare timestamped bright-region geometry; human review required.']}


def frame_pgm(raw, index):
    """Return one bounded grayscale image as bytes, never write a path."""
    review(raw, {'fixture_id': FIXTURE_ID, 'frame_indices': [index]})
    return b'P5\n64 48\n255\n' + _parse(raw)[index]
