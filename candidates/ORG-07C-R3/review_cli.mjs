import {readFileSync,statSync} from "node:fs";
import {createHash} from "node:crypto";
import {join} from "node:path";
import {TextDecoder} from "node:util";
import {reviewEvidence,runFixtureTests} from "./review_evidence.mjs";
const dir=process.argv[2];
try {
 if(dir==="--self-test"&&process.argv.length===3){console.log(JSON.stringify(runFixtureTests(),null,2));}
 else {
 if(!dir||process.argv.length!==3)throw Error("usage");
 const hashes={},values={};
 for(const name of ["report.json","original.log","additional.log"]){const file=join(dir,name);const st=statSync(file);if(!st.isFile()||st.size>65536)throw Error("size");const raw=readFileSync(file);if(raw.length>65536)throw Error("size");hashes[name]=createHash("sha256").update(raw).digest("hex");values[name]=new TextDecoder("utf-8",{fatal:true}).decode(raw);}
 const review=reviewEvidence(JSON.parse(values["report.json"]),values["original.log"],values["additional.log"]);console.log(JSON.stringify({...review,observed_sha256:hashes},null,2));process.exitCode=review.status==="REVIEW_MATCH_ONLY"?0:2;
 }
}catch{console.log(JSON.stringify({status:"HOLD",reason:"EVIDENCE_READ_OR_PARSE_FAILED",activation:"HOLD",canonical_IAM:"HOLD",independent:"HOLD",custody:"UNATTESTED",product_registration:"NOT_APPLIED"}));process.exitCode=2;}
