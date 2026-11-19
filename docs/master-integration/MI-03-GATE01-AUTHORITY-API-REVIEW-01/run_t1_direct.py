"""GATE01 selected exact D0 T1 replay; no full G2 or Memory chain."""
import hashlib, json, pathlib, sqlite3, sys, unittest
HERE=pathlib.Path(__file__).resolve().parent
ROOT=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)==2 else HERE
PINS=json.loads((HERE/'T1_DIRECT_PINS.json').read_text(encoding='utf-8'))
B=ROOT/'product/ai-company-os-backend'
def verify():
    if len(PINS)!=30: raise RuntimeError('PIN_COUNT_HOLD')
    for rel,pin in PINS.items():
        p=ROOT/rel
        if not p.is_file() or p.resolve()!=p or not p.is_relative_to(ROOT):
            raise RuntimeError('SOURCE_PATH_HOLD '+rel)
        b=p.read_bytes()
        actual={'blob':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
        if actual!=pin: raise RuntimeError('SOURCE_PIN_HOLD '+rel)
        if p.suffix=='.py': compile(b,str(p),'exec')
    return len(PINS)
def main():
    print('PRECHECK='+str(verify())+'/30',flush=True)
    print('ENV='+sys.version.split()[0]+'/'+sqlite3.sqlite_version,flush=True)
    sys.path[:0]=[str(B),str(B/'tests')]
    groups=(('test_intent_authority_t1_0212',7),('test_transition_mapping_0194',35))
    total=0
    for module,expected in groups:
        suite=unittest.defaultTestLoader.loadTestsFromName(module)
        if suite.countTestCases()!=expected: raise RuntimeError('COUNT_HOLD '+module)
        r=unittest.TextTestRunner(verbosity=1).run(suite)
        counts=[r.testsRun,len(r.failures),len(r.errors),len(r.skipped),len(r.expectedFailures),len(r.unexpectedSuccesses)]
        print('GROUP='+module+' '+json.dumps(counts),flush=True)
        if not r.wasSuccessful() or counts!=[expected,0,0,0,0,0]: return 1
        total+=r.testsRun
    for name,mod in tuple(sys.modules.items()):
        if name=='app' or name.startswith('app.') or name in dict(groups):
            file=getattr(mod,'__file__',None)
            if not file or str(pathlib.Path(file).resolve().relative_to(ROOT)) not in PINS:
                raise RuntimeError('UNPINNED_IMPORT_HOLD '+name)
    print('POSTCHECK='+str(verify())+'/30',flush=True)
    print('TOTAL='+str(total),flush=True)
    print('MEMORY_FULLCHAIN=NOT_RUN',flush=True)
    print('PRODUCT_ACCEPTANCE=HOLD',flush=True)
    return 0
if __name__=='__main__': sys.exit(main())
