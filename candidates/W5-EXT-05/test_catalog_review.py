import json
import unittest
from dataclasses import replace, asdict
from pathlib import Path
from hashlib import sha256
from app.core.agent_runtime.lifecycle import Scope, LeaseObservation, ClockSample
from app.core.runtime_preview import Scope as CompatScope
from app.core.skill_review import SkillManifestSample as CompatManifest
from app.engines.skill_engine.manifest_review import SkillManifestSample, inspect_skill
from app.engines.skill_engine.resolver import SourcePin, inspect_capabilities
from app.engines.model_gateway.registry import AdapterPin
from app.core.policy.gateway_review import EffectScope, GrantSample, inspect_gateway, DisabledToolGateway
from app.core.policy.witness_review import WitnessSample
from catalog_review import Bundle, CatalogReference, review_candidate
from build_catalog import canonical, sha

ROOT = Path(__file__).resolve().parent
LOCK = json.loads((ROOT/'CATALOG_LOCK.json').read_bytes())
PLAN = 'sha256:'+sha(b'ext05-local-review-plan')

def setup(skill='watch', role='research'):
    e = next(x for x in LOCK['entries'] if x['skill_id']==skill)
    p = ROOT/'catalog'/skill
    b = Bundle(*[(p/n).read_bytes() for n in ('manifest.json','input.schema.json','output.schema.json')], (ROOT/'artifacts'/e['artifact_file']).read_bytes())
    ref = CatalogReference(**{k:e[k] for k in CatalogReference.__dataclass_fields__})
    m = json.loads(b.manifest)
    s = Scope('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY',PLAN,'ext05-review','demo-ext05-run','demo-ext05-'+role,'demo-ext05-principal-'+role)
    tool = tuple(m['tool_ids'])
    a = AdapterPin(s,'ext05-diagnostic-adapter','0.1.0',sha(b'ext05 synthetic adapter reference, not executable'),tool,())
    req = {'skill_id':skill,'version':ref.version,'role':role}
    return [b,ref,req,s,s,role,a,(a,),tool,tool]

def repin(args, **updates):
    m = json.loads(args[0].manifest);m.update(updates)
    raw=canonical(m);args[0]=replace(args[0],manifest=raw);args[1]=replace(args[1],manifest_sha256=sha(raw))

