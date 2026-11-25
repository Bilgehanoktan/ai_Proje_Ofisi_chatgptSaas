"""Bind memory inspection to run, lease, ACL, tombstone and byte provenance.
All inputs are synthetic observations; matching is not authentication or retrieval.
"""
from dataclasses import dataclass
from app.core.agent_runtime.lifecycle import (
    Scope, RunObservation, RunState, valid_scope, uint, token, inspect_lease,
)
from app.core.t1_review import digest_ok
from app.engines.memory_engine.retrieval import (
    inspect_retrieval, RetrievalReview,
)
from app.engines.knowledge_engine.provenance import (
    SourceVersion, valid_source, inspect_span,
)


def inspect_run_memory(run, nodes, target, view, current):
    if not isinstance(run, RunObservation) or not valid_scope(run.scope):
        return RetrievalReview("RUN_SCOPE_HOLD")
    return inspect_retrieval(run.scope, nodes, target, view, current)


@dataclass(frozen=True)
class MemoryAclEntry:
    node_id: str
    revision: str
    digest: str
    decision: str


@dataclass(frozen=True)
class MemoryAclView:
    scope: Scope
    run_version: int
    run_attempt: int
    policy_epoch: int
    witness_epoch: int
    tombstone_epoch: int
    tombstone_sequence: int
    acl_revision: int
    complete: bool
    entries: tuple[MemoryAclEntry, ...]


@dataclass(frozen=True)
class MemoryAccessReview:
    reason: str
    structural_match: bool = False
    decision: str = "HOLD"
    retrieval_allowed: bool = False
    release_allowed: bool = False


def _valid_run(run):
    return (isinstance(run, RunObservation) and valid_scope(run.scope)
            and isinstance(run.state, RunState)
            and uint(run.version) and uint(run.attempt))


def _valid_acl(acl, run):
    if (not isinstance(acl, MemoryAclView) or acl.scope != run.scope
            or acl.complete is not True or not all(uint(v) for v in (
                acl.run_version, acl.run_attempt, acl.policy_epoch, acl.witness_epoch,
                acl.tombstone_epoch, acl.tombstone_sequence, acl.acl_revision))
            or acl.run_version != run.version or acl.run_attempt != run.attempt
            or not isinstance(acl.entries, tuple) or not 1 <= len(acl.entries) <= 512):
        return False
    seen = set()
    for entry in acl.entries:
        if (not isinstance(entry, MemoryAclEntry) or not token(entry.node_id)
                or not token(entry.revision) or not digest_ok(entry.digest)
                or type(entry.decision) is not str
                or entry.decision not in ("ALLOW_READ", "DENY_READ")
                or entry.node_id in seen):
            return False
        seen.add(entry.node_id)
    return True


def inspect_run_memory_access(run, expected_run, nodes, target, view, current,
                              acl, current_acl, lease, lease_reference, clock,
                              source, span, raw):
    """Review exact run and ancestor ACL pins before checking a supplied source span.

    No store, network, provider or content return. Both reference views require
    independent trusted acquisition before a future real retrieval can be authorized.
    """
    if (not _valid_run(run) or not _valid_run(expected_run)
            or run != expected_run or run.state is not RunState.RUNNING):
        return MemoryAccessReview("RUN_REFERENCE_HOLD")
    lease_review = inspect_lease(lease, lease_reference, clock)
    if lease_review.freshness != "FRESH" or lease.scope != run.scope:
        return MemoryAccessReview("MEMORY_LEASE_HOLD")
    lineage = inspect_run_memory(run, nodes, target, view, current)
    if lineage.reason != "D0_LINEAGE_MATCH_ONLY":
        return MemoryAccessReview(lineage.reason)
    if (not _valid_acl(acl, run) or not _valid_acl(current_acl, run)
            or acl != current_acl
            or (acl.policy_epoch, acl.witness_epoch) != (clock.policy_epoch, clock.witness_epoch)
            or (acl.tombstone_epoch, acl.tombstone_sequence) != (view.epoch, view.sequence)):
        return MemoryAccessReview("MEMORY_ACL_REFERENCE_HOLD")
    by_id = {node.node_id: node for node in nodes}
    closure = set()
    pending = [target]
    while pending:
        key = pending.pop()
        if key not in closure:
            closure.add(key)
            pending.extend(by_id[key].parents)
    grants = {entry.node_id: entry for entry in acl.entries}
    if set(grants) != closure:
        return MemoryAccessReview("MEMORY_ACL_COVERAGE_HOLD")
    for key in sorted(closure):
        node, entry = by_id[key], grants[key]
        if (entry.revision, entry.digest) != (node.revision, node.digest):
            return MemoryAccessReview("MEMORY_ACL_PIN_HOLD")
    if any(entry.decision == "DENY_READ" for entry in grants.values()):
        return MemoryAccessReview("MEMORY_ACL_DENY", decision="DENY")
    if (not isinstance(source, SourceVersion) or not valid_source(source)
            or source.scope != run.scope or source.source_id not in closure):
        return MemoryAccessReview("MEMORY_SOURCE_SCOPE_HOLD")
    node = by_id[source.source_id]
    if (source.revision, source.raw_digest) != (node.revision, node.digest):
        return MemoryAccessReview("MEMORY_SOURCE_PIN_HOLD")
    provenance = inspect_span(span, source, raw)
    if provenance != "D0_SPAN_MATCH_ONLY":
        return MemoryAccessReview(provenance)
    return MemoryAccessReview("D0_MEMORY_ACCESS_MATCH_ONLY", structural_match=True)
