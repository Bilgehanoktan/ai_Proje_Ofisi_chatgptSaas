# DOC-REV-0227 — MVP environment preflight (BLOCKED)

Pinned 0226 parent c715e1edfd1af021b4c0be0681c6958455b6a26f. No runtime/product changes, no new prototype or tests. Existing CEO-0174/0179=B boundary remains unchanged. Repo branch readback, exact manifest path/size 392/392, no missing/extra; 393 product files; 1571 repo blob paths. Historical lock at 614aa63efbd0a95d0fa5fe47390df043d773370f: 55/55 Git blob and size matches remotely, current source 52/55 (three expected changed paths), no local source execution. See [environment evidence](../../tests/evidence/TEST_EVIDENCE_0227.json).

Local network probes: git DNS failure exit 128, pip dry-run exit 1 and npm registry metadata exit 1; separate DNS queries all exit 2. Published exact versions were found on public package indexes, so the local resolver error does not prove the pins are unavailable. No transitive lock, installation, PostgreSQL, full checkout or build produced. The existing 307 selected passes are historical 0226 only, not rerun. A3, D1-D3, E1-E4 open, B3 HOLD. 7/16 unchanged. Do not substitute new package pins, change historical lock or infer independent acceptance.

Operational next: [connected workstation runbook](CONNECTED_WORKSTATION_0227.md). Execute source/lock preparation and original residual suites in an actual connected authorized isolated environment, then PG and build/browser. No new user-level authorization requested. No CI or main changes. This revision does not represent a working MVP.


## 0227-A3 — scoped historical evidence transfer
A3 only: 29/29 historical locked tests from pinned A0F review `6140e16edb2ddd943912908f3714ccd3a211b1d3`, actual A0C source `a79df6622e2eb9de63795ff6c0309984d1be6910`; 55/55 source lock, same exact lock/runner/helper, reviewed Python lock and report hashes, four raw markers checked in prior review. Current product is unchanged. No new local execution, no independent replay; raw Library ZIP materialization unavailable in this session. 8/16; 307 historical selected tests unchanged, no additive count. E1, D1-D3, E2-E4, B3 open. P10J15 exact three original test blobs match, but no execution or merge. Evidence: tests/evidence/A3_EVIDENCE_TRANSFER_0227.json.


## 0227-E1 — reviewed-lock reuse execution packet
scripts/run_e1_0227.py reuses original W8 lock inventory, exact A0C hash/wheels and a fresh source-bound review. It copies only pinned product and DB source into a new stage, installs Python offline with hash verification and npm ci with scripts disabled, runs original 6/10/8 suites with exact collection and exit counts. 10/10 synthetic runner mechanics PASS; Windows prepare/execute NOT_RUN and zero product tests. 8/16 unchanged. No runtime/product changes, no CI, no merge. If A0 raw wheel/lock bytes unavailable or mismatch, stop; retain failed stage, use separately reviewed recovery. Evidence: tests/evidence/E1_RUNNER_MECHANICS_0227.json.


## 0227-E1 Windows prepare review
User Windows prepare reports success. 16 DB pins match remote; reconstructed sorted CRLF new and A0 origin review hashes both match. No new source or product execution; install and 24 tests pending explicit local approval. 8/16 remains. Evidence: tests/evidence/E1_WINDOWS_REVIEW_0227.json.


## 0227-E1 Windows execution transcript
User explicitly approved new fingerprint and ran the isolated Windows stage. Six install/inventory commands and original 0219/0221/0224 suites exited zero; runner reported 24/24 PASS after source/lock rechecks. Actual SQLite D0 execution reported, not independent replay. Raw reports/logs/locks pending; E1 gate remains open, 8/16. No additive test aggregate, no product/source changes. Evidence: tests/evidence/E1_WINDOWS_EXECUTION_TRANSCRIPT_0227.json.


## 0227-E1 final raw review — PASS
User-uploaded raw ZIP 14/14 CRC, 9/9 report log hashes, 28 Python wheel/installed versions and 61 npm lock entries, 30 installed versions, 24 original test names match source and all pass. Two extraneous npm packages are exact optional lock entries; E3 recheck. No raw wheel binaries or independent replay. E1 closed, 9/16 (56.25%); product and DB source unchanged; prior 307 count separate. D1/D2 next; D3/E2/E3/E4/B3 open. Evidence: tests/evidence/E1_RAW_EVIDENCE_REVIEW_0227.json.
