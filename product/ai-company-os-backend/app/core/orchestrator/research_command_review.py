"""Non-normative CEO RESEARCH command binding for isolated D0 review."""
from dataclasses import dataclass
import json

from app.core.agent_runtime.lifecycle import token
from app.core.orchestrator.engine import canonical_plan
from app.core.task_engine.dag import valid_id
from app.core.transaction.review import digest_ok


_FIELDS = {"worktype", "project_ref", "plan_ref", "expected_plan_revision"}


class ResearchCommandError(ValueError):
    """A command cannot be bound to the server-selected plan."""


@dataclass(frozen=True)
class ResearchPlanBinding:
    project_ref: str
    plan_ref: str
    plan_revision: str
    plan_digest: str
    root_task_id: str


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchCommandError("COMMAND_DUPLICATE_FIELD")
        result[key] = value
    return result


def bind_research_command(
    body: bytes,
    idempotency_key: str,
    *,
    max_body_bytes: int,
    project_ref: str,
    approved_revision: str,
    retained_plan: dict,
) -> ResearchPlanBinding:
    """Compare draft input with server-selected pins and compile the existing D0 DAG.

    The caller supplies the limit and pins from trusted configuration and custody.
    This function only checks key syntax. Durable idempotency, IAM and admission
    must be established by their existing owners before a transport can use it.
    """
    if type(max_body_bytes) is not int or max_body_bytes < 1:
        raise ResearchCommandError("COMMAND_LIMIT_INVALID")
    if type(body) is not bytes or not 1 <= len(body) <= max_body_bytes:
        raise ResearchCommandError("COMMAND_BODY_SIZE_INVALID")
    if not token(idempotency_key):
        raise ResearchCommandError("COMMAND_KEY_INVALID")
    try:
        request = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object)
    except ResearchCommandError:
        raise
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ResearchCommandError("COMMAND_JSON_INVALID") from exc

    if (type(request) is not dict or set(request) != _FIELDS
            or request["worktype"] != "RESEARCH"
            or not valid_id(request["project_ref"])
            or not valid_id(request["plan_ref"])):
        raise ResearchCommandError("COMMAND_FIELDS_INVALID")
    revision = request["expected_plan_revision"]
    if not isinstance(revision, str) or not revision.startswith("sha256:") or not digest_ok(revision[7:]):
        raise ResearchCommandError("COMMAND_REVISION_INVALID")
    if revision != approved_revision or request["project_ref"] != project_ref:
        raise ResearchCommandError("COMMAND_PIN_MISMATCH")

    projection = canonical_plan(retained_plan)
    if projection["revision"] != revision or projection["plan_id"] != request["plan_ref"]:
        raise ResearchCommandError("COMMAND_PLAN_MISMATCH")

    roots = projection["waves"][0]
    if len(roots) != 1 or not any(
        task["id"] == roots[0] and task["role"] == "orchestrator"
        for task in projection["tasks"]
    ):
        raise ResearchCommandError("COMMAND_ROOT_INVALID")
    return ResearchPlanBinding(
        project_ref, projection["plan_id"], revision, projection["digest"], roots[0]
    )
