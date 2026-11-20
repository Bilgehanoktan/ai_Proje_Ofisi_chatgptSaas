# MI-08 — Linux native symlink source-guard verification (2026-11-20)

**Scope:** Smallest source-level follow-up to prior Windows `Memory 183 PASS + 1 SKIP` and `160 PASS` separate runs. The one skipped original test `SnapshotStoreTests.test_bad_path_and_pin` on Windows could not create a symlink (`winerror=1314`). Source guard `snapshot_store.py::_path` is byte-for-byte copied from GitHub source blob `bc8cd58a5e58a9043d5bf188af11521b1641b9c7` on `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`. The **whole product module was NOT imported** in this local minimal harness; no full original 184 or strict 344 rerun took place.

## Actual new execution

- Linux Python 3.13.5, real OS symlink permissions. The extracted `_path` function was exercised against temporary real filesystem paths, not a mocked symlink.
- Real file symlink rejected, real directory-symlink ancestor rejected, invalid suffix rejected, canonical existing file accepted, canonical unused filepath accepted without creation: **5/5 PASS, 0 SKIP, 0 failure**.
- Local reproducible harness: `MI_MEMORY_SYMLINK_GUARD_LINUX_CHECK.py` sha256 `50309a5934888b2af738d24474af74b84efc0744b2bb26126a62efe09846575c`; output JSON sha256 `cbad75bcb2df39873c0185ffb87c2ce5ed829e59a51d4f34c026b1cd6af13c76`, attached in originating conversation but not committed into GitHub source. The exact result is recorded in `EVIDENCE.json`.
- **This does not retroactively turn the original Windows skipped test into a passing original test; it demonstrates only the exact path guard on compatible Linux.** Original full `344` acceptance still `HOLD`. Do not count a security-negative case as product acceptance.

## Catalog, maintenance, next

- Product source symbol `_path(path)`, Git blob `bc8cd58a5e58a9043d5bf188af11521b1641b9c7`; original test `test_memory_store_0196.py::SnapshotStoreTests.test_bad_path_and_pin` blob `02743dead991906a120e3f3ef627d0e60e8e09c3`. No new production code, class/function/API/schema/event/DB/dependency changes. No Windows policy, admin, original skip or original runner change.
- To fully close original one skipped test, MI-08 owner should run *the original test*, exact same source, in approved Linux CI or otherwise authorized compatible environment, with complete dependencies and all original pin guards. No unsanctioned CI/workflow scope.
- MI-01 W8 C04-C08, independent security roots, protected PG and IV are separate HOLD; G2 50/G9 7 original historical source tests already CI PASS at [#44697437051](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44697437051), but canonical source-version conflict still open.
- MI08 45%→45%, MI03 42.5%→42.5%, global weighted percent undefined, product acceptance delta 0 pp.
- Rollback: normal revert of this governance-only report; preserve unchanged source Git blob and older Windows retry evidence.
