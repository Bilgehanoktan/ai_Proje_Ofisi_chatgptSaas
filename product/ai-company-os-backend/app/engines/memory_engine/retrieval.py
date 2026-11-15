"""R10: bounded lineage closure and current tombstone review; no retrieval IO."""
from dataclasses import dataclass
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


def valid_keys(keys: object) -> bool:
    return (isinstance(keys, tuple) and len(keys) <= 512
            and all(token(k) for k in keys) and len(set(keys)) == len(keys))


def valid_view(view: object, scope: Scope) -> bool:
    return (isinstance(view, TombstoneView) and view.scope == scope
            and view.complete is True and uint(view.epoch) and uint(view.sequence)
            and valid_keys(view.keys))


def inspect_retrieval(scope: Scope, nodes: tuple[Node, ...], target: str,
                      view: TombstoneView, current: TombstoneView) -> RetrievalReview:
    if not valid_scope(scope) or not token(target):
        return RetrievalReview('MEMORY_SCOPE_HOLD')
    if not valid_view(view, scope) or not valid_view(current, scope) or view != current:
        return RetrievalReview('TOMBSTONE_VIEW_UNKNOWN_HOLD')
    if not isinstance(nodes, tuple) or not nodes or len(nodes) > 512:
        return RetrievalReview('LINEAGE_GRAPH_HOLD')
    if not all(isinstance(n, Node) and n.scope == scope and token(n.node_id) and token(n.revision)
               and digest_ok(n.digest) and valid_keys(n.parents) for n in nodes):
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
