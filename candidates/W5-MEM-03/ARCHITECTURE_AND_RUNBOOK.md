# W5-MEM-03 — authenticated retained history (D0)
Parent 1bbcf88035ae0e59162cffa5a16cc30844f3cbec. CEO-0174 / 0179=B isolated branch only. W5 Memory/Knowledge; no D5 T1/IAM or W5-J effect changes.

## What / why / where / how
MEM-02 detects revision rebinding and inconsistent history, but a coherent earlier ACL revision rewrite with rehashed metadata can leave the latest snapshot pin unchanged. Existing v1 Ed25519 MemoryWitness already signs every committed generation (genesis, stage pending, finalize) and links record bodies via previous_sha. Reuse this authenticated chain instead of a second hash chain, table or signer. A trusted latest record digest and key pin from outside both restore domains remain required.

memory_witness.py: _latest optionally collects committed SnapshotPin values only after signature/transition validation. read_history reads head plus tuple in one SQLite read transaction and checks external pin and contiguous generations. read_latest remains compatible. Pending records do not add a committed pin; recovery epochs do not duplicate one. inspect_witnessed_context passes the tuple into existing joint review and rechecks the same externally pinned tuple afterward.

joint_context.py: optional expected_history threaded to both existing memory reads. snapshot_store.py: _review_history compares every generation's exact generation/digest/graph pin to the expected tuple inside the same transaction as existing _load, canonical metadata, raw source provenance and revision invariants. Both reads fail closed on any mismatch. The unsigned direct joint reader remains diagnostic only, not authenticated. No raw bytes or authority returned. No signature format, schema, new table, API, event, dependency, grant or D5 change.

## Test and reproducibility
From exact isolated checkout, with existing Python and cryptography, run in PowerShell:
```powershell
$env:PYTHONPATH = 'product/ai-company-os-backend;product/ai-company-os-backend/tests;candidates/W5-MEM-02'
python -B -m unittest -v test_memory_access_0194 test_memory_store_0196 test_runtime_memory_model_0207 test_joint_context_0208 test_memory_witness_0209 test_revision_continuity test_witness_continuity test_memory_history_w5_mem03
```
Linux uses colon separators. 107 historical cases + 9 new candidate cases, not a current PASS count. Synthetic disposable SQLite and ephemeral keys only. Full checkout unavailable in current runtime (private repo DNS blocked); full run NOT_RUN. See EVIDENCE.json for exact hashes.

## Failure and rollback
MEMORY_SNAPSHOT_READ_HOLD / MEMORY_SNAPSHOT_WITNESS_HISTORY_HOLD: quarantine; retain all original bytes and external pin; compare signed generations and local metadata/source. Never rewrite/rehash/repin to recover match. Pending remains HOLD; no automatic clearing/retry. If recovery reference changes, obtain trusted fresh pin through owner-controlled process. Rollback source only to parent in a separate isolated checkout, not to bypass security or reset data. No migration. Existing 512/64 MiB memory and 4096 Witness record D0 limits unchanged. Production checkpoint/retention owner decisions reserved for MEM-04.

## Explicit residuals
No authenticated write gate added: raw publish_snapshot is still a local diagnostic writer; it may extend a coherently tampered history but witnessed read refuses it. Restore of BOTH stores AND external key/head reference, signer compromise, real independent custody and post-review provider TOCTOU remain outside this D0 result. No prune, compaction, production trust, runtime grant, CI, main merge, external effects, spend, real data or PROD. Canonical PostgreSQL/T1 and full product acceptance HOLD. MEM-04 next only after regression and custody/retention owner coordination.
