"""H01-MVP03-01: isolated D0 fixed-plan binding, never persistence or admission."""
from dataclasses import dataclass, field
import json
import hashlib

from app.core.agent_runtime.lifecycle import token
from app.core.orchestrator.engine import canonical_plan
from app.core.task_engine.dag import valid_id
from app.core.transaction.review import (digest_ok, WorkItemScopeDraft, WorkItemRequestDraft,
                                         inspect_workitem_request)


_FIELDS = {"worktype", "project_ref", "plan_ref", "expected_plan_revision"}
# Existing reviewed D0 fixture, not production plan approval or a public API limit.
_D0_PLAN_REF = "demo-plan-research"
_D0_PLAN_REVISION = "sha256:6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9"
_D0_MAX_BODY_BYTES = 4096


class ResearchCommandError(ValueError):
    """A command cannot be bound to the server-selected plan."""


@dataclass(frozen=True)
class ResearchPlanBinding:
    project_ref: str
    plan_ref: str
    plan_revision: str
    plan_digest: str
    root_task_id: str
    # Retain the validated opaque key for the future protected command service.
    # This is input binding only, not a durable fence or a request identifier.
    idempotency_key: str = field(repr=False)
    decision: str = field(default="HOLD", init=False)
    persistence_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)
    committed: bool = field(default=False, init=False)


    def to_workitem_draft(self, scope: WorkItemScopeDraft, *, project_revision: str,
                          worktype_version: str, workowner_ref: str) -> WorkItemRequestDraft:
        """Transfer D0 pins to T1 review, not authenticated scope or write authority."""
        if (type(scope) is not WorkItemScopeDraft or scope.project_ref != self.project_ref
                or self.plan_ref != _D0_PLAN_REF or self.plan_revision != _D0_PLAN_REVISION
                or self.root_task_id != 'plan'):
            raise ResearchCommandError("WORKITEM_BINDING_MISMATCH")
        draft = WorkItemRequestDraft(scope, project_revision, worktype_version, workowner_ref,
                                     self.plan_ref, self.plan_revision, self.plan_digest, self.idempotency_key)
        if not inspect_workitem_request(draft).structural_match:
            raise ResearchCommandError("WORKITEM_DRAFT_HOLD")
        return draft


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchCommandError("COMMAND_DUPLICATE_FIELD")
        result[key] = value
    return result


