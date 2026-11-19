# MI03-GATE02 — Source audit / runner handover

## What / why / where / how
- **What:** Read-only exact GitHub source compatibility check; 12/12 source-text guards matched. 0 new product tests and no source writes.
- **Why:** The earlier isolated 71-test 32-file stage cannot establish successful Core–OperationsStore **positive** acceptance because original Core imports are excluded from that stage.
- **Where:** Candidate `integration/mi03-gate03-org-runtime-closure-01` at `65a0e978c20378041e98f70e6ed074151214a3bb`. Governance record only on dedicated review branch, not in `integration/product-dev`.
- **How:** GitHub file contents and native Git blob SHA readbacks for eight original modules; 12 fixed nonexecuting source assertions. See EVIDENCE.json.

## Execution & test boundaries
- Previously reported 71/71 isolated Python/SQLite and 42/42 MI-10 GitHub-hosted D0 CI are *separate* earlier executions. No tests rerun in this review.
- Actual positive `OperationsStore.record_assignment_review` through genuine `app.core.development_review.research_slice.inspect_research_slice` and all Core imports: **NOT_RUN**.
- Do not use the 32-file stage as a full product checkout; source adapter is intended for the unchanged original code and no `sys.path` mutation. Do not pass synthetic `ACCEPTED_D0` as an actual owner credential.
- Original 0214 10, G9 7, G2 50, strict PG COMMIT, full product build and browser: remain separate and not implied by these checks.
- MI-10 CI grant is narrowly restricted to MI-01 W8 and original 42 selected D0 tests; do not expand to this new gate without authority. Existing MI-10 browser failure is MI-01 owner triage, not an IAM grant.

## Reproduction on approved, complete exact source checkout
From `product/ai-company-os-backend`, run the existing smoke:
```sh
python -B -m unittest discover -s tests -p test_org_runtime_packaging_mi03.py -v
```
This smoke was already recorded 4/4 PASS in the 71-run and **does not** run the positive Core test. For the next test: construct an approved original Research/Core fixture in a consistent Core snapshot, call the exact `OperationsStore.record_assignment_review()` with independently pinned ORG history and `core_args`, then independently read `assignment_review()`. Require `ACCEPTED_D0` / HOLD without grant; fail closed on identity/revision mismatch. Record log/hash, source refs, environment, case names and failure count. No production DB, migration or real identity issuance.

## Triage / maintenance / rollback
Missing imports: recover original Core transitive closure from the exact immutable candidate, never substitute a mock for a positive proof. Mismatched `durable_ops` revision: keep historical G9 source and new +41-line additive owner file separate until G9/ORG/Core owner disposition. Any positive candidate that issues actual authority is rejected. Rollback by deleting the isolated review branch / reverting governance-only evidence; do not reset an IAM claim, mutate data, rewrite history, or change `product-dev`/main.

## Reporting
IAM/ORG development **42.50% → 42.50%**, change **0 pp**. Core acceptance 12/16 = 75%, MVP 0/11, independent security 0/7. These are preserved recorded criteria, not inferred from a source check. Owner review remains HOLD.
