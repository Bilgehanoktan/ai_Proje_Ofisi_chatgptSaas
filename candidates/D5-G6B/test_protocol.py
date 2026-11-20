"""G6B adapter control tests with simulated owner ports, NOT product acceptance."""
from dataclasses import dataclass, replace
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch


@dataclass(frozen=True)
class Review:
    reason: str
    structural_match: bool = False
    binding_sha: str | None = None
    decision: str = 'HOLD'
    commit_allowed: bool = False
    dispatch_allowed: bool = False
    retry_allowed: bool = False


@dataclass(frozen=True)
class Member:
    project_id: str = 'demo-project'
    plan_revision: str = 'sha256:' + 'a'*64
    task_id: str = 'research'
    agent: str = 'demo-agent'


@dataclass(frozen=True)
class IdentityReadback:
    member: Member = Member()
    scope: tuple = ('tenant', 'company', 'env')
    principal: str = 'demo-principal'


@dataclass(frozen=True)
class SessionReference:
    request: object


@dataclass(frozen=True)
class OrgReadback:
    role: str = 'research'
    seat: str = 'worker'


@dataclass(frozen=True)
class TaskHistory:
    task_id: str = 'research'
    version: int = 0
    role: str = 'research'


@dataclass(frozen=True)
class ResearchSliceReview:
    structural_match: bool = True
    decision: str = 'HOLD'
    freshness: str = 'HISTORICAL_SAMPLE'
    dispatch_allowed: bool = False
    release_ready: bool = False
    project_id: str = Member().project_id
    plan_revision: str = Member().plan_revision
    tasks: tuple = (TaskHistory(),)


