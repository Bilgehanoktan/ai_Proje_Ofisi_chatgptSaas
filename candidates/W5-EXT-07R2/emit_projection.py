"""Local cross-language acceptance fixture; never a registry or permission issuer."""
import json
from dataclasses import asdict
from hashlib import sha1
from test_catalog_review import setup, LOCK
from catalog_review import review_candidate
from build_catalog import canonical

EXPECTED_BLOB='436ceb58f36690087324d6ebdfbdbd6601c60427'

def project():
    rows=[]
    for entry in LOCK['entries']:
        sid=entry['skill_id']
        manifest=json.loads(setup(sid)[0].manifest)
        roles=manifest['role_hints']
        reviews=[]
        for role in roles:
            result=review_candidate(*setup(sid,role))
            row={**asdict(result),'role_hint':role}
            if result.decision!='HOLD' or result.status!='QUARANTINED' or result.enabled or result.effective_tools or result.grant_created or result.dispatch_allowed or result.independent_verified:
                raise ValueError('AUTHORITY_BOUNDARY_HOLD')
            reviews.append(row)
        rows.append({**{k:entry[k] for k in ('artifact_sha256','input_schema_sha256','manifest_sha256','output_schema_sha256','skill_id','source_path','version')},'effective_tools':[],'enabled':False,'installation_evidence':'NOT_RUN','installed':False,'reviews':reviews,'role_hints':roles,'status':'QUARANTINED'})
    return dict(active_count=0,authority='NONE',independent_acceptance='HOLD',installed_count=0,profile='EXT05_LOCAL_SYNTHETIC_READBACK',skills=rows)

if __name__=='__main__':
    import sys
    raw=canonical(project())
    actual=sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if actual!=EXPECTED_BLOB:
        raise SystemExit('PROJECTION_PIN_MISMATCH '+actual)
    sys.stdout.buffer.write(raw)
