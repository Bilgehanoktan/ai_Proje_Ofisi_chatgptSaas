"""0227 isolated Windows E1 recovery + original 24 tests. No PG, CI or PROD."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

SOURCE = '52219c7a222bae41735c9a9b9f7f7082462982b4'
MANIFEST = '981a13fc226184dc3a911ae0d94e0042285ff302'
A0_REVIEW = 'a861d3d6bf4cd6e3727f2cbb2474ee221a435c5b3d660b11a9ce10d8acb72545'
NPM_LOCK = '036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88'
PY_LOCK = 'bedb32b1d0462180ccc25fc4487af3b61ba30c4ee0dfd946fa33a3fe6fdc5253'
B = 'product/ai-company-os-backend'
F = 'product/ai-company-os-frontend'
SUITES = {'test_company_fence_binding_0219': 6, 'test_result_reference_0221': 10,
          'test_canonical_research_0224': 8}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def blob(p):
    raw = p.read_bytes()
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def load(path, expected):
    require(blob(path) == expected, 'RUNNER_PIN_HOLD: ' + path.name)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def tree_pins(root, prefix):
    out = {}
    for row in git(root, 'ls-tree', '-r', '-z', SOURCE, '--', prefix).split(b'\0'):
        if not row:
            continue
        meta, name = row.split(b'\t', 1)
        mode, kind, pin = meta.decode().split()
        require(kind == 'blob' and mode in ('100644', '100755'), 'NON_FILE_HOLD')
        out[name.decode('utf-8')] = pin
    require(bool(out), 'TREE_EMPTY_HOLD')
    return out


def check_files(root, pins):
    for name, expected in pins.items():
        p = root / name
        require(p.is_file() and p.resolve() == p.absolute() and blob(p) == expected,
                'SOURCE_FILE_HOLD: ' + name)


def source_check(root):
    require(git(root, 'rev-parse', 'HEAD').decode().strip() == SOURCE, 'CHECKOUT_PIN_HOLD')
    require(not git(root, 'status', '--porcelain', '--untracked-files=all'), 'DIRTY_CHECKOUT_HOLD')
    verifier = load(root/'scripts/verify_product.py', 'dd414ebd0b65d8e9c3eec47fdeed03a00e5879e8')
    require(verifier.verify(root, MANIFEST)['verified_files'] == 392, 'MANIFEST_COUNT_HOLD')
    pp = tree_pins(root, 'product')
    dp = tree_pins(root, 'database')
    require(len(pp) == 393, 'PRODUCT_COUNT_HOLD')
    check_files(root, {**pp, **dp})
    return pp, dp


def check_origin(a0, w):
    review = a0/'locks/REVIEW.json'
    require(sha(review) == A0_REVIEW, 'A0_REVIEW_HASH_HOLD')
    require(sha(a0/F/'package-lock.json') == NPM_LOCK and sha(a0/'locks/python.lock') == PY_LOCK,
            'A0_LOCK_HASH_HOLD')
    previous = json.loads(review.read_text(encoding='utf-8'))
    require(len(previous['wheels']) == 28 and previous['npm_packages'] == 61, 'A0_INVENTORY_HOLD')
    # Check exact reviewed graph AND every retained wheel byte via original W8 logic.
    w.MANIFEST_BLOB = previous['manifest_blob']
    require(w.lock_inventory(a0) == previous, 'A0_WHEEL_OR_ENVIRONMENT_HOLD')
    w.MANIFEST_BLOB = MANIFEST
    return previous


def fresh_dir(path, source, a0):
    require(not path.exists() and not path.is_relative_to(source) and not path.is_relative_to(a0)
            and not source.is_relative_to(path) and not a0.is_relative_to(path), 'STAGE_PATH_HOLD')
    path.mkdir(parents=True, exist_ok=False)


def copy_pins(source, stage, pins):
    for name in pins:
        target = stage/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source/name, target)
    check_files(stage, pins)


def lock_review(stage, w, pp, dp):
    check_files(stage, {**pp, **dp})
    inventory = w.lock_inventory(stage)
    require(inventory['npm_lock_sha256'] == NPM_LOCK and inventory['python_lock_sha256'] == PY_LOCK,
            'CURRENT_LOCK_DRIFT_HOLD')
    return {'source_commit': SOURCE, 'origin_review_sha256': A0_REVIEW,
            'product_files': len(pp), 'database_git_pins': dp, 'inventory': inventory}


def prepare(source, a0, stage, w, pp, dp):
    origin = check_origin(a0, w)
    fresh_dir(stage, source, a0)
    copy_pins(source, stage, {**pp, **dp})
    (stage/'locks/wheels').mkdir(parents=True)
    for name in origin['wheels']:
        require(Path(name).name == name and name.endswith('.whl'), 'WHEEL_PATH_HOLD')
        shutil.copy2(a0/'locks/wheels'/name, stage/'locks/wheels'/name)
    shutil.copy2(a0/'locks/python.lock', stage/'locks/python.lock')
    shutil.copy2(a0/F/'package-lock.json', stage/F/'package-lock.json')
    review = lock_review(stage, w, pp, dp)
    require(review['inventory']['wheels'] == origin['wheels'], 'COPIED_WHEEL_HOLD')
    w.write_json(stage/'locks/REVIEW_0227.json', review)
    print('REVIEW_0227 SHA256:', sha(stage/'locks/REVIEW_0227.json'))
    print('Inspect new source-bound REVIEW_0227.json; do not reuse A0 approval.')


def run_logged(args, cwd, env, log):
    require(not log.exists(), 'LOG_EXISTS_HOLD')
    with log.open('xb') as out:
        r = subprocess.run(list(map(str, args)), cwd=cwd, env=env, stdout=out, stderr=subprocess.STDOUT)
    print(log.name, 'exit', r.returncode, flush=True)
    return r.returncode


TEST_DRIVER = r'''
import json, sys, unittest
name, expected = sys.argv[1], int(sys.argv[2])
sys.path.insert(0, 'tests')
suite = unittest.defaultTestLoader.loadTestsFromName(name)
collected = suite.countTestCases()
r = unittest.TextTestRunner(verbosity=2).run(suite)
report = dict(suite=name, collected=collected, ran=r.testsRun,
              failures=len(r.failures), errors=len(r.errors), skipped=len(r.skipped),
              expected_failures=len(r.expectedFailures), unexpected_successes=len(r.unexpectedSuccesses))
report['pass'] = r.wasSuccessful() and r.testsRun == expected and not r.skipped and not r.expectedFailures
print('AIOS_RESULT '+json.dumps(report), flush=True)
raise SystemExit(0 if report['pass'] else 1)
'''


def parse_result(log, name, expected, code):
    lines = [s for s in log.read_text(encoding='utf-8', errors='replace').splitlines()
             if s.startswith('AIOS_RESULT ')]
    require(len(lines) == 1, 'TEST_REPORT_HOLD: ' + name)
    r = json.loads(lines[0][12:])
    require(r['suite'] == name and r['collected'] == expected and r['ran'] == expected
            and r['pass'] is True and code == 0
            and all(r[k] == 0 for k in ('failures','errors','skipped','expected_failures','unexpected_successes')),
            'TEST_FAILURE_HOLD: ' + name)
    return {**r, 'log_sha256': sha(log)}


def check_stage_clean(stage, pp, dp):
    for prefix, expected in [('product', set(pp) | {F+'/package-lock.json'}), ('database', set(dp))]:
        paths = list((stage/prefix).rglob('*'))
        require(all(p.resolve() == p.absolute() for p in paths), 'STAGE_LINK_HOLD')
        actual = {p.relative_to(stage).as_posix() for p in paths if p.is_file()}
        require(actual == expected, 'STAGE_EXTRA_OR_MISSING_HOLD: ' + prefix)


def check_python_inventory(lock, log):
    norm = lambda s: re.sub(r'[-_.]+', '-', s).lower()
    expected = {}
    for line in lock.read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'([^=\s]+)==([^\s]+) --hash=sha256:[0-9a-f]{64}', line)
        require(match is not None, 'LOCK_FORMAT_HOLD')
        expected[norm(match[1])] = match[2]
    actual = {norm(x['name']):x['version'] for x in json.loads(log.read_text(encoding='utf-8'))}
    require(len(expected) == 28 and all(actual.get(k) == v for k,v in expected.items())
            and set(actual) - set(expected) <= {'pip'}, 'INSTALLED_PYTHON_DRIFT_HOLD')


def execute(source, a0, stage, w, pp, dp, approval):
    require(not stage.is_relative_to(source) and not stage.is_relative_to(a0)
            and not source.is_relative_to(stage) and not a0.is_relative_to(stage), 'STAGE_PATH_HOLD')
    origin = check_origin(a0, w)
    review_path = stage/'locks/REVIEW_0227.json'
    require(re.fullmatch('[0-9a-f]{64}', approval or '') and sha(review_path) == approval,
            'NEW_REVIEW_APPROVAL_HOLD')
    review = lock_review(stage, w, pp, dp)
    require(json.loads(review_path.read_text(encoding='utf-8')) == review
            and review['inventory']['wheels'] == origin['wheels'], 'REVIEW_RECHECK_HOLD')
    for p in (stage/'.venv', stage/F/'node_modules', stage/'evidence', stage/'tmp'):
        require(not p.exists(), 'USE_FRESH_STAGE_HOLD: ' + p.name)
    check_stage_clean(stage, pp, dp)
    evidence = stage/'evidence'; evidence.mkdir()
    temp = stage/'tmp'; temp.mkdir()
    env = w.env_local(); env.update(TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp), PYTHONUTF8='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
    usercfg, globalcfg = temp/'npm-user.cfg', temp/'npm-global.cfg'
    usercfg.touch(); globalcfg.touch()
    env.update(NPM_CONFIG_USERCONFIG=str(usercfg), NPM_CONFIG_GLOBALCONFIG=str(globalcfg))
    def run(args, cwd, name):
        code = run_logged(args, cwd, env, evidence/name)
        require(code == 0, 'COMMAND_HOLD: '+name)
    run([sys.executable, '-m', 'venv', stage/'.venv'], stage, '01_venv.log')
    py = w.python(stage)
    run([py,'-m','pip','--isolated','install','--no-index','--find-links',stage/'locks/wheels',
         '--require-hashes','-r',stage/'locks/python.lock'],stage,'02_pip_install.log')
    run([py,'-m','pip','check'],stage,'03_pip_check.log')
    run([w.npm(),'ci','--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org'],
        stage/F,'04_npm_ci.log')
    require(lock_review(stage,w,pp,dp) == review, 'POST_INSTALL_SOURCE_LOCK_HOLD')
    run([py,'-m','pip','list','--format=json'],stage,'05_pip_list.log')
    check_python_inventory(stage/'locks/python.lock', evidence/'05_pip_list.log')
    run([w.npm(),'ls','--all','--json'],stage/F,'06_npm_tree.log')
    w.write_json(evidence/'E1_LOCAL_RESULT.json', {'status':'LOCAL_PREPARED_REVIEW_REQUIRED_FOR_GATE',
        'source_commit':SOURCE,'manifest_blob':MANIFEST,'review_sha256':approval,
        'product_files':393,'verified_manifest_entries':392,'database_files':len(dp),
        'logs':{p.name:sha(p) for p in evidence.glob('*.log')}})
    results=[]
    for name, expected in SUITES.items():
        log=evidence/(name+'.log')
        code=run_logged([py,'-B','-c',TEST_DRIVER,name,expected],stage/B,env,log)
        results.append(parse_result(log,name,expected,code))
    require(lock_review(stage,w,pp,dp) == review, 'POST_TEST_SOURCE_LOCK_HOLD')
    source_check(source)
    w.write_json(evidence/'ORIGINAL24_RESULT.json', {'status':'PASS','source_commit':SOURCE,
        'review_sha256':approval,'results':results,'total':sum(r['ran'] for r in results),
        'scope':'SQLite D0 only; no PostgreSQL, full build, browser, independent acceptance'})
    print('24/24 PASS; send evidence and REVIEW_0227.json for review.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','execute']);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--a0-stage',type=Path,required=True);p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--approve');a=p.parse_args()
    require(sys.platform=='win32' and sys.version.split()[0]=='3.14.3','WINDOWS_PYTHON_3_14_3_REQUIRED')
    source,a0,stage=(x.resolve() for x in (a.source,a.a0_stage,a.stage))
    sys.dont_write_bytecode=True
    pp,dp=source_check(source)
    w=load(source/'tests/integration/w8_unified.py','162a2387e5cdea6828a0cbbf0dab247bc4678551')
    require(subprocess.check_output([w.node(),'--version'],text=True).strip()=='v24.14.0','NODE_PIN_HOLD')
    require(subprocess.check_output([w.npm(),'--version'],text=True).strip()=='11.9.0','NPM_PIN_HOLD')
    if a.command=='prepare': prepare(source,a0,stage,w,pp,dp)
    else: execute(source,a0,stage,w,pp,dp,a.approve)


if __name__=='__main__':
    try: main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as e:
        print('HOLD:', e, file=sys.stderr);sys.exit(1)
