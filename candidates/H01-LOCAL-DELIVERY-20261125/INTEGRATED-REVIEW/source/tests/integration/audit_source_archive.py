"""Read-only exact product archive audit. Never extracts, installs or executes content."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import zipfile

HEX40 = re.compile(r'[0-9a-f]{40}\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
MAX_MEMBER = 64 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or p.as_posix() != name or '\\' in name or ':' in name or '..' in p.parts:
        raise ValueError('UNSAFE_PATH: ' + name)
    return name


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('DUPLICATE_JSON_KEY: ' + key)
        result[key] = value
    return result


def audit(archive, manifest_blob, expected_count):
    if not HEX40.fullmatch(manifest_blob) or type(expected_count) is not int or expected_count <= 0:
        raise ValueError('INVALID_EXPECTED_PIN')
    with zipfile.ZipFile(archive) as z:
        members = {}
        folded = set()
        total = 0
        for info in z.infolist():
            name = safe_name(info.filename.rstrip('/') if info.is_dir() else info.filename)
            if name.casefold() in folded:
                raise ValueError('DUPLICATE_OR_CASE_ALIAS: ' + name)
            folded.add(name.casefold())
            kind = (info.external_attr >> 16) & 0o170000
            if kind not in ((0, stat.S_IFDIR) if info.is_dir() else (0, stat.S_IFREG)):
                raise ValueError('NONREGULAR_MEMBER: ' + name)
            if info.is_dir():
                continue
            if info.file_size > MAX_MEMBER:
                raise ValueError('MEMBER_SIZE_HOLD: ' + name)
            total += info.file_size
            if total > MAX_TOTAL:
                raise ValueError('ARCHIVE_SIZE_HOLD')
            members[name] = info
        candidates = [n for n in members if n == 'product/SOURCE_MANIFEST.json' or (len(PurePosixPath(n).parts) == 3 and n.endswith('/product/SOURCE_MANIFEST.json'))]
        if len(candidates) != 1:
            raise ValueError('FULL_PRODUCT_MANIFEST_MISSING_OR_AMBIGUOUS')
        manifest_name = candidates[0]
        prefix = manifest_name[:-len('SOURCE_MANIFEST.json')]
        raw = z.read(members[manifest_name])
        if blob(raw) != manifest_blob:
            raise ValueError('MANIFEST_BLOB_MISMATCH')
        manifest = json.loads(raw, object_pairs_hook=unique_object)
        files = manifest['files']
        if not isinstance(files, dict) or len(files) != expected_count:
            raise ValueError('MANIFEST_COUNT_MISMATCH')
        for name, pin in files.items():
            safe_name(name)
            if name == 'SOURCE_MANIFEST.json' or not isinstance(pin, dict) or type(pin.get('bytes')) is not int or not 0 <= pin['bytes'] <= MAX_MEMBER or not isinstance(pin.get('sha256'), str) or not HEX64.fullmatch(pin['sha256']):
                raise ValueError('INVALID_FILE_PIN: ' + name)
        actual = {n[len(prefix):] for n in members if n.startswith(prefix) and n != manifest_name}
        missing = sorted(set(files) - actual)
        extra = sorted(actual - set(files))
        mismatch = []
        for name in sorted(set(files) & actual):
            info = members[prefix+name]
            if info.file_size != files[name]['bytes'] or hashlib.sha256(z.read(info)).hexdigest() != files[name]['sha256']:
                mismatch.append(name)
        exact = expected_count - len(missing) - len(mismatch)
        return {'status':'SOURCE_MATCH_NOT_ACCEPTANCE' if not (missing or extra or mismatch) else 'HOLD', 'manifest_blob':manifest_blob, 'expected':expected_count, 'exact':exact, 'missing':missing, 'extra':extra, 'mismatch':mismatch, 'scope':'Product bytes only; W8 auxiliary, dependency and runtime gates separate'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--manifest-blob', required=True)
    p.add_argument('--expected-count', type=int, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    try:
        result = audit(args.archive, args.manifest_blob, args.expected_count)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, RuntimeError) as exc:
        result = {'status':'HOLD','reason':str(exc),'expected':args.expected_count,'exact':None}
    with args.report.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(result['status'])
    return 0 if result['status'] == 'SOURCE_MATCH_NOT_ACCEPTANCE' else 1


if __name__ == '__main__':
    sys.exit(main())
