"""Candidate: only run against an independently authorized loopback D0 instance. No process start or writes."""
import argparse
import json
from pathlib import Path
from urllib.request import HTTPRedirectHandler, build_opener, Request, ProxyHandler
from urllib.error import HTTPError

BASE = 'http://127.0.0.1:8000'
LIMIT = 512 * 1024
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

OPENER = build_opener(ProxyHandler({}), NoRedirect())

def get(path, expected=200):
    try:
        with OPENER.open(Request(BASE+path, headers={'Accept':'application/json'}, method='GET'), timeout=5) as response:
            if response.status != expected or response.headers.get_content_type() != 'application/json':
                raise ValueError('HTTP_OR_CONTENT_TYPE_MISMATCH')
            raw = response.read(LIMIT+1)
            if len(raw)>LIMIT: raise ValueError('RESPONSE_TOO_LARGE')
            return json.loads(raw)
    except HTTPError as exc:
        if exc.code==expected==404:
            exc.close()
            return None
        exc.close()
        raise

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    fixtures=args.root/'product'/'ai-company-os-backend'/'fixtures'
    def fixture(name): return json.loads((fixtures/name).read_text(encoding='utf-8'))
    status={'mode':'D0_SAMPLE_NO_RUNTIME','security_acceptance':'HOLD','release_ready':False,'real_test':'NOT_RUN'}
    authority={'mode':'D0_SAMPLE_NO_RUNTIME','effective':False,'security_acceptance':'HOLD','blocked':['CODE','REPO','DEV','REAL_TEST','PROD','SPEND','EXTERNAL_MUTATION'],'real_test':'NOT_RUN','enforcement':'NOT_IMPLEMENTED'}
    def preview():
        value=get('/demo/v1/core/preview')
        return isinstance(value,dict) and set(value)=={'sample','plan_preview','event_preview'} and value['sample']==fixture('core.preview.json')
    cases=[('status',lambda: get('/demo/v1/status')==status),
           ('snapshot',lambda: get('/demo/v1/office/worlds/demo-world/snapshot')==fixture('office.snapshot.json')),
           ('catalog',lambda: get('/demo/v1/catalog')==fixture('company.catalog.json')),
           ('plan',lambda: get('/demo/v1/core/plan-projection')==fixture('core.plan.projection.json')),
           ('preview_sample',preview),
           ('authority',lambda: get('/demo/v1/authority')==authority),
           ('unknown_world_404',lambda: get('/demo/v1/office/worlds/unknown-world/snapshot',404) is None)]
    rows=[]
    for name,check in cases:
        try: rows.append({'case':name,'status':'PASS' if check() else 'FAIL'})
        except Exception as exc: rows.append({'case':name,'status':'FAIL','error':type(exc).__name__})
    print(json.dumps({'scope':'D0_LOOPBACK_SMOKE_ONLY','independent_acceptance':False,'cases':rows},indent=2))
    return int(any(row['status']!='PASS' for row in rows))

if __name__=='__main__': raise SystemExit(main())
