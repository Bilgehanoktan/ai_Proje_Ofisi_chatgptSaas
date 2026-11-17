from dataclasses import asdict, replace
import unittest
from identity_binding import Request, Binding as IdentityBinding, binding_digest
from org_model import Org, Unit, Seat
from staffing import Staffing, Definition, Instance, Binding
from operations import ProjectTeam, digest, propose
from org_bridge import OrgPin, inspect_org, inspect_proposal

S=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
R=Request(S,'project-a','sha256:'+'a'*64,'task-a','demo-run','demo-agent','demo-principal','b'*64,2,3)
B=IdentityBinding(R,R.principal,1,2,3,4,'c'*64,'d'*64,'e'*64,'f'*64,'aicos_d4_run_a','aicos_d4_0229','aicos_d4_0229_disposable',10,True)
O=Org(*S[:2],(Unit(S[1],'company',None),Unit('dep-a','department',S[1]),Unit('dep-b','department',S[1])),(Seat('lead','dep-b','orchestrator'),Seat('seat-a','dep-a','research','lead'),Seat('seat-b','dep-a','research','lead')))
ST=Staffing(O,(Definition('d-lead','orchestrator'),Definition('d-research','research')),(Instance('demo-lead','d-lead',*S[:2]),Instance(R.agent,'d-research',*S[:2]),Instance('demo-other','d-research',*S[:2])),(Binding('lead','demo-lead'),Binding('seat-a',R.agent),Binding('seat-b','demo-other')))
TEAM=ProjectTeam(*S[:2],ST.revision(),R.project,'lead',('lead','seat-a','seat-b'))
REF=(S,R.project,R.plan_revision,R.task,'research',R.agent,R.principal)
MEM=(R.project,R.plan_revision,R.task,R.run,R.agent,R.principal,0)
P=OrgPin(S,'1'*64,1,ST.revision(),digest(asdict(TEAM)),'seat-a','dep-a','research',binding_digest(B),digest(['d4-r5-core-member-review-v1',S,MEM]))

class Tests(unittest.TestCase):
    def review(self,**kw):
        args=dict(request=R,binding=B,latest_binding=B,tick=9,pin=P,latest_pin=P,staffing=ST,team=TEAM,task_ref=REF,core_scope=S,member_row=MEM,plan_role='research')
        args.update(kw);return inspect_org(**args)
    def deny(self,**kw):
        r=self.review(**kw);self.assertFalse(r.structural_match);self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)
    def test_hypothetical_common_scope_only(self):
        r=self.review();self.assertTrue(r.structural_match);self.assertEqual(r.decision,'HOLD');self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)
    def test_actual_org_scopes_disjoint(self):
        for k in 'ab':
            p=replace(P,scope=('synthetic-tenant-'+k,'synthetic-company-'+k,'ORG_R4_SAMPLE_ONLY'))
            self.assertEqual(self.review(pin=p,latest_pin=p).reason,'D4_COMMON_SCOPE_HOLD')
    def test_scope_dimensions(self):
        for i in range(3):
            v=list(S);v[i]='other';p=replace(P,scope=tuple(v));self.deny(pin=p,latest_pin=p)
    def test_core_scope(self):self.deny(core_scope=('other',*S[1:]))
    def test_stale_head(self):self.deny(latest_pin=replace(P,head='2'*64))
    def test_stale_sequence(self):self.deny(latest_pin=replace(P,sequence=2))
    def test_stale_staffing(self):self.deny(latest_pin=replace(P,staffing_sha='2'*64))
    def test_stale_team(self):self.deny(latest_pin=replace(P,team_sha='2'*64))
    def test_staffing_drift(self):self.deny(staffing=replace(ST,previous='2'*64))
    def test_team_drift(self):self.deny(team=replace(TEAM,members=('lead','seat-b')))
    def test_wrong_project(self):
        t=replace(TEAM,project='other');p=replace(P,team_sha=digest(asdict(t)));self.deny(team=t,pin=p,latest_pin=p)
    def test_wrong_seat(self):
        p=replace(P,seat='seat-b');self.deny(pin=p,latest_pin=p)
    def test_wrong_department(self):
        p=replace(P,department_id='dep-b');self.deny(pin=p,latest_pin=p)
    def test_wrong_role(self):self.deny(plan_role='independent-verifier')
    def test_ref_substitution(self):
        for i in range(7):
            r=list(REF);r[i]='other';self.deny(task_ref=tuple(r))
    def test_member_substitution(self):
        for i in range(6):
            m=list(MEM);m[i]='other';self.deny(member_row=tuple(m))
    def test_member_initial_version_drift(self):self.deny(member_row=MEM[:-1]+(1,))
    def test_identity_pin_drift(self):
        b=replace(B,role_revision=8);self.deny(binding=b,latest_binding=b)
    def test_missing_run(self):self.deny(member_row=None);self.deny(member_row=MEM[:3]+MEM[4:])
    def test_invalid_initial_version(self):self.deny(member_row=MEM[:-1]+(True,))
    def test_revoked_identity(self):self.deny(latest_binding=replace(B,active=False))
    def test_delegated_identity(self):
        b=replace(B,authenticated_principal='demo-human');self.deny(binding=b,latest_binding=b)
    def test_expiry(self):self.deny(tick=10)
    def test_malformed_pin(self):self.deny(pin=replace(P,sequence=True),latest_pin=replace(P,sequence=True))
    def test_delegation_proposal_no_authority(self):
        p=propose(ST,TEAM,R.task,'lead','seat-a','delegation');r=inspect_proposal(ST,TEAM,R.task,'lead','seat-a','delegation',p);self.assertTrue(r.structural_match);self.assertFalse(r.dispatch_allowed or r.commit_allowed)
    def test_handoff_proposal_no_authority(self):
        p=propose(ST,TEAM,R.task,'lead','seat-a','handoff');r=inspect_proposal(ST,TEAM,R.task,'lead','seat-a','handoff',p);self.assertTrue(r.structural_match);self.assertEqual(r.decision,'HOLD')
    def test_invalid_delegation(self):self.assertFalse(inspect_proposal(ST,TEAM,R.task,'seat-a','seat-b','delegation',None).structural_match)
    def test_same_department_handoff(self):self.assertFalse(inspect_proposal(ST,TEAM,R.task,'seat-a','seat-b','handoff',None).structural_match)
    def test_proposal_cannot_grant(self):
        p=replace(propose(ST,TEAM,R.task,'lead','seat-a','delegation'),decision='ALLOW');self.assertFalse(inspect_proposal(ST,TEAM,R.task,'lead','seat-a','delegation',p).structural_match)

if __name__=='__main__':unittest.main()
