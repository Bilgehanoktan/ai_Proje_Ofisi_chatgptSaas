# P10J-02 architecture and technical catalog delta

Scope: supplemental read-only checkout audit outside product; no architecture authority or product manifest changes.

| File / symbol | Purpose | Dependencies |
|---|---|---|
| docs/UI-P10J/audit_manifest.py / audit(root, manifest, expected_count=384) | Compare path, length, SHA-256, reject links, aliases and extra files | Python stdlib hashlib, json, pathlib, sys |
| CLI | Require manifest SHA-256 and return nonzero on HOLD | Same |

8/8 local synthetic fixture checks passed: valid, count, missing, traversal, length, case alias, symlink, extra. CLI and full checkout NOT_RUN. Existing original ZIP auditor/W8 remain authoritative. No API, DB, classes, runtime or external dependency changes. Limit: assumes quiescent trusted local checkout; not race-safe against concurrent mutation; not independent security verification. Manifest hash must come from trusted pinned source, not Git blob SHA. Diagnosis: inspect errors; restore exact pinned files, never edit manifest to suppress mismatch. Rollback: revert helper commit on isolated branch; no migration. Progress 21/40, independent 0/7. Next P10J-03 full checkout and W8; remote 12/384 prior, no additional full-source claim.
