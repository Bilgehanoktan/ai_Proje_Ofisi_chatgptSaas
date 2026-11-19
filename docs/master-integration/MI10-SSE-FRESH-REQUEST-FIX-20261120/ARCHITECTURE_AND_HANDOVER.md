# MI-10 — İstek bazlı SSE uyumluluk düzeltmesi ve devir

20.11.2026 · PR #4 `integration/mi10-limited-ci-20261119` (DRAFT, **NO_MERGE**).

## Sorun ve karşılaştırma
Önceki başarılı CI akışı, tarayıcıda her `/api/demo/shared-snapshot` isteğinden sonra aynı global `window.__mi10LastStreamBody` Promise değerinin null olmamasını bekliyordu. Ayrı QA hattının `MI10-SSE-FRESHNESS-REPRO-20261120` çalışmasında, B yanıtı henüz gelmemişken A'nın okunabileceği iki olumsuz senaryo **gerçek offline Node testiyle** tekrarlandı. Bu, eski CI'nin freshness kontrolünü yetersiz kılar; ürün/gerçek browser kusuru olarak varsayılmaz.

## Ne / neden / nerede / nasıl
Sadece dört MI-10 CI dosyası değişti: gerçek ürün kodu, REST API, SQLite tablo yapısı ve bağımlılıklar aynı. `.github/mi10/sse_fresh_interceptor.js`, aynı kaynağa yapılan her fetch çağrısı sırasında **sıralı istek kaydı** açar. Her response URL ve Promise sonucu yalnız kendi kaydına yazılır. Kopyalanan özgün U3 testinin `read(panel)` fonksiyonu, butona basmadan önce beklediği sonraki sıra numarasını belirler ve tam o numaradaki gövdenin hazır olmasını bekler; önceki gövde kabul edilmez. Orijinal U3 Git blob `2a3f2b8e286c5d79847a6b00cdb6d046d0429773` ve ek JS blob `6431565e3ccdbdeb72fbebeb7bd5a7891aafc534` sabittir. Ek HTTP çağrısı veya sahte `route.fulfill` yok.

Yeni `.github/mi10/test_sse_freshness.cjs`, **aynı JS kaynak dosyasını** Node VM içinde çalıştırır ve A/B/C gövdeleri için 17/17 negatif/kimlik kontrolünü yürütür. Eski Promise kullanılabilse test FAIL olur. `.github/workflows/mi10-limited-ci.yml` içine mevcut frontend işinde bu test adımı eklendi. Önceki ilk deneme run `44620487661`, testin VM-dizi prototipi nedeniyle FAIL oldu; yanlış kaynak bağlamını `Array.from` ile düzelttim, beklenen sonuçları gevşetmedim.

## Kanıt
- Kaynak commit: `f98da5ab0cef72e87b15878499baceeb15909005`.
- [GitHub Actions run 44620987573](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44620987573): 3/3 CI işi PASS; 17/17 taze-yanıt Node testi, Next build/TS, gerçek geçici SQLite+FastAPI+Chromium U3 uyumluluk akışı ve özgün seçili 42 T1 SQLite PASS.
- Tarayıcı artifact `14577580762`: yalnız sentetik ekran görüntüleri ve yerel sunucu logları.
- [EVIDENCE.json](./EVIDENCE.json) ve [TECHNICAL_CATALOG.json](./TECHNICAL_CATALOG.json) sürümlü kanıtlardır.

## Kalan sınırlar
Özgün `browser_unified_u3.py` dosyası byte-exact biçimde doğrudan CDP `Response.text()` üzerinden henüz başarılı çalıştırılmadı; orijinal CDP hatası **HOLD**. Tam `W8 audit/prepare/install/test/smoke` zincirinin sadece audit aşaması tamam; bağımlılık fingerprint'i/owner onayı, gerçek protected IAM–ORG–T1 PostgreSQL ve bağımsız IV açık. Bu test QA tanılama PASS'ıdır; ürün kabul deltası 0, 15/35/20/20/10 genel yüzde hesaplanamaz.

## Bakım, arıza teşhis ve geri dönüş
- Node negatif senaryo FAIL: `test_sse_freshness.cjs` VM içi sıra kimliği/gövde ilişkilendirmesini incele; test beklentisi gevşetilemez.
- JavaScript interceptor git blob mismatch: kaynak güvenliği için `MI10_SSE_INTERCEPTOR_PIN_HOLD`; owner review olmadan repin yok.
- Playwright timeout: clone gövde bitmedi, yanlış response URL veya request id; sentetik FastAPI/log ve UI isteği sayısını karşılaştır, FAIL bırak.
- Rollback: izole CI commitleri normal revert veya PR #4'ü kapat, ürün kaynakları/izinler/main değişmez.

Sonraki adım: MI-01 tam wheelhouse/provenance incelemesi için `docs/master-integration/MI01-W8-P0-PROGRESS-20261120/DEPENDENCY_REVIEW.json` kaydına göre owner onayı; otomatik W8 install/test/smoke başlatma.
