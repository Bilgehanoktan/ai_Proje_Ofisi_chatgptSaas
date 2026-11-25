"""Read-only R11 dependency preflight. Never installs/imports/runs product code."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import sys

REQ = 'product/ai-company-os-backend/requirements.txt'
PKG = 'product/ai-company-os-frontend/package.json'
PINS = {REQ: (105, '25295154f2f3db91ea65c2a9e1f7558925e723ef9847b805fdbe77a3fb44c4cd'),
        PKG: (448, 'e81b9fd3f07d30737e30ebfe0fd5573a6e86d0ebf2c67ae148677590cd460c0c')}
NAME = re.compile(r'(?:@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*\Z')
VER = re.compile(r'[0-9]+\.[0-9]+\.[0-9]+\Z')
MAX_BYTES = 8 * 1024 * 1024


def unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('DUPLICATE_JSON_KEY')
        out[key] = value
    return out


def read_safe(root: Path, relative: str) -> bytes:
    parts = relative.split('/')
    if any(not x or x in ('.', '..') or '\\' in x or ':' in x for x in parts):
        raise ValueError('UNSAFE_PATH')
    p = root
    if p.is_symlink():
        raise ValueError('SYMLINK_ROOT')
    for part in parts:
        p = p / part
        if p.is_symlink() or getattr(p, 'is_junction', lambda: False)():
            raise ValueError('LINK_OR_JUNCTION')
    if not p.is_file():
        raise FileNotFoundError(relative)
    with p.open('rb') as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('FILE_LIMIT')
    return raw


def parse_requirements(raw):
    result = {}
    for line in raw.decode('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9._-]*)==([0-9]+\.[0-9]+\.[0-9]+)', line)
        if not match:
            raise ValueError('PYTHON_PIN_FORMAT')
        name, version = match.groups()
        name = re.sub(r'[-_.]+', '-', name).lower()
        if name in result:
            raise ValueError('DUPLICATE_PYTHON_PIN')
        result[name] = version
    if not result:
        raise ValueError('EMPTY_REQUIREMENTS')
    return result


def parse_package(raw):
    obj = json.loads(raw, object_pairs_hook=unique)
    result = {}
    for group in ('dependencies', 'devDependencies'):
        values = obj.get(group, {})
        if not isinstance(values, dict):
            raise ValueError('NPM_PIN_FORMAT')
        for name, version in values.items():
            if not NAME.fullmatch(name) or not isinstance(version, str) or not VER.fullmatch(version):
                raise ValueError('NPM_PIN_FORMAT')
            if name in result:
                raise ValueError('DUPLICATE_NPM_PIN')
            result[name] = version
    if not result:
        raise ValueError('EMPTY_PACKAGE_PINS')
    return result


def installed_python(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def installed_node(root, name):
    try:
        obj = json.loads(read_safe(root, 'product/ai-company-os-frontend/node_modules/'+name+'/package.json'), object_pairs_hook=unique)
        if obj.get('name') != name or not isinstance(obj.get('version'), str):
            raise ValueError('NPM_INSTALLED_METADATA_INVALID')
        return obj['version']
    except FileNotFoundError:
        return None


def rows(pins, get_version):
    out = []
    for name, expected in pins.items():
        actual = get_version(name)
        out.append({'name': name, 'expected': expected, 'observed': actual,
                    'status': 'MATCH' if actual == expected else 'MISSING' if actual is None else 'MISMATCH'})
    return out


def optional_lock(root, relative):
    try:
        raw = read_safe(root, relative)
        return {'status': 'PRESENT_UNREVIEWED', 'sha256': hashlib.sha256(raw).hexdigest()}
    except FileNotFoundError:
        return {'status': 'ABSENT'}


def audit(root, pins=PINS, python_lookup=installed_python):
    sources = {}
    for name, (size, expected) in pins.items():
        raw = read_safe(root, name)
        if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('SPEC_PIN_MISMATCH: '+name)
        sources[name] = raw
    py = rows(parse_requirements(sources[REQ]), python_lookup)
    js = rows(parse_package(sources[PKG]), lambda name: installed_node(root, name))
    return {'source_spec_check': 'MATCH', 'source_scope': 'TWO_DEPENDENCY_SPEC_FILES_ONLY',
            'python_version': sys.version.split()[0], 'python_candidate_minor': sys.version_info[:2] in ((3,11),(3,12)),
            'node_on_path': shutil.which('node') is not None, 'npm_on_path': shutil.which('npm') is not None,
            'python_direct': py, 'node_direct': js,
            'python_lock': optional_lock(root, 'product/ai-company-os-backend/requirements.lock.txt'),
            'node_lock': optional_lock(root, 'product/ai-company-os-frontend/package-lock.json'),
            'full_transitive_lock_review': 'NOT_EVALUATED', 'authority': 'NOT_EVALUATED',
            'product_execution': 'NOT_RUN', 'installation': 'NOT_RUN', 'readiness': 'HOLD'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True, type=Path)
    args = p.parse_args()
    try:
        print(json.dumps(audit(args.root.absolute()), indent=2))
        return 0  # Successfully collected inventory; NOT runtime readiness.
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as exc:
        print(json.dumps({'source_spec_check':'HOLD','reason':str(exc),'installation':'NOT_RUN','product_execution':'NOT_RUN','readiness':'HOLD'}, indent=2))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
