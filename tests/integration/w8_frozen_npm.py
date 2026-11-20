"""Fail-closed, immutable npm lock injection for the existing W8 U3 prepare path.

No npm install is executed during lock preparation. Wheel downloads remain the
responsibility of the existing, unchanged W8 prepare implementation.
"""
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

LOCK_PATH = 'tests/integration/locks/mi01-frozen-npm/package-lock.json'
LOCK_BLOB = '4cd33f437df85d7e74c7946a0999f76adf2e31fe'
LOCK_SHA256 = '036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88'
LOCK_BYTES = 33618
PACKAGE_BLOB = '55a6d296ee20daad2cd36f4552f9feb3f4440ba3'
PACKAGE_COUNT = 61
NPM_PREPARE_ARGS = ('install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org')


def _blob_bytes(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def verify_frozen_npm_inputs(repo, frontend, lock_path=LOCK_PATH,
                             lock_blob=None, lock_sha256=None,
                             lock_bytes=None, package_blob=None,
                             package_count=None):
    """Return exact bytes only after validating source, provenance and pin graph.

    The optional expected values are dependency-injection seams for synthetic tests,
    not runtime CLI overrides; the adapter always invokes production constants.
    """
    lock_blob = LOCK_BLOB if lock_blob is None else lock_blob
    lock_sha256 = LOCK_SHA256 if lock_sha256 is None else lock_sha256
    lock_bytes = LOCK_BYTES if lock_bytes is None else lock_bytes
    package_blob = PACKAGE_BLOB if package_blob is None else package_blob
    package_count = PACKAGE_COUNT if package_count is None else package_count
    source = repo / lock_path
    package = frontend / 'package.json'
    if (source.is_symlink() or package.is_symlink()
            or not source.is_file() or not package.is_file()):
        raise ValueError('W8_IMMUTABLE_NPM_INPUT_MISSING_OR_SYMLINK')
    raw = source.read_bytes()
    package_raw = package.read_bytes()
    if (len(raw) != lock_bytes or _blob_bytes(raw) != lock_blob
            or hashlib.sha256(raw).hexdigest() != lock_sha256):
        raise ValueError('W8_IMMUTABLE_NPM_LOCK_PIN_HOLD')
    if _blob_bytes(package_raw) != package_blob:
        raise ValueError('W8_IMMUTABLE_NPM_PACKAGE_PIN_HOLD')
    try:
        lock = json.loads(raw)
        pkg = json.loads(package_raw)
        packages = lock['packages']
        root = packages['']
        if (lock['lockfileVersion'] != 3 or lock['name'] != pkg['name']
                or lock['version'] != pkg['version']
                or len(packages) - 1 != package_count):
            raise ValueError('W8_IMMUTABLE_NPM_GRAPH_HOLD')
        for k in ('dependencies','devDependencies'):
            if root.get(k) != pkg.get(k):
                raise ValueError('W8_IMMUTABLE_NPM_DIRECT_PIN_HOLD')
        for name, pin in pkg.get('overrides', {}).items():
            versions = [v['version'] for k, v in packages.items()
                        if k.endswith('node_modules/' + name)]
            if not versions or any(version != pin for version in versions):
                raise ValueError('W8_IMMUTABLE_NPM_OVERRIDE_HOLD')
        for name, info in packages.items():
            if not name:
                continue
            url = urlparse(info['resolved'])
            if (url.scheme != 'https' or url.hostname != 'registry.npmjs.org'
                    or info.get('integrity', '').split('-',1)[0] not in ('sha256','sha512')):
                raise ValueError('W8_IMMUTABLE_NPM_PROVENANCE_HOLD')
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('W8_IMMUTABLE_NPM_GRAPH_HOLD') from exc
    return raw


class FrozenNpmPrepareHook:
    """Replace only the exact old npm lock-generation call with pinned bytes."""

    def __init__(self, original_run, npm_binary, frontend, raw):
        self.original_run = original_run
        self.frontend = Path(frontend)
        self.raw = raw
        self.expected = (str(npm_binary), *NPM_PREPARE_ARGS)
        self.count = 0

    def __call__(self, args, cwd, env=None):
        arguments = tuple(map(str, args))
        # Any unexpected package-lock generation invocation fails closed.
        if '--package-lock-only' in arguments:
            if (arguments != self.expected or Path(cwd) != self.frontend
                    or self.count != 0):
                raise ValueError('W8_IMMUTABLE_NPM_CALL_HOLD')
            destination = self.frontend / 'package-lock.json'
            if destination.exists() or destination.is_symlink():
                raise ValueError('W8_IMMUTABLE_NPM_OVERWRITE_HOLD')
            destination.write_bytes(self.raw)
            self.count += 1
            return None
        return self.original_run(args, cwd, env)


def install_into_w8(w):
    """Decorate current U3 adapter without touching pinned W8 ancestor modules."""
    original_prepare = w.prepare

    def prepare(repo, stage):
        # Preflight before allocating the original stage or invoking package managers.
        raw = verify_frozen_npm_inputs(repo, w.frontend(repo))
        original_run = w.run
        hook = FrozenNpmPrepareHook(original_run, w.npm(), w.frontend(stage), raw)
        w.run = hook
        try:
            result = original_prepare(repo, stage)
            dest = w.frontend(stage) / 'package-lock.json'
            if hook.count != 1 or not dest.is_file() or dest.read_bytes() != raw:
                raise ValueError('W8_IMMUTABLE_NPM_PREPARE_INCOMPLETE')
            return result
        except Exception:
            # No false approval marker if any step fails (including pip download).
            (stage / 'locks' / 'REVIEW.json').unlink(missing_ok=True)
            raise
        finally:
            w.run = original_run
    w.prepare = prepare
    return w
