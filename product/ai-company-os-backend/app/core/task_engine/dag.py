"""Pure graph validation and deterministic wave planning. Never schedules work."""
from dataclasses import dataclass
from typing import Iterable
import re

@dataclass(frozen=True)
class Task:
    id: str
    label: str
    role: str
    depends_on: tuple[str, ...]

ROLES = frozenset({"orchestrator", "research", "engineer", "qa", "independent-verifier", "human-authority"})

def valid_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,127}", value) is not None

class GraphError(ValueError):
    pass

def topological_waves(tasks: Iterable[Task]) -> tuple[tuple[str, ...], ...]:
    tasks = tuple(tasks)
    if not tasks or len(tasks) > 100:
        raise GraphError("TASK_COUNT_INVALID")
    if any(not isinstance(t, Task) or not valid_id(t.id) or not isinstance(t.role, str) or t.role not in ROLES
           or not isinstance(t.label, str) or not t.label.strip() or len(t.label) > 256
           or not isinstance(t.depends_on, tuple) or any(not valid_id(d) for d in t.depends_on) for t in tasks):
        raise GraphError("TASK_FIELD_INVALID")
    by_id = {t.id: t for t in tasks}
    if len(by_id) != len(tasks):
        raise GraphError("TASK_ID_OR_ROLE_INVALID")
    for t in tasks:
        if len(set(t.depends_on)) != len(t.depends_on) or t.id in t.depends_on:
            raise GraphError("DEPENDENCY_INVALID")
        if any(d not in by_id for d in t.depends_on):
            raise GraphError("DEPENDENCY_MISSING")
    remaining = set(by_id)
    done: set[str] = set()
    waves = []
    while remaining:
        wave = tuple(sorted(i for i in remaining if set(by_id[i].depends_on) <= done))
        if not wave:
            raise GraphError("DAG_CYCLE")
        waves.append(wave)
        remaining.difference_update(wave)
        done.update(wave)
    return tuple(waves)

def ancestors(task_id: str, tasks: tuple[Task, ...]) -> set[str]:
    by_id = {t.id:t for t in tasks}
    pending = list(by_id[task_id].depends_on)
    found: set[str] = set()
    while pending:
        node = pending.pop()
        if node not in found:
            found.add(node)
            pending.extend(by_id[node].depends_on)
    return found

def validate_release_boundary(tasks: tuple[Task, ...]) -> None:
    topological_waves(tasks)
    by_id = {t.id:t for t in tasks}
    release = [t for t in tasks if t.role == "human-authority"]
    if len(release) != 1:
        raise GraphError("RELEASE_BOUNDARY_MISSING")
    upstream = ancestors(release[0].id, tasks)
    if any(t.id not in upstream for t in tasks if t.id != release[0].id):
        raise GraphError("RELEASE_BYPASS")
    verifiers = [by_id[i] for i in upstream if by_id[i].role == "independent-verifier"]
    if len(verifiers) != 1:
        raise GraphError("IV_BOUNDARY_MISSING")
    iv_upstream = ancestors(verifiers[0].id, tasks)
    producers = {t.id for t in tasks if t.role in {"orchestrator", "research", "engineer", "qa"}}
    if not producers <= iv_upstream or not any(by_id[i].role == "qa" for i in iv_upstream):
        raise GraphError("QA_OR_PRODUCER_BYPASS")

    # Every non-QA producer must have a path through QA before IV.
    qa_ids = {t.id for t in tasks if t.role == "qa"}
    reviewed = set().union(*(ancestors(q, tasks) for q in qa_ids))
    if not (producers - qa_ids) <= reviewed:
        raise GraphError("PRODUCER_QA_BYPASS")
