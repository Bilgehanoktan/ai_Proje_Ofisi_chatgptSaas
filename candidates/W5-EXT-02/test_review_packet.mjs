import { reviewPacket } from './review_packet.mjs';
function fixture() {
  return {task_id:"EXT02-1",base_sha:"a".repeat(40),observed_head:"b".repeat(40),plan_id:"plan-1",mode:"PLAN",isolation:"REVIEWED_ISOLATED",ownership:{status:"NO_CONFLICT_REPORTED",head_sha:"b".repeat(40),review_ref:"preflight-1"},steps:["PLAN","TDD","CODE_REVIEW","VERIFY","HANDOFF"],test:{status:"NOT_RUN",kind:"NONE",head_sha:null,report_sha256:null}};
}
function runCases() {
  const cases = [];
  const check=(name, mutate, status, reason)=>{
    const p=fixture(); const v=mutate(p); const result=reviewPacket(v===undefined?p:v);
    if(result.status!==status || result.reason!==reason || result.execution_authorized!==false || result.merge_authorized!==false || result.independent_acceptance!==false || result.evidence_verified!==false) throw Error(name+": "+JSON.stringify(result));
    cases.push({name,result:"PASS"});
  };
  const evidence=p=>{p.mode="HANDOFF";p.test={status:"PASS",kind:"SYNTHETIC",head_sha:p.observed_head,report_sha256:"c".repeat(64)};};
  check("valid plan remains advisory",()=>{},"PLAN_REVIEW_ONLY","NO_TEST_EVIDENCE");
  check("null packet",()=>null,"HOLD","PACKET_INVALID");
  check("unexpected authorization field",p=>{p.allow=true},"HOLD","PACKET_INVALID");
  check("invalid base",p=>{p.base_sha="main"},"HOLD","PACKET_INVALID");
  check("zero base",p=>{p.base_sha="0".repeat(40)},"HOLD","PACKET_INVALID");
  check("unsafe task id",p=>{p.task_id="../task"},"HOLD","PACKET_INVALID");
  check("unknown mode",p=>{p.mode="EXECUTE"},"HOLD","MODE_INVALID");
  check("shared directory fallback",p=>{p.isolation="SHARED"},"HOLD","ISOLATION_UNCONFIRMED");
  check("missing worktree review",p=>{p.isolation=null},"HOLD","ISOLATION_UNCONFIRMED");
  check("ownership conflict",p=>{p.ownership.status="CONFLICT"},"HOLD","OWNERSHIP_UNCONFIRMED");
  check("stale ownership head",p=>{p.ownership.head_sha=p.base_sha},"HOLD","OWNERSHIP_UNCONFIRMED");
  check("ownership grant injection",p=>{p.ownership.grant=true},"HOLD","OWNERSHIP_UNCONFIRMED");
  for(const step of ["MERGE","PUSH","DELETE","INSTALL","HOOK","NETWORK","SUBAGENT","CLEANUP"]) check("reject "+step,p=>{p.steps.push(step)},"HOLD","STEP_NOT_IN_GUIDANCE");
  check("duplicate steps",p=>{p.steps=["PLAN","PLAN"]},"HOLD","STEP_NOT_IN_GUIDANCE");
  check("plan must come first",p=>{p.steps=["TDD","PLAN"]},"HOLD","STEP_ORDER");
  check("handoff must include review",p=>{p.mode="HANDOFF";p.steps=["PLAN","VERIFY","HANDOFF"]},"HOLD","STEP_ORDER");
  check("handoff review before verify",p=>{p.mode="HANDOFF";p.steps=["PLAN","VERIFY","CODE_REVIEW","HANDOFF"]},"HOLD","STEP_ORDER");
  check("handoff without evidence",p=>{p.mode="HANDOFF"},"HOLD","NO_TEST_EVIDENCE");
  check("blocked test",p=>{p.mode="HANDOFF";p.test.status="BLOCKED"},"HOLD","NO_TEST_EVIDENCE");
  check("not run with fake report",p=>{p.test.report_sha256="c".repeat(64)},"HOLD","TEST_CLAIM_MISMATCH");
  check("pass with missing evidence",p=>{evidence(p);p.test.report_sha256=null},"HOLD","EVIDENCE_REFERENCE_INVALID");
  check("pass with stale head",p=>{evidence(p);p.test.head_sha=p.base_sha},"HOLD","EVIDENCE_REFERENCE_INVALID");
  check("pass with invalid digest",p=>{evidence(p);p.test.report_sha256="0".repeat(64)},"HOLD","EVIDENCE_REFERENCE_INVALID");
  check("actual provider test not allowed",p=>{evidence(p);p.test.kind="PROD"},"HOLD","EVIDENCE_REFERENCE_INVALID");
  check("reported failure",p=>{evidence(p);p.test.status="FAIL"},"HOLD","TEST_FAILED_REPORTED");
  check("synthetic pass is only reported",evidence,"EVIDENCE_REVIEW_ONLY","PASS_REPORTED_NOT_VERIFIED");
  check("product local pass is only reported",p=>{evidence(p);p.test.kind="PRODUCT_LOCAL"},"EVIDENCE_REVIEW_ONLY","PASS_REPORTED_NOT_VERIFIED");
  return cases;
}
const cases=runCases();
console.log(JSON.stringify({passed:cases.length,cases},null,2));