class CatalogTests(unittest.TestCase):
    def assert_hold(self, args, reason, structural=False):
        r=review_candidate(*args)
        self.assertEqual(r.reason,reason);self.assertIs(r.structural_match,structural)
        self.assertEqual((r.status,r.decision,r.effective_tools),('QUARANTINED','HOLD',()))
        for k in ('enabled','grant_created','dispatch_allowed','independent_verified'): self.assertIs(getattr(r,k),False)
        return r
    def test_facades_identity(self):
        self.assertIs(Scope,CompatScope);self.assertIs(SkillManifestSample,CompatManifest)
    def test_three_candidates_five_role_hints(self):
        for s,r in [('superpowers','engineer'),('superpowers','qa'),('ui-ux-pro-max','engineer'),('ui-ux-pro-max','research'),('watch','research')]:
            with self.subTest(skill=s,role=r):
                a=setup(s,r);self.assertEqual(self.assert_hold(a,'INDEPENDENT_RECEIPTS_ABSENT',True).diagnostic_overlap,a[8])
    def test_exact_bytes(self):
        for i in range(4):
            a=setup();fields=list(Bundle.__dataclass_fields__);k=fields[i];a[0]=replace(a[0],**{k:getattr(a[0],k)+b' '});self.assert_hold(a,'BYTE_PIN_MISMATCH')
    def test_oversize(self):
        a=setup();a[0]=replace(a[0],artifact=b'x'*262145);self.assert_hold(a,'BYTE_LIMIT_HOLD')
    def test_wrong_reference(self):
        a=setup();a[1]=None;self.assert_hold(a,'REFERENCE_HOLD')
    def test_noncanonical_json_even_repinned(self):
        a=setup();raw=a[0].manifest+b' ';a[0]=replace(a[0],manifest=raw);a[1]=replace(a[1],manifest_sha256=sha(raw));self.assert_hold(a,'INVALID_CANDIDATE_HOLD')
    def test_tenant_company_environment(self):
        for field in ('tenant_id','company_id','environment_id'):
            a=setup();a[3]=replace(a[3],**{field:'other'});self.assert_hold(a,'SCOPE_HOLD')
    def test_task_run_agent_principal_plan(self):
        for field in ('task_id','run_id','agent_instance_id','principal_id','plan_revision'):
            a=setup();a[3]=replace(a[3],**{field:'demo-other' if field!='plan_revision' else 'sha256:'+sha(b'other')});self.assert_hold(a,'SCOPE_HOLD')
    def test_wrong_role(self):
        self.assert_hold(setup('watch','qa'),'ROLE_REQUEST_HOLD')
    def test_forged_role_identity(self):
        a=setup();a[3]=a[4]=replace(a[3],principal_id='demo-other');self.assert_hold(a,'ROLE_REQUEST_HOLD')
    def test_unknown_request_key(self):
        a=setup();a[2]['enable']=True;self.assert_hold(a,'ROLE_REQUEST_HOLD')
    def test_request_version(self):
        a=setup();a[2]['version']='old';self.assert_hold(a,'ROLE_REQUEST_HOLD')
    def test_reference_version(self):
        a=setup();a[1]=replace(a[1],version='old');self.assert_hold(a,'VERSION_HOLD')
    def test_manifest_authority(self):
        for v in ({'enabled':True},{'g7_ref':'fake'},{'g8_ref':'fake'},{'tool_ids_semantics':'REAL'}):
            a=setup();repin(a,**v);self.assert_hold(a,'AUTHORITY_HOLD')
    def test_schema_binding(self):
        a=setup();repin(a,input_schema_sha256=sha(b'wrong'));self.assert_hold(a,'SCHEMA_OR_SOURCE_BINDING_HOLD')
    def test_source_binding(self):
        a=setup();m=json.loads(a[0].manifest);m['source']['sha256']=sha(b'wrong');repin(a,source=m['source']);self.assert_hold(a,'SCHEMA_OR_SOURCE_BINDING_HOLD')
    def test_source_git_blob_binding(self):
        a=setup();m=json.loads(a[0].manifest);m['source']['git_blob']='0'*40;repin(a,source=m['source']);self.assert_hold(a,'SCHEMA_OR_SOURCE_BINDING_HOLD')
    def test_source_commit_binding(self):
        a=setup();m=json.loads(a[0].manifest);m['source']['commit']='0'*40;repin(a,source=m['source']);self.assert_hold(a,'SCHEMA_OR_SOURCE_BINDING_HOLD')
    def test_source_path_binding(self):
        a=setup();m=json.loads(a[0].manifest);m['source']['path']='other';repin(a,source=m['source']);self.assert_hold(a,'SCHEMA_OR_SOURCE_BINDING_HOLD')
    def test_schema_semantics_even_repinned(self):
        a=setup();o=json.loads(a[0].output_schema);o['properties']['enabled']={'const':True};raw=canonical(o);a[0]=replace(a[0],output_schema=raw);a[1]=replace(a[1],output_schema_sha256=sha(raw));repin(a,output_schema_sha256=sha(raw));self.assert_hold(a,'SCHEMA_PROFILE_HOLD')
    def test_adapter_effect_ceiling(self):
        a=setup();a[6]=replace(a[6],effect_ceiling=('network',));a[7]=(a[6],);self.assert_hold(a,'ADAPTER_EFFECT_CEILING_HOLD')
    def test_empty_requested(self):
        a=setup();a[8]=();self.assert_hold(a,'CAPABILITY_REQUEST_INVALID')
    def test_adapter_enabled(self):
        a=setup();a[6]=replace(a[6],enabled=True);a[7]=(a[6],);self.assert_hold(a,'ADAPTER_SCOPE_HOLD')
    def test_adapter_scope(self):
        a=setup();a[6]=replace(a[6],scope=replace(a[3],task_id='other'));a[7]=(a[6],);self.assert_hold(a,'ADAPTER_SCOPE_HOLD')
    def test_duplicate_adapter(self):
        a=setup();a[7]=(a[6],a[6]);self.assert_hold(a,'ADAPTER_SCOPE_HOLD')
    def test_unknown_tool(self):
        a=setup();a[8]=('network-upload',);self.assert_hold(a,'CAPABILITY_HOLD')
    def test_policy_empty(self):
        a=setup();a[9]=();self.assert_hold(a,'CAPABILITY_HOLD')
    def test_duplicate_requested_tool(self):
        a=setup();a[8]=a[8]+a[8];self.assert_hold(a,'CAPABILITY_REQUEST_INVALID')
    def test_manifest_core_denies_enabled(self):
        a=setup();s=a[3];m=SkillManifestSample(s,'watch','0.1.0',a[1].manifest_sha256,a[1].input_schema_sha256,a[1].output_schema_sha256,a[8],enabled=True)
        self.assertEqual(inspect_skill(m,m,s).reason,'SKILL_ENABLE_PROHIBITED')
    def test_resolver_requires_manifest_digest_not_artifact_digest(self):
        a=setup();s=a[3];r=a[1];m=SkillManifestSample(s,r.skill_id,r.version,r.manifest_sha256,r.input_schema_sha256,r.output_schema_sha256,a[8]);p=SourcePin(r.skill_id,r.version,r.artifact_sha256,'review-only','local-review-only')
        self.assertEqual(inspect_capabilities(m,m,s,p,p,a[6],a[7],a[8],a[9]).reason,'SKILL_SOURCE_PIN_HOLD')
    def test_output_shape(self):
        a=setup();r=self.assert_hold(a,'INDEPENDENT_RECEIPTS_ABSENT',True);o=json.loads(a[0].output_schema);d=json.loads(json.dumps(asdict(r)));self.assertEqual(set(d),set(o['required']))
        for k,p in o['properties'].items():
            if 'const' in p:self.assertEqual(d[k],p['const'])

