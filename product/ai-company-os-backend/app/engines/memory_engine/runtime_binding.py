"""Bind memory lineage inspection to a specific run; no retrieval authority."""
from app.core.agent_runtime.lifecycle import RunObservation, valid_scope
from app.engines.memory_engine.retrieval import inspect_retrieval, RetrievalReview

def inspect_run_memory(run, nodes, target, view, current):
    if not isinstance(run, RunObservation) or not valid_scope(run.scope):
        return RetrievalReview("RUN_SCOPE_HOLD")
    return inspect_retrieval(run.scope, nodes, target, view, current)
