# MI03-GATE01-GATE02-SOURCE-RECONCILIATION-01
**19 November 2026 · remote GitHub source reconciliation, no new product test.**
Source baseline: `integration/product-dev` `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`. Common review: `61bb06efbba7544bfc68260ed8eb4d342cab9b8e`. Governance parent: `d84b3046fbe17e77011668920de3d420b0afd609`.

## What / why / where / how
- GATE-01: reopened original `test_authority_fullchain_0214.py` (blob `4918027e828e8e72273ee4d6a508cac3aa6e9b59`). Its ten concrete test method names and known full-restore replay residual are recorded in `CATALOG_AND_EVIDENCE.json`. Reopened previously prepared `run_t1_fullchain.py` (blob `e60add70f9eee84f500279dddddb1bcbb4022dc7`). It pins the common 265-entry backend tree, two G6A owner sources, three DDL files and exact dependency versions. We did NOT execute it; preceding exact checkout preflight was exit 2 due missing common manifest. Prior 7+35=42 SQLite passes belong solely to prior evidence commit `878a0e4...`.
- GATE-02: compared `candidates/ORG-05R3/durable_ops.py` blob `43ed448c02904ab44b3cf8665f4aeafb0a38f10a` with owner candidate `619fe224c05d7f7f7efe998583e4730cb2cb4d3e`. All 162 original lines occur in unchanged order; 41 lines were added, none removed. Additions: initializer, assignment writer, assignment reader. This is **static additive shape**, not proof of runtime compatibility.
- Support module `assignment_lifecycle.py` blob `9f259e89fd339804292eb6c7fa8e7fd177c71b70` pins `SCOPE=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')`; `assignment_review.sql` blob `3e887b10263f44b601f6a811a89687b2ee4d864e` adds the isolated `op_assignment_review` table and no-update/no-delete triggers. No migration against existing database may be inferred. Prior 20/20 tests used direct synthetic seeds, not the real OperationsStore/Core adapter.
- Preserve original G9 fixture and this D0 extension as separate owner artifacts. Do NOT silently replace G9's pinned `durable_ops.py` or promote candidate to `integration/product-dev`. Owner review must decide namespacing/composition, SQL ownership, and later original test coverage.

## Function / API / DB / dependency catalog delta
- Existing unchanged methods: `OperationsStore._current/_team/_history/append_proposal/history/combined` and prior initializer are retained verbatim.
- New isolated symbols: `initialize_assignment_ops`, `OperationsStore.record_assignment_review`, `OperationsStore.assignment_review`; `AssignmentPin`, `ApprovalObservation`, `AssignmentReview`; `verify_core_reference`.
- New D0 table only: `op_assignment_review`, two immutability triggers. No canonical PostgreSQL schema accepted.
- Public API routes: **0**. New package dependencies: **0** (candidate imports Python stdlib and existing internal modules). Existing import semantics and live execution NOT_RUN.
- No product code, user permission, event publication, real claim, CI, build or release change.

## Test gate, diagnosis, rollback
1. GATE-01: exact common tree and dependency fingerprint (preflight); run existing pinned `run_t1_fullchain.py` only on a complete reviewed isolated checkout. Require exact [10,0,0,0,0,0] runner result, raw stdout/stderr, exit, test IDs and stable source hashes. **A 10/10 run would still reproduce one known full-restore residual.** Never call it security acceptance.
2. GATE-02: ORG/Core owners first choose the canonical namespace preserving G9 fixture. Run original OperationsStore+Core historical reader with verified pin/freshness, followed by G8 P02-A–E and strict G9 multi-store tests. Synthetic acceptance is `HOLD` and no grant.
3. If missing source/manifest: mark `BLOCKED`, do not backfill a different commit. If a SQL/role/source mismatch: `HOLD` and preserve original audit history. If the ref changes concurrently: rebase via a new reviewed commit, never force push.
4. Rollback only these governance documents by normal revert; do not overwrite previous product candidates or restore any live DB.

## Progress and handover
D5-G7 development 42.50% → 42.50% (Δ0 pp); D5-C-R8 50.00% → 50.00% (Δ0 pp); Core acceptance 12/16 → 12/16; whole-MVP acceptance 0/11 → 0/11. Overall development HESAPLANAMADI. No new unique product test or acceptance gate. Canonical source changes zero; protected COMMIT, IAM, PostgreSQL and IV remain HOLD.

Reviewed governance standards: `docs/master-integration/WORKING_STANDARD.md`, `progress/MASTER_INTEGRATION_CURRENT.json` and `progress/REPORTING_STANDARD_20261118.md`. Owners retain their tasks, no duplicate implementation.
