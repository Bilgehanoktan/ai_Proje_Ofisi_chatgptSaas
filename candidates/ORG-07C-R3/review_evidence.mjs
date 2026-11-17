// Offline evidence structure review only; never grants authority.
const pins=Object.freeze({
  "commit": "17be56406408d572ebc66cf6fe7c1b6d83f18d76",
  "verified_blobs": 1739,
  "cryptography": "46.0.4",
  "additional_sha256": "69e68de19a7a86724ed430ba4f5c65da1963e651bc8dfa4fef965afc792459ed",
  "scope": "local synthetic SQLite only; no CI/PG/real IAM or acceptance"
});
const names=Object.freeze(["test_admitted_readback","test_gate_not_run","test_no_db_changes","test_org_notice_tamper","test_queued_readback","test_research_seat","test_stale_head","test_wrong_environment","test_wrong_history","test_wrong_member","test_wrong_seat"]);
function reviewEvidence(report, original, additional) {
 const result=(status,reason)=>({status,reason,custody:"UNATTESTED",activation:"HOLD",canonical_IAM:"HOLD",independent:"HOLD",product_registration:"NOT_APPLIED"});
 if(!report||typeof report!=="object"||Array.isArray(report)) return result("HOLD","REPORT_INVALID");
 if(report.commit!==pins.commit||report.scope!==pins.scope) return result("HOLD","SOURCE_OR_SCOPE_MISMATCH");
 if(report.status!=="PASS_LOCAL_SQLITE_ONLY") return result("HOLD","OWNER_RUN_NOT_PASS");
 for(const k of ["verified_blobs","cryptography","additional_sha256"]) if(report[k]!==pins[k]) return result("HOLD","PIN_MISMATCH_"+k);
 if(typeof report.python!=="string"||!/^3\.(12|13|14|15)\.\d+$/.test(report.python)||typeof report.sqlite!=="string"||!/^\d+\.\d+\.\d+$/.test(report.sqlite)) return result("HOLD","ENVIRONMENT_METADATA_INVALID");
 if(report.original!=="PASS"||report.additional!=="PASS"||report.original_returncode!==0||report.additional_returncode!==0) return result("HOLD","OWNER_SUITE_NOT_PASS");
 function checkLog(raw,expected,owner){
  if(typeof raw!=="string"||raw.length>65536||raw.includes("\0")) return false;
  const rows=raw.replace(/\r\n/g,"\n").split("\n").filter(s=>s!=="");
  if(rows.length!==expected.length+3) return false;
  const seen=[];
  for(const line of rows.slice(0,expected.length)){
   const name=line.split(" ")[0];
   if(line!==`${name} (${owner}.${name}) ... ok`) return false;
   seen.push(name);
  }
  const n=expected.length;
  return seen.sort().join("\n")===expected.slice().sort().join("\n") && /^-{70}$/.test(rows[n]) && new RegExp(`^Ran ${n} ${n===1?"test":"tests"} in \\d+\\.\\d+s$`).test(rows[n+1]) && rows[n+2]==="OK";
 }
 if(!checkLog(original,names,"__main__.CheckoutTests")) return result("HOLD","ORIGINAL_LOG_MISMATCH");
 if(!checkLog(additional,["test_operation_notice_tamper"],"__main__.main.<locals>.OperationNoticeTests")) return result("HOLD","ADDITIONAL_LOG_MISMATCH");
 return result("REVIEW_MATCH_ONLY","12_EXPECTED_SUCCESS_ROWS_UNATTESTED");
}
function runFixtureTests(){
 const r={...pins,status:"PASS_LOCAL_SQLITE_ONLY",python:"3.13.5",sqlite:"3.46.1",original:"PASS",additional:"PASS",original_returncode:0,additional_returncode:0};
 const fmt=(ns,c)=>ns.map(n=>`${n} (${c}.${n}) ... ok`).join("\n")+"\n\n"+"-".repeat(70)+`\nRan ${ns.length} ${ns.length===1?"test":"tests"} in 0.123s\n\nOK\n`;
 const o=fmt(names,"__main__.CheckoutTests"),a=fmt(["test_operation_notice_tamper"],"__main__.main.<locals>.OperationNoticeTests");
 const cases=[
 ["exact",r,o,a,"REVIEW_MATCH_ONLY"],["CRLF",r,o.replace(/\n/g,"\r\n"),a.replace(/\n/g,"\r\n"),"REVIEW_MATCH_ONLY"],
 ["blocked",{...r,status:"BLOCKED"},o,a,"HOLD"],["commit",{...r,commit:"0".repeat(40)},o,a,"HOLD"],["scope",{...r,scope:"production"},o,a,"HOLD"],["count",{...r,verified_blobs:1738},o,a,"HOLD"],["dependency",{...r,cryptography:"46.0.5"},o,a,"HOLD"],["extra pin",{...r,additional_sha256:"0".repeat(64)},o,a,"HOLD"],["environment",{...r,python:null},o,a,"HOLD"],["exit",{...r,original_returncode:1},o,a,"HOLD"],["boolean exit",{...r,original_returncode:false},o,a,"HOLD"],["not run",{...r,additional:"NOT_RUN"},o,a,"HOLD"],["missing log",r,null,a,"HOLD"],["missing extra",r,o,null,"HOLD"],["duplicate",r,o.replaceAll(names[0],names[1]),a,"HOLD"],["wrong name",r,o.replaceAll(names[0],"test_forged"),a,"HOLD"],["skip",r,o.replace("... ok","... skipped"),a,"HOLD"],["fail",r,o.replace("... ok","... FAIL"),a,"HOLD"],["wrong total",r,o.replace("Ran 11 tests","Ran 10 tests"),a,"HOLD"],["extra output",r,o+"unexpected\n",a,"HOLD"],["wrong class",r,o.replaceAll("CheckoutTests","ForgedTests"),a,"HOLD"],["wrong extra",r,o,a.replaceAll("test_operation_notice_tamper","test_forged"),"HOLD"],["oversize",r,"x".repeat(65537),a,"HOLD"],["null",null,o,a,"HOLD"]];
 const results=cases.map(([name,r,x,y,want])=>{const got=reviewEvidence(r,x,y);return {name,pass:got.status===want&&got.activation==="HOLD"&&got.canonical_IAM==="HOLD"&&got.custody==="UNATTESTED"&&got.independent==="HOLD"&&got.product_registration==="NOT_APPLIED",actual:got.status}});
 if(results.some(x=>!x.pass))throw Error(JSON.stringify(results)); return results;
}
export {reviewEvidence,runFixtureTests};
