"""Fixed, deterministic review DAG; deliberately separate from the RESEARCH worktype."""
from dataclasses import dataclass, asdict
from .model import PROFILE, ReviewScope, PrincipalPin, digest, scope_digest, valid_scope, valid_roster


@dataclass(frozen=True)
class ReviewTask:
    id: str
    role: str
    depends_on: tuple[str, ...]


TASKS = (
    ReviewTask('plan', 'orchestrator', ()),
    ReviewTask('requirements', 'research', ('plan',)),
    ReviewTask('candidate', 'engineer', ('requirements',)),
    ReviewTask('quality', 'qa', ('candidate',)),
    ReviewTask('security', 'security', ('candidate',)),
    ReviewTask('verify', 'independent-verifier', ('quality', 'security')),
    ReviewTask('gate-review', 'policy-review', ('verify',)),
)
WAVES = (('plan',), ('requirements',), ('candidate',), ('quality', 'security'), ('verify',), ('gate-review',))


@dataclass(frozen=True)
class ReviewPlan:
    scope_sha256: str
    roster: tuple[PrincipalPin, ...]
    tasks: tuple[ReviewTask, ...]
    waves: tuple[tuple[str, ...], ...]
    plan_sha256: str


def compile_review(s: ReviewScope, roster: tuple[PrincipalPin, ...]) -> ReviewPlan:
    if not valid_scope(s) or not valid_roster(roster):
        raise ValueError('REVIEW_PLAN_SCOPE_OR_SOD_INVALID')
    body = {'profile': PROFILE, 'scope_sha256': scope_digest(s),
            'roster': [asdict(p) for p in roster], 'tasks': [asdict(t) for t in TASKS], 'waves': WAVES}
    return ReviewPlan(scope_digest(s), roster, TASKS, WAVES, digest(body))


def valid_plan(p: object, s: ReviewScope) -> bool:
    return (type(p) is ReviewPlan and valid_scope(s) and valid_roster(p.roster)
            and p == compile_review(s, p.roster))
