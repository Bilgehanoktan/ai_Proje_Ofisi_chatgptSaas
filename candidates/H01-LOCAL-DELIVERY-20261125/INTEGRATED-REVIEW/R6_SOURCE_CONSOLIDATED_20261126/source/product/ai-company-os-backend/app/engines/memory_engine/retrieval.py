"""R10: bounded lineage closure and current tombstone review; no retrieval IO."""
from dataclasses import dataclass, fields
from ...core.runtime_preview import Scope, valid_scope, token, uint
from ...core.t1_review import digest_ok


@dataclass(frozen=True)
class Node:
    scope: Scope
    node_id: str
    revision: str
    digest: str
    parents: tuple[str, ...]


@dataclass(frozen=True)
class TombstoneView:
    scope: Scope
    epoch: int
    sequence: int
    keys: tuple[str, ...]
    complete: bool


@dataclass(frozen=True)
class RetrievalReview:
    reason: str
    stale_nodes: tuple[str, ...] = ()
    retrieval_allowed: bool = False
    release_allowed: bool = False
    deletion_receipt: None = None


def _exact_scope(scope: object) -> bool:
    # Compare only primitive values, never caller-defined equality/hash methods.
    return (type(scope) is Scope
            and all(type(getattr(scope, f.name)) is str for f in fields(Scope))
            and valid_scope(scope))


def _exact_token(value: object) -> bool:
    return type(value) is str and token(value)


def valid_keys(keys: object) -> bool:
    return (type(keys) is tuple and len(keys) <= 512
            and all(_exact_token(k) for k in keys) and len(set(keys)) == len(keys))


def valid_view(view: object, scope: Scope) -> bool:
    return (type(view) is TombstoneView and _exact_scope(scope)
            and _exact_scope(view.scope) and view.scope == scope
            and view.complete is True and uint(view.epoch) and uint(view.sequence)
            and valid_keys(view.keys))


def inspect_retrieval(scope: Scope, nodes: tuple[Node, ...], target: str,
                      view: TombstoneView, current: TombstoneView) -> RetrievalReview:
    if not _exact_scope(scope) or not _exact_token(target):
        return RetrievalReview('MEMORY_SCOPE_HOLD')
    if not valid_view(view, scope) or not valid_view(current, scope) or view != current:
        return RetrievalReview('TOMBSTONE_VIEW_UNKNOWN_HOLD')
    if type(nodes) is not tuple or not nodes or len(nodes) > 512:
        return RetrievalReview('LINEAGE_GRAPH_HOLD')
    if not all(type(n) is Node and _exact_scope(n.scope) and n.scope == scope
               and _exact_token(n.node_id) and _exact_token(n.revision)
               and type(n.digest) is str and digest_ok(n.digest) and valid_keys(n.parents) for n in nodes):
        return RetrievalReview('LINEAGE_SCOPE_OR_PIN_HOLD')
    by_id = {n.node_id: n for n in nodes}
    if len(by_id) != len(nodes) or target not in by_id or any(p not in by_id for n in nodes for p in n.parents):
        return RetrievalReview('LINEAGE_ORPHAN_OR_DUPLICATE_HOLD')
    remaining = set(by_id)
    done: set[str] = set()
    stale = set(view.keys)
    while remaining:
        ready = {k for k in remaining if set(by_id[k].parents) <= done}
        if not ready:
            return RetrievalReview('LINEAGE_CYCLE_HOLD')
        stale.update(k for k in ready if set(by_id[k].parents) & stale)
        done.update(ready)
        remaining.difference_update(ready)
    affected = tuple(sorted(stale & set(by_id)))
    if target in stale:
        return RetrievalReview('STALE_HOLD', affected)
    return RetrievalReview('D0_LINEAGE_MATCH_ONLY', affected)
