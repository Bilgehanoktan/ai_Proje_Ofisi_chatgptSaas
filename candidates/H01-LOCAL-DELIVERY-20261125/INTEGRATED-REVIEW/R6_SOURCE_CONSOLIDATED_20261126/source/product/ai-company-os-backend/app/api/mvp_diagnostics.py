"""D0 cross-engine synthetic readback. No grants, external calls or real commits."""
from app.core.orchestrator.engine import canonical_plan
from app.core.agent_runtime.lifecycle import Scope, RunObservation, RunState, inspect_transition
from app.core.agent_runtime.plan_binding import inspect_plan_binding
from app.core.event_store.ledger import replay_preview
from app.core.event_store.sqlite_preview import inspect_sqlite_replay
from app.core.policy.iv_review import ArtifactPin, TrustPlane, IVObservation, inspect_iv
from app.engines.model_gateway.registry import AdapterPin
from app.engines.model_gateway.fallback import inspect_fallback
from app.engines.model_gateway.gateway import DisabledModelGateway
from app.engines.skill_engine.manifest_review import SkillManifestSample
from app.engines.skill_engine.resolver import SourcePin, inspect_capabilities
from app.engines.budget_engine.reservation_review import BudgetSnapshot, ReservationRequest, inspect_reservation
from app.observability.finance_projection import project_finance


def inspect_mvp(sample: dict) -> dict:
    plan = canonical_plan(sample['plan'])
    task = next(t for t in plan['tasks'] if t['role'] == 'research')
    scope = Scope('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY', plan['revision'],
                  task['id'], 'demo-run', 'demo-agent', 'demo-principal')
    binding = inspect_plan_binding(plan, task['id'], task['role'])
    transition = inspect_transition(RunObservation(scope, RunState.CREATED, 0, 0), RunState.QUEUED, 0, None, None, None)
    replay = replay_preview(sample['events'], sample['layout'])
    storage = inspect_sqlite_replay(sample['events']) if replay['freshness'] == 'SAMPLE' else {'reason': 'REPLAY_HOLD', 'rows': None}
    digest = plan['digest']
    adapter = AdapterPin(scope, 'demo-model', 'v1', digest, ('demo-tool',), ())
    alternate = AdapterPin(scope, 'demo-fallback', 'v1', digest, ('demo-tool',), ())
    registry = (adapter, alternate)
    model = inspect_fallback(adapter, alternate, registry, ('demo-tool',), ())
    gateway = DisabledModelGateway().invoke(None)
    skill = SkillManifestSample(scope, 'demo-skill', 'v1', digest, digest, digest, ('demo-tool',))
    source = SourcePin('demo-source', 'v1', digest, 'demo-license', 'demo-custody')
    tools = inspect_capabilities(skill, skill, scope, source, source, adapter, registry, ('demo-tool',), ('demo-tool',))
    artifact = ArtifactPin(scope, digest, 0, 0, 0)
    plane = lambda name: TrustPlane(*(f'demo-{name}-{part}' for part in ('principal', 'root', 'admin', 'recovery')))
    iv = inspect_iv(IVObservation(artifact, artifact, plane('qa'), plane('iv'), plane('release')), artifact)
    budget = BudgetSnapshot(scope, 'demo-budget', 0, 'TRY', 10000, 1000, 2000, False, 0, 0, digest)
    request = ReservationRequest(scope, 'demo-budget', 0, 'TRY', 100, 'demo-reservation', 0, 0)
    reservation = inspect_reservation(request, budget, budget)
    finance = project_finance(reservation)
    # Never mask an unexpected effect/authority projection as a safe D0 result.
    if (plan['admission'] != 'DENY' or plan['dispatch_allowed'] is not False
            or plan['release_ready'] is not False or plan['real_run_count'] is not None
            or binding['binding_created'] is not False or binding['dispatch_allowed'] is not False
            or binding['run_id'] is not None or binding['agent_instance_id'] is not None
            or transition.commit_allowed is not False or transition.dispatch_allowed is not False
            or model.provider_call_allowed is not False or gateway.provider_call_allowed is not False
            or tools.enabled is not False or tools.effective_tools != ()
            or iv.independent_proven is not False or iv.receipt_issued is not False or iv.release_ready is not False
            or reservation.reservation_created is not False or reservation.spend_allowed is not False
            or any(value is not None for value in (finance.authorized_remaining_minor, finance.actual_cost_minor,
                                                   finance.revenue_minor, finance.collection_minor))
            or replay['persistent'] is not False or replay['verified'] is not False
            or (replay['freshness'] == 'SAMPLE' and any(storage.get(k) is not False
                for k in ('persistent', 'canonical_commit', 'dispatch_allowed')))):
        raise ValueError('D0_EFFECT_BOUNDARY_HOLD')
    return {'schema_version': 'mvp.diagnostics.v1-D0', 'mode': 'SYNTHETIC_LOCAL_ONLY',
            'plan_digest': digest, 'admission': 'DENY', 'dispatch_allowed': False,
            'release_ready': False, 'provider_called': False, 'spend_allowed': False,
            'independent_accepted': False, 'real_run_count': None,
            'sections': {'orchestrator': binding['reason'], 'runtime': transition.reason,
                         'event_store': storage['reason'], 'model': model.reason,
                         'gateway': gateway.reason, 'tools': tools.reason,
                         'verifier': iv.reason, 'finance': finance.status},
            'sample_event_rows': storage['rows'], 'diagnostic_remaining_minor': finance.diagnostic_remaining_minor,
            'actual_cost_minor': None, 'revenue_minor': None}
