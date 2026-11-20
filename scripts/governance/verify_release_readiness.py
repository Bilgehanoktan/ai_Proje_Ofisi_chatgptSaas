#!/usr/bin/env python3
"""Fail-closed, read-only AI Company OS central release evidence gate.

This is NOT independent verification, a deployment control, or an authorization
service. It only checks whether owner-supplied, source-pinned evidence is
complete enough for a separate release-approval review. No network or effects.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MANDATORY_PRS = (10, 19, 20, 21, 22, 23, 24, 26)
REQUIRED_GATES = (
    "w8_exact_prepare", "supply_chain_owner_review", "w8_full_install_build_browser",
    "g2_g9_current_org_regression", "authority_root_sink_custody",
    "protected_postgres_restore", "independent_iv", "office_stalled_transport",
    "eleven_mvp_criteria",
)
ALLOWED_STATES = {"PASS", "FAIL", "HOLD", "NOT_RUN"}
NONFINAL_OWNER_PASS = "PASS"


class EvidenceError(ValueError):
    """Malformed, incomplete, stale or incompatible evidence."""


def _object(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise EvidenceError(f"{label}: expected object")
    return value


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise EvidenceError(f"{label}: invalid full Git SHA")
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise EvidenceError(f"{label}: invalid SHA-256")
    return value


def _source_receipt(value: object, label: str, source_head: str) -> None:
    receipt = _object(value, label)
    if _sha(receipt.get("tested_source_head"), f"{label}.tested_source_head") != source_head:
        raise EvidenceError(f"{label}: tested source head mismatch")
    _digest(receipt.get("raw_log_sha256"), f"{label}.raw_log_sha256")


def _pairs(value: object, label: str) -> tuple[int, int]:
    if (not isinstance(value, list) or len(value) != 2 or
        any(type(x) is not int or x < 0 for x in value) or value[1] == 0 or value[0] > value[1]):
        raise EvidenceError(f"{label}: expected [passed,total] with 0<=passed<=total")
    return value[0], value[1]


def audit(current: object, snapshot: object, evidence: object) -> dict:
    """Return a verified HOLD/REVIEW_CANDIDATE report or raise EvidenceError.

    Passing this audit does NOT grant release authorization.
    """
    c = _object(current, "current")
    s = _object(snapshot, "snapshot")
    e = _object(evidence, "evidence")
    product = _object(c.get("product_dev"), "current.product_dev")
    source = _object(s.get("source"), "snapshot.source")
    p = _sha(product.get("sha"), "current.product_dev.sha")
    for label, value in (
        ("snapshot.source.canonical_sha", source.get("canonical_sha")),
        ("evidence.canonical_sha", e.get("canonical_sha")),
    ):
        if _sha(value, label) != p:
            raise EvidenceError(f"{label}: canonical pin mismatch")
    if product.get("ref") != "integration/product-dev" or product.get("product_files") != 553:
        raise EvidenceError("unexpected canonical product ref/file count; repin after new owner review")
    if product.get("manifest_entries") != 552:
        raise EvidenceError("canonical manifest entry count mismatch")
    if _sha(product.get("manifest_blob"), "product.manifest_blob") != _sha(source.get("canonical_manifest_blob"), "snapshot.manifest"):
        raise EvidenceError("canonical manifest does not match snapshot")
    if source.get("canonical_tree") != product.get("source_product_tree"):
        raise EvidenceError("product Git tree differs from snapshot")
    progress = _object(s.get("formal_progress"), "snapshot.formal_progress")
    if progress.get("approved_group_denominators") != 0 or progress.get("draft_stage_slots") != 315:
        raise EvidenceError("program denominator revision changed; redo scope and owner approval")
    if progress.get("current_percent") is not None:
        raise EvidenceError("unratified denominator cannot create an overall development percent")
    if [len(s.get("groups", [])), len(s.get("phases", [])), len(s.get("mvp_crosswalk", []))] != [10, 8, 11]:
        raise EvidenceError("program group/phase/MVP coverage mismatch")
    if len(_object(s.get("legacy_tracker_24"), "legacy_tracker_24").get("rows", [])) != 24:
        raise EvidenceError("24-area tracker incomplete")
    accepted = _object(c.get("program_global_snapshot_20261120"), "current.program_global_snapshot_20261120")
    if _sha(accepted.get("base_source_sha"), "central pointer") != p:
        raise EvidenceError("central dashboard pointer uses a different canonical source")

    observed = e.get("observed_prs")
    if not isinstance(observed, list):
        raise EvidenceError("observed_prs missing")
    seen = {}
    for pr in observed:
        row = _object(pr, "observed_prs[]")
        n = row.get("number")
        if type(n) is not int or n in seen:
            raise EvidenceError("invalid/duplicate PR number")
        _sha(row.get("head_sha"), f"PR #{n} head")
        if row.get("state") != "open" or row.get("draft") is not True:
            raise EvidenceError(f"PR #{n} is not an open owner-held draft")
        seen[n] = row
    missing = set(MANDATORY_PRS) - set(seen)
    if missing:
        raise EvidenceError(f"missing live owner/QA observations: {sorted(missing)}")
    qa_head = _sha(e.get("office_qa_source_pr22_head"), "office QA tested PR22 head")
    # Stale dashboard is HOLD, not an exception: report every stale owner pin.
    snapshot_prs = s.get("owner_prs")
    if not isinstance(snapshot_prs, list):
        raise EvidenceError("snapshot.owner_prs missing")
    snapshot_numbers = set()
    stale_snapshot_heads = []
    for row in snapshot_prs:
        data = _object(row, "snapshot.owner_prs[]")
        n = data.get("number")
        if type(n) is not int or n in snapshot_numbers or n not in seen:
            raise EvidenceError(f"snapshot PR #{n}: duplicate or missing live observation")
        snapshot_numbers.add(n)
        if _sha(data.get("head_sha"), f"snapshot PR #{n}") != seen[n]["head_sha"]:
            stale_snapshot_heads.append(n)

    gates = _object(e.get("gates"), "evidence.gates")
    if set(gates) != set(REQUIRED_GATES):
        raise EvidenceError(f"required gate names mismatch: absent {sorted(set(REQUIRED_GATES)-set(gates))}")
    blockers = []
    for key in REQUIRED_GATES:
        entry = _object(gates[key], f"gates.{key}")
        state = entry.get("status")
        if state not in ALLOWED_STATES:
            raise EvidenceError(f"gates.{key}: invalid/non-explicit state")
        if not isinstance(entry.get("owner"), str) or not entry["owner"].strip():
            raise EvidenceError(f"gates.{key}: owner required")
        if state != NONFINAL_OWNER_PASS:
            blockers.append({"gate": key, "status": state, "owner": entry["owner"], "reason": entry.get("reason", "")})
    counts = _object(e.get("test_counters"), "evidence.test_counters")
    owner_office = _pairs(counts.get("office_owner_local"), "owner Office")
    independent_office = _pairs(counts.get("office_independent_stalled"), "independent Office")
    g7 = _pairs(counts.get("g7_current_org"), "current ORG G7")
    if owner_office != (6, 6) or independent_office[1] != 3 or g7[1] != 7:
        raise EvidenceError("unreviewed change in test evidence baseline; rerun/repin actual evidence")
    office_status = gates["office_stalled_transport"]["status"]
    office_fresh = qa_head == seen[22]["head_sha"]
    if office_status == "PASS":
        if independent_office != (3, 3) or not office_fresh:
            raise EvidenceError("independent FAIL or stale head cannot become Office PASS")
        _source_receipt(e.get("office_independent_receipt"), "office_independent_receipt", seen[22]["head_sha"])
        receipt = e["office_independent_receipt"]
        if _sha(receipt.get("qa_pr_head"), "office_independent_receipt.qa_pr_head") != seen[23]["head_sha"]:
            raise EvidenceError("Office receipt QA PR23 head mismatch")
    elif independent_office != (3, 3) and office_status not in ("FAIL", "HOLD", "NOT_RUN"):
        raise EvidenceError("Office test evidence/status inconsistent")
    g7_status = gates["g2_g9_current_org_regression"]["status"]
    if g7_status == "PASS":
        if g7 != (7, 7):
            raise EvidenceError("unexecuted current ORG G7 cannot become PASS")
        _source_receipt(e.get("g7_current_org_receipt"), "g7_current_org_receipt", seen[19]["head_sha"])
    elif g7 != (0, 7) and g7_status not in ("FAIL", "HOLD", "NOT_RUN"):
        raise EvidenceError("current ORG test evidence/status inconsistent")
    mvp = _pairs(e.get("mvp_acceptance"), "MVP")
    iv = _pairs(e.get("independent_iv_acceptance"), "IV")
    if mvp[1] != 11 or iv[1] != 7:
        raise EvidenceError("MVP/IV canonical acceptance denominator changed")
    if mvp != (0, 11):
        _source_receipt(e.get("mvp_acceptance_receipt"), "mvp_acceptance_receipt", p)
    if iv != (0, 7):
        _source_receipt(e.get("independent_iv_receipt"), "independent_iv_receipt", p)
    if gates["eleven_mvp_criteria"]["status"] == "PASS" and mvp != (11, 11):
        raise EvidenceError("MVP PASS without eleven accepted criteria")
    if gates["independent_iv"]["status"] == "PASS" and iv != (7, 7):
        raise EvidenceError("IV PASS without seven independently accepted criteria")
    if e.get("owner_final_approval") is not False:
        raise EvidenceError("owner approval cannot be inferred; separate signed acceptance required")
    if not office_fresh:
        blockers.append({"gate": "office_qa_candidate_freshness", "status": "HOLD",
                         "owner": "MI-05/QA", "reason": "Independent QA evidence covers previous PR22 head, current candidate NOT_RETESTED"})
    if stale_snapshot_heads:
        blockers.append({"gate": "dashboard_head_freshness", "status": "HOLD", "owner": "MI-P0",
                         "reason": "Snapshot PR heads differ from live owners: " + str(sorted(stale_snapshot_heads))})
    stale_dashboard_prs = sorted(set(MANDATORY_PRS) - snapshot_numbers)
    if stale_dashboard_prs:
        blockers.append({"gate": "dashboard_pr_freshness", "status": "HOLD", "owner": "MI-P0",
                         "reason": "Snapshot omits owner/QA PRs: " + str(stale_dashboard_prs)})
    return {
        "evidence_status": "VERIFIED_HOLD" if blockers else "ELIGIBLE_FOR_SEPARATE_OWNER_REVIEW_ONLY",
        "release_approved": False,
        "canonical_sha": p,
        "blockers": blockers,
        "checked_owner_prs": list(MANDATORY_PRS),
        "owner_local_office": list(owner_office),
        "independent_stalled_office": list(independent_office),
        "current_org_g7": list(g7),
        "mvp_acceptance": list(mvp),
        "independent_iv_acceptance": list(iv),
        "note": "Read-only evidence evaluation, NOT an authorized CI, IV, security or product release verdict",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--require-review-eligible", action="store_true",
                        help="Exit nonzero when any blocker remains; no authorizations granted")
    args = parser.parse_args(argv)
    try:
        files = [json.loads(path.read_text(encoding="utf-8")) for path in (args.current, args.snapshot, args.evidence)]
        result = audit(*files)
        output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.json_out:
            args.json_out.write_text(output, encoding="utf-8")
        print(output, end="")
        return 2 if args.require_review_eligible and result["evidence_status"] != "ELIGIBLE_FOR_SEPARATE_OWNER_REVIEW_ONLY" else 0
    except (EvidenceError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"evidence_status": "ERROR_FAIL_CLOSED", "release_approved": False, "error": str(exc)}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    sys.exit(main())
