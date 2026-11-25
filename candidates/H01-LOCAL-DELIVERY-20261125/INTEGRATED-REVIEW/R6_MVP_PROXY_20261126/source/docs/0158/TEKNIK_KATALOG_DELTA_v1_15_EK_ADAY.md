# Teknik katalog v1.15 — bağımsız ek adayı

Önceki v1.14 dosyası erişilemedi; onun yerine geçmez.

## CHG-0156-01 — `app/core/runtime_preview.py`
Semboller: Scope, LeaseObservation, ClockSample, RunObservation, RunState, inspect_lease, inspect_renewal, inspect_transition

Ne/neden/nasıl: D07/R01: exact sample/reference comparison; bool/int, expiry, future heartbeat, epoch, CAS, no real state mutation; STALE separate

Teşhis: Check scope→reference→epoch→expiry→heartbeat→CAS; never resurrect terminal run; no grant or renewal

Geri dönüş: ek adayını ayrı tut; R3 doğrulanmadan birleştirme.

## CHG-0156-02 — `app/core/outbox_review.py`
Semboller: Phase, OutboxObservation, inspect_outbox, DisabledRuntimeCommitPort

Ne/neden/nasıl: D15/D21/R02: commit/claim/send marker distinction, reference/generation/owner/fence, no retry or reconcile; disabled commit port

Teşhis: Readback and independent evidence missing → UNKNOWN_HOLD; no actual DB, provider call or T1

Geri dönüş: ek adayını ayrı tut; R3 doğrulanmadan birleştirme.

## CHG-0156-03 — `app/core/runtime_plan_binding.py`
Semboller: inspect_plan_binding

Ne/neden/nasıl: R09: R3-reported v1 plan shape, recompute digest, match task/role; no instance created

Teşhis: R3 exact source parity not verified; hash is not signature; IV/human roles denied

Geri dönüş: ek adayını ayrı tut; R3 doğrulanmadan birleştirme.

## CHG-0156-04 — `tests/test_runtime_preview_0156.py`
Semboller: RuntimePreviewTests

Ne/neden/nasıl: 11 unittest methods, unexecuted candidate oracles

Teşhis: Future separately authorized test; no product import performed

Geri dönüş: ek adayını ayrı tut; R3 doğrulanmadan birleştirme.

API/DB/bağımlılık değişmedi. Hashler kaynak manifestinde. İzin ve sınırlamalar JSON kaydında.
