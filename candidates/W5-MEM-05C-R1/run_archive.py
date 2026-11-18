"""MEM-05C-R1: verify 149 original source blobs and run only the original ten diagnostics.
No Git, download, install, product mutation, provider or real execution permission.
"""
from hashlib import sha1, sha256
from pathlib import Path, PurePosixPath
import json
import os
import re
import subprocess
import sys
import tempfile

MEMORY = '56e3dde18d2f80f4f502cdbba3a8f47a91049168'
GATEWAY = '12d5149ef891b69a909162f8eecfe5847858e8b4'
PINS_BLOB = '913f79a26cfef06f1afc78b3835829f6b37875c6'
TEST_BLOB = 'c0ded1c2f351a2a538cd3e710de0f2d7ff7e6616'
ORIGINAL = 'candidates/W5-MEM-05C'
OVERLAY = 'candidates/W5-MEM-05C-R1/overlay'
BACKEND = 'product/ai-company-os-backend'
HEX = re.compile(r'[0-9a-f]{40}\Z')


def git_blob(raw):
    return sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def checked_path(root, relative):
    if type(relative) is not str or not relative or '\\' in relative or ':' in relative:
        raise ValueError('UNSAFE_PATH')
    parts = PurePosixPath(relative).parts
    if not parts or relative.startswith('/') or any(p in ('.','..') for p in parts) or '/'.join(parts) != relative:
        raise ValueError('UNSAFE_PATH')
    path = root.joinpath(*parts)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('UNSAFE_PATH')
    return path


def read_pinned(root, path, expected):
    if type(expected) is not str or HEX.fullmatch(expected) is None:
        raise ValueError('BAD_BLOB_PIN')
    raw = checked_path(root,path).read_bytes()
    if git_blob(raw) != expected:
        raise ValueError('SOURCE_BLOB_MISMATCH: ' + path)
    return raw


def load_pins(root):
    body=read_pinned(root, ORIGINAL+'/SOURCE_PINS.json',PINS_BLOB)
    obj=json.loads(body)
    if obj['memory'] != MEMORY or obj['gateway'] != GATEWAY or type(obj['files']) is not list:
        raise ValueError('SOURCE_MANIFEST_HOLD')
    files=obj['files']
    if len(files)!=149 or sum(x['ref']==MEMORY for x in files)!=136 or sum(x['ref']==GATEWAY for x in files)!=13:
        raise ValueError('SOURCE_COUNT_HOLD')
    return files


def stage_sources(root, stage, pins):
    seen=set()
    for item in pins:
        path, ref, blob = (item[k] for k in ('path','ref','blob'))
        dest=checked_path(stage,path)
        key=path.casefold()
        if key in seen:
            raise ValueError('DUPLICATE_PATH_HOLD')
        seen.add(key)
        if ref==MEMORY:
            origin=path
        elif ref==GATEWAY:
            origin=OVERLAY+'/'+path
        else:
            raise ValueError('UNEXPECTED_SOURCE_REF')
        raw=read_pinned(root,origin,blob)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
    return len(seen)


def main(root=None):
    root = Path(__file__).resolve().parents[2] if root is None else Path(root).resolve()
    pins=load_pins(root)
    original=read_pinned(root,ORIGINAL+'/test_memory_gateway.py',TEST_BLOB)
    with tempfile.TemporaryDirectory(prefix='m5c-') as tmp:
        stage=Path(tmp).resolve()
        count=stage_sources(root,stage,pins)
        test=stage/'test_memory_gateway.py'
        test.write_bytes(original)
        backend=stage/BACKEND
        print('SOURCE_PINS_VERIFIED='+str(count),flush=True)
        print('ORIGINAL_TEST_BLOB='+git_blob(original),flush=True)
        print('ORIGINAL_TEST_SHA256='+sha256(original).hexdigest(),flush=True)
        print('PYTHON='+sys.version.replace('\n',' '),flush=True)
        # Explicit paths under -I: ambient PYTHONPATH and user site are not used.
        bootstrap=('import sys, runpy, sqlite3, cryptography; '
                   'sys.path[:0]=sys.argv[1:4]; '
                   'print("SQLITE="+sqlite3.sqlite_version,flush=True); '
                   'print("CRYPTOGRAPHY="+cryptography.__version__,flush=True); '
                   'sys.argv=[sys.argv[4]]; runpy.run_path(sys.argv[0],run_name="__main__")')
        env={k:v for k,v in os.environ.items() if k.upper() in
             {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','HOME','USERPROFILE','LOCALAPPDATA','APPDATA','SYSTEMDRIVE'}}
        rc=subprocess.call([sys.executable,'-I','-B','-c',bootstrap,str(backend),str(backend/'tests'),str(stage/'tests/w5'),str(test)],cwd=stage,env=env)
        print('TEST_EXIT_CODE='+str(rc),flush=True)
        return rc


if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:
        print('BLOCKED: '+str(exc),file=sys.stderr,flush=True)
        sys.exit(2)
