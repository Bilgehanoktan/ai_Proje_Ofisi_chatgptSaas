# EXT-05 — reproduction (isolated developer review only)
Use the included local slice or copy this candidate directory from the pinned EXT-05 branch into a fresh disposable directory. From the exact EXT-04 parent checkout, copy each `CORE_PINS.json` relative path under `product/ai-company-os-backend/` to `core_slice/` preserving its relative name. Copy the three `source_path` entries in `CATALOG_LOCK.json` to `artifacts/<artifact_file>`. Verify SHA-256 and Git blob identity of every byte before use. Never overwrite product source or use a shared checkout as a fallback. The local candidate ZIP includes those exact 22 files so no network or package installation is needed for the 40 unittest checks.

Run in the isolated candidate directory (Linux):
```
PYTHONPATH=core_slice python -B -m unittest -v test_catalog_review.py
```
The optional schema validation uses the already present local jsonschema 4.26.0 (no product dependency added):
```
PYTHONPATH=core_slice python -B validate_schemas.py
```
`build_catalog.py` is a developer-only deterministic builder, not a runtime loader. It writes review-only manifests/schemas into the isolated candidate directory. Do not regenerate the reference lock to accept an unexpected artifact. On source or schema pin mismatch, stop and open an explicit new review revision. No agent assignment, tool registration or execution. `CATALOG_PROJECTION.json` is historical synthetic readback, not a live install inventory. Existing core authority/acceptance is unchanged.