@dataclass(frozen=True)
class BindingReview:
    structural_match: bool = True
    reason: str = 'D0_HISTORICAL_REFERENCE_MATCH_ONLY'
    decision: str = 'HOLD'
    freshness: str = 'HISTORICAL_SAMPLE'
    authoritative: bool = False
    runtime_binding: object = None
    dispatch_allowed: bool = False
    release_ready: bool = False
    org_revision: str = 'b'*64
    plan_revision: str = Member().plan_revision
    project_id: str = Member().project_id
    task_id: str = 'research'
    seat_id: str = 'worker'
    role: str = 'research'


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.sample = IdentityReadback()
        self.request = NS(project=Member().project_id, plan_revision=Member().plan_revision, task='research')
        self.core = Mock(return_value=ResearchSliceReview())
        self.bridge = Mock(return_value=BindingReview())
        self.reader = Mock(return_value=self.sample)
        def g5(*a, **kw):
            try: a[6]()
            except ValueError: return Review('D5G5_ORG_READBACK_HOLD')
            return Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY', True, 'c'*64)
        self.g5 = Mock(side_effect=g5)
        modules = {}
        def mod(name, **attrs):
            m = ModuleType(name); m.__dict__.update(attrs); modules[name] = m
        mod('app.core.transaction.identity_binding', Review=Review,
            digest=lambda v: type(v) is str and len(v)==64, valid_request=lambda v: v is self.request)
        mod('app.core.development_review.research_slice', inspect_research_slice=self.core, ResearchSliceReview=ResearchSliceReview)
        mod('app.core.event_store.plan_history_review', TaskHistory=TaskHistory)
        mod('app.core.event_store.company_coordination', Member=Member, _member=lambda m: type(m) is Member)
        mod('app.core.transaction.identity_fence_review', IdentityReadback=IdentityReadback, SessionReference=SessionReference)
        mod('app.core.transaction.intent_identity', derive_request=lambda *a: self.request)
        mod('app.core.transaction.org_membership_review', OrgReadback=OrgReadback, inspect_org_session_reference=self.g5)
        mod('org_core_bridge', BindingReview=BindingReview, review_research_binding=self.bridge)
        p=patch.dict(sys.modules, modules); p.start(); self.addCleanup(p.stop)
        path=Path(__file__).with_name('core_org_session_review.py')
        if not path.is_file(): path=Path(__file__).resolve().parents[2]/'product/ai-company-os-backend/app/core/transaction/core_org_session_review.py'
        spec=importlib.util.spec_from_file_location('g6b_under_test', path)
        self.adapter=importlib.util.module_from_spec(spec); spec.loader.exec_module(self.adapter)
        self.args=dict(cursor=object(),resolver=object(),credential='synthetic',intent=NS(expected_version=0),
            initial=self.sample,session=SessionReference(self.request),session_sha='d'*64,read_latest=self.reader,
            plan={},pins=(),members=(Member(),),pool=None,events=(),anchor=None,store=object(),
            org_reference=OrgReadback(),org_sha='e'*64,org_head='b'*64,seat='worker',history_pin=object(),
            root=object(),owner_pin='f'*64,domain='demo-clock')

    def invoke(self, **kw): return self.adapter.inspect_core_org_session_reference(**(self.args | kw))
    def hold(self, reason, **kw):
        r=self.invoke(**kw); self.assertEqual(r.reason,reason); self.assertFalse(r.structural_match)
        self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)

    def test_match_remains_hold(self):
        r=self.invoke(); self.assertTrue(r.structural_match); self.assertEqual(r.decision,'HOLD')
        self.assertFalse(r.commit_allowed or r.dispatch_allowed or r.retry_allowed)
        self.assertEqual(self.bridge.call_count,3); self.core.assert_called_once(); self.reader.assert_called_once()
        self.assertEqual(self.g5.call_args.kwargs['role'],'research')
    def test_wrong_session_request(self): self.hold('D5G6_CORE_ORG_REQUEST_HOLD',session=SessionReference(None))
    def test_duplicate_members(self): self.hold('D5G6_CORE_MEMBER_HOLD',members=(Member(),Member()))
    def test_forged_member(self): self.hold('D5G6_CORE_MEMBER_HOLD',members=(replace(Member(),agent='other'),))
    def test_core_reject(self):
        self.core.return_value=replace(ResearchSliceReview(),structural_match=False); self.hold('D5G6_CORE_READBACK_HOLD'); self.g5.assert_not_called()
    def test_wrong_version(self): self.hold('D5G6_CORE_TASK_ROLE_VERSION_HOLD',intent=NS(expected_version=1))
    def test_wrong_role(self): self.hold('D5G6_CORE_TASK_ROLE_VERSION_HOLD',org_reference=OrgReadback('qa'))
    def test_bool_version(self):
        self.core.return_value=replace(ResearchSliceReview(),tasks=(TaskHistory(version=False),)); self.hold('D5G6_CORE_TASK_ROLE_VERSION_HOLD')
    def test_bridge_grant_rejected(self):
        self.bridge.return_value=replace(BindingReview(),authoritative=True); self.hold('D5G6_HISTORICAL_JOIN_HOLD'); self.g5.assert_not_called()
    def test_member_drift(self):
        self.reader.return_value=IdentityReadback(replace(Member(),agent='other')); self.hold('D5G6_G5_REVIEW_HOLD')
    def test_final_bridge_drift(self):
        self.bridge.side_effect=[BindingReview(),BindingReview(),replace(BindingReview(),structural_match=False)]; self.hold('D5G6_HISTORICAL_JOIN_DRIFT_HOLD')
    def test_g5_unexpected_grant(self):
        self.g5.side_effect=None; self.g5.return_value=Review('D5G5_ORG_PROPOSAL_SESSION_MATCH_ONLY',True,'c'*64,commit_allowed=True); self.hold('D5G6_G5_REVIEW_HOLD')
    def test_unavailable_owner(self):
        self.core.side_effect=OSError('private path'); self.hold('D5G6_CORE_ORG_UNAVAILABLE_HOLD')


if __name__=='__main__': unittest.main(verbosity=2)
