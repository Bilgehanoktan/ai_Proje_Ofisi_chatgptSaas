# W5-MEM-03R1 — exact regression and runbook correction
Parent 0bbcb5853eb7235dcbeefbd4fadae11383ddb715; architecture remains [MEM-03](../W5-MEM-03/ARCHITECTURE_AND_RUNBOOK.md). CEO-0174 / 0179=B D0 only. No product source, test expectations, schema, authority, API or dependencies changed.

## What / why / where / how
Private repo checkout remains blocked locally. Recovered 34 original files from the pinned Git tree (including 8 package initializers, 3 requirements, and MEM-01 fixture). Verified each local Git blob identity against its source. The prior MEM-03 runbook omitted candidates/W5-MEM-01 from PYTHONPATH; first combined attempt produced an import error, 99 other tests passed. Restored the exact fixture (blob 60608147f84cf74f9ac5849f66cd8eeb92c9c9ea), corrected invocation only. Original historical residual tests are imported as fixtures, not separately run as current acceptance tests. 116/116 passed twice. First verbose raw log is in the local evidence ZIP; final verbose and repeat quiet logs are retained in this branch.

## Corrected reproducibility
From an isolated checkout of the parent or source-identical evidence branch:
```powershell
$env:PYTHONPATH = 'product/ai-company-os-backend;product/ai-company-os-backend/tests;candidates/W5-MEM-01;candidates/W5-MEM-02'
python -B -m unittest -v test_memory_access_0194 test_memory_store_0196 test_runtime_memory_model_0207 test_joint_context_0208 test_memory_witness_0209 test_revision_continuity test_witness_continuity test_memory_history_w5_mem03
```
Linux uses colon separators. Python 3.13.5 / SQLite 3.46.1 / cryptography 46.0.4. Existing optional direct pin matches; transitive lock not verified. No provider/network/runtime effects.

## Maintenance and rollback
If import fails, check all four paths and exact pins before running; do not edit the fixture or weaken assertions. Preserve logs and source; on HOLD, quarantine, compare existing signed refs and history, never rehash/repin or reset pending. Source rollback remains MEM-02 parent only in a separate isolated checkout, never to bypass controls. Evidence branch rollback: use parent 0bbcb5853eb7235dcbeefbd4fadae11383ddb715; no product change to revert.

## Next
MEM-04 checkpoint/retention owner review: preserve signed prefix and revision/tombstone semantics, define bounded checkpoint proof and authenticated restore reference; no silent compaction/deletion or production retention decision. D5 recovery owns external trust/T1. MEM-05 canonical runtime/PostgreSQL after locked unified regression and owner alignment. Independent custody, full product, real authority, CI/main/PROD remain HOLD.