class GatewayTests(unittest.TestCase):
    def setUp(self):
        a=setup();s=a[3];tool=a[8][0];d=sha(b'ext05 synthetic effect only')
        self.e=EffectScope(s,'review',tool,d,'demo-grant','demo-admission','demo-lease','demo-budget',1,2,3)
        self.g=GrantSample(s,'demo-grant','demo-admission','demo-lease','demo-budget',('review',),(tool,),d,1,2,3,100,False)
        self.l=LeaseObservation(s,'demo-lease','demo-grant',1,1,3,1,2,100,10)
        self.c=ClockSample(20,1,2,20)
        self.w=WitnessSample(s,'demo-witness',2,1,sha(b'synthetic witness only'),10)
    def args(self):return [self.e,self.g,self.g,self.l,self.l,self.c,self.w,self.w,20]
    def deny(self,args,reason,match=False):
        r=inspect_gateway(*args);self.assertEqual((r.reason,r.structural_match,r.decision),(reason,match,'DENY'));self.assertFalse(r.dispatch_allowed);self.assertFalse(r.provider_called);self.assertFalse(r.release_ready)
    def test_no_grant(self):
        a=self.args();a[1]=a[2]=None;self.deny(a,'GRANT_REFERENCE_MISSING')
    def test_revoked(self):
        a=self.args();a[1]=a[2]=replace(self.g,revoked=True);self.deny(a,'GRANT_REVOKED')
    def test_mismatched_reference(self):
        a=self.args();a[2]=replace(self.g,expires_tick=90);self.deny(a,'GRANT_REFERENCE_MISMATCH')
    def test_outside_grant(self):
        a=self.args();a[0]=replace(self.e,tool_id='upload');self.deny(a,'EFFECT_OUTSIDE_GRANT')
    def test_expired(self):
        a=self.args();a[1]=a[2]=replace(self.g,expires_tick=20);self.deny(a,'GRANT_EXPIRED')
    def test_stale_witness(self):
        a=self.args();a[6]=a[7]=replace(self.w,epoch=1);self.deny(a,'ERR_WA_EPOCH_STALE')
    def test_missing_lease(self):
        a=self.args();a[3]=None;self.deny(a,'GATEWAY_LEASE_BINDING_MISMATCH')
    def test_complete_synthetic_chain_denied(self):
        self.deny(self.args(),'PEP_ISOLATION_NOT_PROVEN',True)
    def test_disabled_gateway(self):
        r=DisabledToolGateway().dispatch(self.e);self.assertEqual(r.reason,'ERR_F3_EXTERNAL_WRITE_FORBIDDEN');self.assertEqual(r.decision,'DENY');self.assertFalse(r.dispatch_allowed)

if __name__=='__main__':unittest.main()
