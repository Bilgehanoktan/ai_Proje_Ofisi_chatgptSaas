# MI-PROGRESS-04-R1 — Gerçek CI kanıtları, tarayıcı arızası ve sahip devir kaydı
2026-11-19. Başlangıç governance commit `69eff7e8ed4ec2eec85a6c3b10d09ba96fc15d5b`. CI yalnız açık H01 istisnasıyla PR #4; kapsam diğer CI yetkilerine yayılmaz.

## Gerçek bulgu
- Run [44610698699](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44610698699) ve [44612266079](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44612266079) **her ikisi de overall FAIL**. İkisinde de kaynak SHA-256 538/538, 17 ortak eş dosya, 33 yardımcı blob, özgün npm lock, Next.js production build/TS ve 42/42 özgün T1 D0 SQLite PASS. 42 test tekrarını ikinci defa benzersiz sayma.
- 1. koşumda U3 tarayıcı `browser_unified_u3.py:42` 200/no-store assert başarısız; Next route sadece 127.0.0.1 backend'e proxy, backend ve `AICOS_D0_LIFECYCLE_PREFIX_DB` başlatılmamış. Ham HTTP durum kodu logda yok; muhtemel 503, ama kesin 503 iddia edilmez.
- 2. koşumda `37a9180` ile gerçek sentetik SQLite prefix ve FastAPI startup tasarlandı; **Python pip check FAIL**: `fastapi 0.163.0 requires opentelemetry-api, which is not installed.` U3 browser adımına geçilmedi; PASS değil. Owner'a [PR #4 yorumuyla](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/4#issuecomment-7021871254) kesin blok aktarılmıştır.
- Yeni `integration/mi-common-source-review-01` HEAD `87272b6aebd1ce4b26d3a789b2ea75e4310cf60a`, eski `61bb06ef...` ile **539/539 product Git blob aynı**; yalnız yeni yardımcı kaynak/pin belgeleri. Formal W8 full audit/prepare/approve/install/test/smoke ayrı, NOT_RUN.

## Mimaride kalan HOLD ve sonraki gerçek aksiyon
MI10 sahibi yalnız mevcut PR #4 üzerinde tam pinli opentelemetry-api bağımlılığını doğrulasın; `--no-deps`, `pip check`, real FastAPI persisted reader, browser assert ve korumalı kapılar korunmalı. Ürün kaynağını, test beklentisini veya güvenlik yetkilerini değiştirme. Tam U3 browser sonucunu ham log/screenshots ile doğrulayana kadar HOLD.
MI03 sahiplerinin başka adayındaki 71/71 paketleme ve 11/11 SQL şema testleri gerçek izole SQLite başarısıdır, fakat pozitif OperationsStore/Core atama, G9 7, G2 50, Memory-T1 10, strict PostgreSQL COMMIT ve IV değil. Original 344 ModelMemory bekliyor.
MVP 0/11, IV 0/7, Core 12/16, UI 21/40 ve owner paket oranları değişmez. 10 grup ağırlık/payda dondurulmadı; genel geliştirme % HESAPLANAMADI. Bu tur yeni gerçek ürün testi yürütülmedi, mevcut bulut logları denetlendi.

## Tanı / bakım / rollback
- CI `pip check` dependency eksik → owner pinned requirements; asla `pip check` kaldırma. Backend readiness 200/no-store/SSE ve DB SHA, tarayıcı screenshot/TTL kanıtı bekle. Başarısız smoke marker PASS olmaz.
- GitHub Actions kanıtı run_id/job_id/commit ile sabit; tekrar koşumları tekilleştirilir.
- İzole branch source sahibi dışında mutation yok. H01 istisnası dışında CI/main/PROD, provider, harcama, müşteri verisi, real IAM grant, bağımsız IV HOLD. Governance yalnız rapor, katalog, görev listesi değişir; normal revert, force yok.
