# ORG-06R2 — exact SQLite integration preflight (2026-11-17)

Parent / test target: `17be56406408d572ebc66cf6fe7c1b6d83f18d76`. Branch-only candidate delta. Core D4R6 `c42beeb9f8ed7e5fc0ec83c2fdaccf6563a8607a`, Unified U3A `8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`, W5 `01bc99b5fe30aa4f0f0be3dfdfcf64e8b0d2f836`, ORG-05R5R3 `1d0d587d8e42a2f0324712e614b7a85d6245cffa` and Office A6 `438985fea059f0ffafdfa16f0d090cb854b5fc36` were inspected read-only. Branch inventory: 183 (100+83); no existing R2 branch at observation. No reservation/lock implied. Core pins: 12/12 in parent, D4R6, U3A, W5, R5R3; A6 8/12. R3 pins: 9/9 in parent/R5R3. These are selected pins, not full cross-branch compatibility.

Architecture: existing ORG-06 bridge and original R3/Core fixtures unchanged. No second Runtime, IAM, API, DB schema or event writer. Existing `org_notice` test is valid: `Store.record` seeds a revision notice. Additional independent test covers `op_notice` after one actual delegation, positive readback, corruption of exactly one row, fail-closed review. All writes only in original disposable fixture. No PG execution, UI, live agents, CI, main merge, independent acceptance or maturity promotion.

Evidence: 4/4 archive-preflight fixture tests PASS; Python compile PASS; 11 original integration scenarios NOT_RUN, 1 additional NOT_RUN. Local GitHub network DNS unavailable; local exact commit absent. Initial runner attempt BLOCKED. No product result inferred. cryptography 46.0.4 available locally; full dependency closure has not been reviewed here. Runner checks exact Git commit, 1739 tracked blob hashes, cryptography pin and unittest outcomes; does not install dependencies. Use a reviewed isolated Python environment and a complete local Git repository containing the parent commit; archive extraction may fail closed on platform/path or archive attribute differences. Full archive not downloaded locally.

Run from the R2 checkout with reviewed Python 3.12+ environment (no package installation by runner):

```
python candidates/ORG-06R2/run_checkout.py --repo . --evidence ../org06r2-evidence
```

Evidence directory must not exist. Raw logs stay local (may contain local paths); share only after review/redaction. If git/commit missing, obtain the exact source using authorized local Git access; do not relax pins. If archive mismatch, inspect Git attributes/bytes. If dependency mismatch, use reviewed isolated dependencies. If tests fail, retain logs and fix only the owned bridge/test boundary, coordinate owner changes instead of merging. Rollback: keep the original ORG-06 commit; ignore R2 delta; no persistent DB migration to reverse. Next: execute 11+1 in exact checkout, review actual evidence, then ORG-07 existing Studio API read context; keep ORG-08 and PostgreSQL owner separate.

Discovery safety: the additional scenario is explicitly invoked via main(root), not automatically discovered. Standard discovery reran the same four preflight fixture tests, 4/4 PASS; this is not four additional unique tests.
