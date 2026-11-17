/** EXT-02: advisory task packet lint; pure JSON input, no side effects. Not a policy engine or evidence verifier. */
function reviewPacket(p) {
  const out = (status, reason) => ({status, reason, execution_authorized:false, merge_authorized:false, independent_acceptance:false, evidence_verified:false});
  const shape = (v, keys) => v !== null && typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === keys.length && keys.every(k => Object.prototype.hasOwnProperty.call(v,k));
  const id = v => typeof v === "string" && /^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/.test(v);
  const sha = v => typeof v === "string" && /^[0-9a-f]{40}$/.test(v) && !/^0+$/.test(v);
  const digest = v => typeof v === "string" && /^[0-9a-f]{64}$/.test(v) && !/^0+$/.test(v);
  const top = ["task_id","base_sha","observed_head","plan_id","mode","isolation","ownership","steps","test"];
  if (!shape(p,top) || !id(p.task_id) || !id(p.plan_id) || !sha(p.base_sha) || !sha(p.observed_head)) return out("HOLD","PACKET_INVALID");
  if (!["PLAN","HANDOFF"].includes(p.mode)) return out("HOLD","MODE_INVALID");
  if (p.isolation !== "REVIEWED_ISOLATED") return out("HOLD","ISOLATION_UNCONFIRMED");
  if (!shape(p.ownership,["status","head_sha","review_ref"]) || p.ownership.status !== "NO_CONFLICT_REPORTED" || p.ownership.head_sha !== p.observed_head || !id(p.ownership.review_ref)) return out("HOLD","OWNERSHIP_UNCONFIRMED");
  const allowed = ["PLAN","TDD","ROOT_CAUSE","CODE_REVIEW","VERIFY","HANDOFF"];
  if (!Array.isArray(p.steps) || p.steps.length === 0 || p.steps.length > allowed.length || p.steps.some(s=>!allowed.includes(s)) || new Set(p.steps).size !== p.steps.length) return out("HOLD","STEP_NOT_IN_GUIDANCE");
  if (p.steps[0] !== "PLAN" || (p.mode === "HANDOFF" && (p.steps[p.steps.length-1] !== "HANDOFF" || !p.steps.includes("VERIFY") || !p.steps.includes("CODE_REVIEW") || p.steps.indexOf("CODE_REVIEW") > p.steps.indexOf("VERIFY")))) return out("HOLD","STEP_ORDER");
  const t=p.test;
  if (!shape(t,["status","kind","head_sha","report_sha256"])) return out("HOLD","TEST_SHAPE");
  if (!["NOT_RUN","BLOCKED","PASS","FAIL"].includes(t.status)) return out("HOLD","TEST_STATUS");
  if (["NOT_RUN","BLOCKED"].includes(t.status)) {
    if (t.kind !== "NONE" || t.head_sha !== null || t.report_sha256 !== null) return out("HOLD","TEST_CLAIM_MISMATCH");
    return out(p.mode==="PLAN" ? "PLAN_REVIEW_ONLY" : "HOLD","NO_TEST_EVIDENCE");
  }
  if (!["SYNTHETIC","PRODUCT_LOCAL"].includes(t.kind) || t.head_sha !== p.observed_head || !digest(t.report_sha256)) return out("HOLD","EVIDENCE_REFERENCE_INVALID");
  if (t.status === "FAIL") return out("HOLD","TEST_FAILED_REPORTED");
  return out("EVIDENCE_REVIEW_ONLY","PASS_REPORTED_NOT_VERIFIED");
}
export { reviewPacket };