def _reject_constant(value):
    raise ResearchCommandError("COMMAND_NON_JSON_CONSTANT")


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

    The caller supplies observed project and plan pins, not authority. The D0
    cap and fixed fixture are source-review limits only. Durable idempotency,
    real HUMAN IAM, protected persistence and admission remain separate HOLD gates.
    A returned binding is not a receipt, grant or authorization.
    """
    if type(max_body_bytes) is not int or not 1 <= max_body_bytes <= _D0_MAX_BODY_BYTES:
        raise ResearchCommandError("COMMAND_LIMIT_INVALID")
    if type(body) is not bytes or not 1 <= len(body) <= max_body_bytes:
        raise ResearchCommandError("COMMAND_BODY_SIZE_INVALID")
    if not token(idempotency_key):
        raise ResearchCommandError("COMMAND_KEY_INVALID")
    try:
        request = json.loads(body.decode("utf-8"), object_pairs_hook=_unique_object,
                             parse_constant=_reject_constant)
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
    if (not valid_id(project_ref) or revision != approved_revision
            or request["project_ref"] != project_ref
            or request["plan_ref"] != _D0_PLAN_REF or revision != _D0_PLAN_REVISION):
        raise ResearchCommandError("COMMAND_PIN_MISMATCH")

    try:
        projection = canonical_plan(retained_plan)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise ResearchCommandError("COMMAND_PLAN_INVALID") from exc
    if (projection["revision"] != revision or projection["plan_id"] != request["plan_ref"]
            or projection["digest"] != revision[7:] or projection["admission"] != "DENY"
            or projection["dispatch_allowed"] is not False or projection["release_ready"] is not False):
        raise ResearchCommandError("COMMAND_PLAN_MISMATCH")

    roots = projection["waves"][0]
    if len(roots) != 1 or not any(
        task["id"] == roots[0] and task["role"] == "orchestrator"
        for task in projection["tasks"]
    ):
        raise ResearchCommandError("COMMAND_ROOT_INVALID")
    return ResearchPlanBinding(
        project_ref, projection["plan_id"], revision, projection["digest"], roots[0], idempotency_key
    )


@dataclass(frozen=True)
class ResearchPublicationCandidate:
    """Exact review candidate, never a publication decision or entitlement."""
    worktype_id: str
    version: str
    content_digest: str
    provenance_digest: str
    source_commit: str
    plan_revision: str
    package_digest: str
    decision: str = field(default="HOLD", init=False)
    published: bool = field(default=False, init=False)
    activation_allowed: bool = field(default=False, init=False)
    admission_allowed: bool = field(default=False, init=False)
    persistence_allowed: bool = field(default=False, init=False)


_RESEARCH_PUBLICATION_PACKAGE_SHA256 = "4c5f0b8ab9efa7e0525f1b5e3d2da1072fab8e6f219df2fe4f565605dfd2ce4e"


def bind_research_publication_draft(binding: ResearchPlanBinding, package: bytes,
                                    retained_plan: dict, scope: WorkItemScopeDraft, *,
                                    project_revision: str, workowner_ref: str
                                    ) -> tuple[ResearchPublicationCandidate, WorkItemRequestDraft]:
    """Bind only the exact reviewed A1 package to the existing D0 request seam.

    Package pins are immutable candidate identity, not live source attestation,
    H01 publication, current policy, authenticated IAM or protected COMMIT.
    No file I/O, grant, G8, admission, request ID or transaction is created.
    """
    if (type(package) is not bytes or len(package) != 4107
            or hashlib.sha256(package).hexdigest() != _RESEARCH_PUBLICATION_PACKAGE_SHA256):
        raise ResearchCommandError("PUBLICATION_PACKAGE_PIN_MISMATCH")
    if type(binding) is not ResearchPlanBinding:
        raise ResearchCommandError("PUBLICATION_BINDING_INVALID")
    value = json.loads(package.decode("utf-8"), object_pairs_hook=_unique_object,
                       parse_constant=_reject_constant)
    content, provenance = value["content"], value["provenance"]
    def digest(obj):
        return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()
    if (digest(content) != value["content_digest"] or digest(provenance) != value["provenance_digest"]
            or value["status"] != "REVIEW_CANDIDATE_NOT_PUBLISHED"
            or content["worktype_id"] != "RESEARCH"
            or content["plan_ref"] != _D0_PLAN_REF or content["plan_revision"] != _D0_PLAN_REVISION):
        raise ResearchCommandError("PUBLICATION_CONTENT_PIN_MISMATCH")
    try:
        projection = canonical_plan(retained_plan)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise ResearchCommandError("PUBLICATION_PLAN_INVALID") from exc
    if (projection["plan_id"], projection["revision"], projection["digest"]) != (
            binding.plan_ref, binding.plan_revision, binding.plan_digest) or (
            binding.plan_ref, binding.plan_revision) != (content["plan_ref"], content["plan_revision"]):
        raise ResearchCommandError("PUBLICATION_PLAN_PIN_MISMATCH")
    draft = binding.to_workitem_draft(scope, project_revision=project_revision,
                                      worktype_version=content["version"], workowner_ref=workowner_ref)
    return ResearchPublicationCandidate(content["worktype_id"], content["version"],
                                        value["content_digest"], value["provenance_digest"],
                                        provenance["source_commit"], content["plan_revision"],
                                        _RESEARCH_PUBLICATION_PACKAGE_SHA256), draft
