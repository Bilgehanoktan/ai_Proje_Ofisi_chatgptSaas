# MEM-05C-R1 — Portable exact-source regression

Parent 31c07c5cd58458abfb4ed20a3b33c73cda57c1df. Existing original 10 test methods and 149-pin manifest preserved byte-for-byte. GitHub private repository accessible via connector; local git ls-remote failed DNS resolution. Original test execution NOT_RUN. 136 Memory pins already present in parent; 13 exact Gateway blobs (12 modules and one test fixture) copied only to this revision's overlay, not to product. No W5/IAM/ORG/D4/T1 or Studio source change, no merge.

## What/why/where/how
run_archive.py authenticates original pin file and test against fixed Git blob IDs, validates 149 exact source bytes, checks path and reference, stages a disposable directory, runs original ten diagnostics with isolated Python and explicit import paths. No git fetch, install, CI, provider, external effect or spend. Runner mechanics: ten actual synthetic helper tests passed, separate raw helper.log. Local run_archive preflight stopped exit 2 due to missing local parent checkout. No original test case executed. No product or security acceptance.

## Static oracle review
Original test_independent_matches_can_reference_different_invocations and test_signed_memory_head_is_not_invocation_authority exercise the same independent-match setup and differ only in assertion ordering. Preserve both original methods; do not claim ten independent security properties. The revocation test changes an unsigned snapshot and expects old witness failure, not signed publication or atomic egress prevention. Fixture token count 40 is supplied; no tokenizer verification. Current budget owner readback is synthetic and not authoritative reservation custody. These are scope limitations, not proven runtime bugs or fixes.

## Run
Download the complete ZIP at this revision's commit from the authenticated GitHub account, extract to a short local path, using reviewed installed Python 3.13.5 and cryptography 46.0.4 (known prior versions; runner prints actual versions). From repository root:
`py -3 -B candidates/W5-MEM-05C-R1/run_archive.py`
Capture stdout/stderr and exit code. Git is not needed. On missing source, blob mismatch, missing crypto, failed import, or test error preserve log and stop; no expectation or original pin changes just to pass. Source files are read-only; temporary stage deleted. Rollback discard this revision/overlay only; parent untouched.

## Integration owner boundary
D5-G4 reported 14 selected local tests but protected ORG publication and actual T1 writer remain absent. W5-J2-R4 owns economic phase/receipt semantics; ORG current membership and D4 binding stay in owner branches. Do not implement an independent parallel authority or budget engine. Shared guarded reader integration remains HOLD. Next action: obtain exact ten-case execution and diagnose observed failures; then agree smallest common binding in existing owner path. Preserve 24-area tracker and all acceptance gates.
