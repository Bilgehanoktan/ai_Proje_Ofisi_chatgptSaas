"""MI03-GATE-01 local review of exact G6A/IAM sources; not G2 full runner."""
from pathlib import Path
from hashlib import sha1, sha256
import sys, unittest, sqlite3, json
ROOT = Path(__file__).resolve().parent
B = ROOT / 'product/ai-company-os-backend'
PINS = {
    'app/__init__.py': 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391',
    'app/core/__init__.py': '9d457472970b7f581687ba142d1bf99ba91c7388',
    'app/core/transaction/__init__.py': '5b19819cd7070302e874ecee80170a3921ce8fb0',
    'app/core/iam_session.py': 'f3c37428acd475e09c228bce47d534d6584cd944',
    'app/core/transaction/intent_authority.py': '88fd68c563db7e620c5b06c1a9c6b68d304ae071',
    'tests/test_iam_session_d5g1.py': '6be21cfdcaf7408d7d17b5848966bb7f6772581e',
    'tests/test_iam_authority_d5g2.py': '16bfc7013ae77cdcf437227b9fb6ac8a9a69d08c',
}
def verify():
    rows = {}
    for rel, pin in PINS.items():
        path = B / rel
        if path.resolve() != path or not path.is_file():
            raise RuntimeError('SOURCE_PATH_HOLD ' + rel)
        raw = path.read_bytes()
        if sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != pin:
            raise RuntimeError('SOURCE_PIN_HOLD ' + rel)
        compile(raw, str(path), 'exec')
        rows[rel] = dict(blob=pin, bytes=len(raw), sha256=sha256(raw).hexdigest())
    return rows

def main():
    before = verify()
    print('SOURCE_PINS=7/7', flush=True)
    print('ENV='+sys.version.split()[0]+'/'+sqlite3.sqlite_version, flush=True)
    print('SOURCE_HASHES='+json.dumps(before,sort_keys=True), flush=True)
    sys.path[:0] = [str(B),str(B/'tests')]
    import app.core.iam_session as iam
    import app.core.transaction.intent_authority as authority
    if Path(iam.__file__).resolve() != B/'app/core/iam_session.py' or Path(authority.__file__).resolve() != B/'app/core/transaction/intent_authority.py':
        raise RuntimeError('IMPORT_PATH_HOLD')
    total=0
    for module, expected in [('test_iam_session_d5g1',14),('test_iam_authority_d5g2',19)]:
        suite=unittest.defaultTestLoader.loadTestsFromName(module)
        if suite.countTestCases()!=expected:
            raise RuntimeError('TEST_COUNT_HOLD '+module)
        r=unittest.TextTestRunner(verbosity=2).run(suite)
        counts=[r.testsRun,len(r.failures),len(r.errors),len(r.skipped),len(r.expectedFailures),len(r.unexpectedSuccesses)]
        print('GROUP_COUNTS='+module+' '+json.dumps(counts),flush=True)
        if counts!=[expected,0,0,0,0,0] or not r.wasSuccessful():
            return 1
        total+=r.testsRun
    if verify()!=before:
        raise RuntimeError('SOURCE_DRIFT_HOLD')
    print('POSTCHECK=7/7',flush=True)
    print('TOTAL='+str(total),flush=True)
    print('PRODUCT_ACCEPTANCE=HOLD',flush=True)
    return 0
if __name__=='__main__':
    sys.exit(main())
