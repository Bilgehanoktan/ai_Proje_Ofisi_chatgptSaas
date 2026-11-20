"""Local synthetic guards for source-pinned, fail-closed MI-P0 release evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).with_name("verify_release_readiness.py")
spec = importlib.util.spec_from_file_location("release_gate", MODULE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
SHA = "a" * 40
MAN = "b" * 40
TREE = "c" * 40
PRLIST = [10, 19, 20, 21, 22, 23, 24]


def samples():
    current = {"product_dev": {"ref": "integration/product-dev", "sha": SHA,
              "product_files": 553, "manifest_entries": 552, "manifest_blob": MAN,
              "source_product_tree": TREE},
              "program_global_snapshot_20261120": {"base_source_sha": SHA}}
    snapshot = {"source": {"canonical_sha": SHA, "canonical_manifest_blob": MAN, "canonical_tree": TREE},
                "formal_progress": {"approved_group_denominators": 0, "draft_stage_slots": 315, "current_percent": None},
                "groups": [{}]*10, "phases": [{}]*8, "mvp_crosswalk": [{}]*11,
                "legacy_tracker_24": {"rows": [{}]*24},
                "owner_prs": [{"number": i, "head_sha": SHA} for i in [10,19,20,21,22]]}
    evidence = {"canonical_sha": SHA, "office_qa_source_pr22_head": SHA,
                "observed_prs": [{"number": i, "head_sha": SHA, "state":"open", "draft": True} for i in PRLIST],
                "gates": {key: {"status": "HOLD", "owner": "MI-P0", "reason": "Unapproved"} for key in gate.REQUIRED_GATES},
                "test_counters": {"office_owner_local": [6,6], "office_independent_stalled": [0,3], "g7_current_org": [0,7]},
                "mvp_acceptance": [0,11], "independent_iv_acceptance": [0,7], "owner_final_approval": False}
    evidence["gates"]["office_stalled_transport"]["status"] = "FAIL"
    evidence["gates"]["g2_g9_current_org_regression"]["status"] = "NOT_RUN"
    return current,snapshot,evidence


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.current,self.snapshot,self.evidence=samples()

    def invalid(self, text):
        with self.assertRaises(gate.EvidenceError) as err:
            gate.audit(self.current,self.snapshot,self.evidence)
        self.assertIn(text,str(err.exception))

    def test_still_hold_despite_local_office_green(self):
        report=gate.audit(self.current,self.snapshot,self.evidence)
        self.assertEqual(report["evidence_status"],"VERIFIED_HOLD")
        self.assertFalse(report["release_approved"])
        self.assertIn("office_stalled_transport", {q["gate"] for q in report["blockers"]})
        self.assertIn("dashboard_pr_freshness", {q["gate"] for q in report["blockers"]})

    def test_independent_qa_old_head_remains_hold(self):
        self.evidence["observed_prs"][4]["head_sha"] = "d"*40
        self.snapshot["owner_prs"][4]["head_sha"] = "d"*40
        report=gate.audit(self.current,self.snapshot,self.evidence)
        self.assertIn("office_qa_candidate_freshness",{q["gate"] for q in report["blockers"]})

    def test_canonical_sha_mismatch_fail(self):
        self.evidence["canonical_sha"] = "d"*40
        self.invalid("canonical pin mismatch")

    def test_manifest_mismatch_fail(self):
        self.snapshot["source"]["canonical_manifest_blob"] = "d"*40
        self.invalid("manifest")

    def test_tree_mismatch_fail(self):
        self.snapshot["source"]["canonical_tree"] = "d"*40
        self.invalid("tree")

    def test_unsigned_overall_percent_fail(self):
        self.snapshot["formal_progress"]["current_percent"] = 90
        self.invalid("unratified")

    def test_missing_required_gate_fail(self):
        self.evidence["gates"].pop("independent_iv")
        self.invalid("required gate names mismatch")

    def test_implicit_green_state_fail(self):
        self.evidence["gates"]["protected_postgres_restore"]["status"] = None
        self.invalid("invalid/non-explicit")

    def test_missing_pr23_fail(self):
        self.evidence["observed_prs"] = [p for p in self.evidence["observed_prs"] if p["number"]!=23]
        self.invalid("missing live")

    def test_closed_pr_refuse(self):
        self.evidence["observed_prs"][1]["state"]="closed"
        self.invalid("not an open")

    def test_owner_pr_head_changed_fail(self):
        self.evidence["observed_prs"][1]["head_sha"] = "d"*40
        self.invalid("stale head")

    def test_owner_green_does_not_override_independent_fail(self):
        self.evidence["gates"]["office_stalled_transport"]["status"] = "PASS"
        self.invalid("independent FAIL")

    def test_current_org_runner_not_run_cannot_be_pass(self):
        self.evidence["gates"]["g2_g9_current_org_regression"]["status"] = "PASS"
        self.invalid("unexecuted current ORG")

    def test_independent_negatives_not_double_counted(self):
        self.evidence["test_counters"]["office_independent_stalled"] = [6,6]
        self.invalid("unreviewed change")

    def test_missing_owner_approval_is_error(self):
        self.evidence["owner_final_approval"] = True
        self.invalid("owner approval")

    def test_missing_scope_not_allowed(self):
        self.snapshot["mvp_crosswalk"].pop()
        self.invalid("coverage mismatch")

    def test_missing_pinned_dashboard_pointer(self):
        self.current.pop("program_global_snapshot_20261120")
        self.invalid("current.program_global_snapshot")

    def test_duplicate_pr_rejected(self):
        self.evidence["observed_prs"].append(copy.deepcopy(self.evidence["observed_prs"][0]))
        self.invalid("duplicate PR")

    def test_not_ready_returns_two(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[]
            for i,obj in enumerate((self.current,self.snapshot,self.evidence)):
                path=Path(d)/f"{i}.json";path.write_text(json.dumps(obj));paths.append(path)
            with patch("builtins.print"):
                status=gate.main(["--current",str(paths[0]),"--snapshot",str(paths[1]),"--evidence",str(paths[2]),"--require-review-eligible"])
            self.assertEqual(status,2)

    def test_valid_audit_writes_json(self):
        with tempfile.TemporaryDirectory() as d:
            paths=[]
            for i,obj in enumerate((self.current,self.snapshot,self.evidence)):
                path=Path(d)/f"{i}.json";path.write_text(json.dumps(obj));paths.append(path)
            out=Path(d)/"report.json"
            with patch("builtins.print"):
                status=gate.main(["--current",str(paths[0]),"--snapshot",str(paths[1]),"--evidence",str(paths[2]),"--json-out",str(out)])
            self.assertEqual(status,0)
            self.assertFalse(json.loads(out.read_text())["release_approved"])

if __name__=="__main__": unittest.main(verbosity=2)
