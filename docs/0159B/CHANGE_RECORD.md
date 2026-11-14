# DOC-REV-0159-B — R6 source candidate
Parent 0159-A 5d48944585ccde25b5d98199a3ac68768aa8d833; source commit 516aea0091c1834263e3e99b386a5888b141b16b. 72 parent source byte-exact; 12 new Python files, 308 lines (including 5 initializers and test file). New packages under backend app/engines. No API, DB, dependency or existing product path change.
|What|Why/how|Diagnosis/rollback|
|---|---|---|
|model_gateway/registry.py, fallback.py, gateway.py|D08/D21: disabled exact adapter registry, same Scope/principal and effect ceiling, no capability expansion; no real invoke|ADAPTER_PIN_INVALID, FALLBACK_SCOPE_MISMATCH, CAPABILITY_HOLD; rollback parent, never reactivate old grant|
|skill_engine/resolver.py|R08: source/manifest pin, diagnostic intersection only; quarantine, effective_tools empty|SKILL_SOURCE_PIN_HOLD, INDEPENDENT_RECEIPTS_ABSENT; independent custody/license remains open|
|knowledge_engine/provenance.py|D09/R10 raw and span SHA-256; byte index bounds|SOURCE_DIGEST_HOLD, SPAN_BOUNDS_HOLD; no source authority|
|memory_engine/retrieval.py|R10 current-view equality, scope, orphan/cycle rejection, tombstone descendant closure|TOMBSTONE_VIEW_UNKNOWN_HOLD, STALE_HOLD; no retrieval, purge or release|
|tests/test_engines_0159b.py|12 candidate unittest methods|NOT_RUN; no accepted real evidence|
Catalog v1.18 and progress tracker v9, handover, migration and contract inventory added. Existing management pointers updated; prior history in Git and full parent ZIP. D0 code only, NO_CODE normative conflict persists; narrow repo permission is not T01 ratification. CODE/REPO/DEV normative 0/3. No real TEST/CI, PROD, provider, external runtime effect, spend or main merge.
