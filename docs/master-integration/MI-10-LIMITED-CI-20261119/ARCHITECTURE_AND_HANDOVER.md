# AI Company OS — MI-10 / Sınırlı bulut CI mimarisi, karar ve devir
19 Kasım 2026 • Kaynak: `integration/mi10-limited-ci-20261119` • PR #4 **DRAFT / NO_MERGE**

## Amaç ve kanonik referans
Kullanıcının yeni açık kararıyla PC üzerinde manuel test yerine GitHub-hosted izole, salt-okunur D0 test iş akışı kuruldu. H01 istisnası yalnız bu CI PR'ına aittir. Ana ürün `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`; test edilen ortak kaynak `integration/mi-common-source-review-01@61bb06efbba7544bfc68260ed8eb4d342cab9b8e`; kaynak aktarımı/merge yok.

Kanonik mimarideki IAM/ORG/Authority/T1 ve bağımsız IV otoriteleri bu otomasyon tarafından oluşturulamaz veya yükseltilemez. CI yalnız salt-okunur kaynak, sentetik kalıcı SQLite, izole loopback FastAPI+Next.js ve Playwright ile sınırlandırıldı. 15/35/20/20/10 raporlama standardı ve ürün kabulü ayrı tutuldu.

## Gerçek yürütme zinciri (CI, test ile kabul ayrımı)
1. `source-integrity`: GitHub checkout SHA 61bb06e sabit; gerçek Python W8 source `audit` 538/538 SHA-256, 17/17 frontend/backend parity, 33/33 yardımcı Git blob, özgün package-lock SHA-256 ve 61 npm transitif paket.
2. `frontend-browser`: sabit Node/Python, özgün npm lock'tan `npm ci --ignore-scripts`, gerçek Next.js build + TypeScript typecheck. Yalnız geliştime amaçlı pinlenmiş Python/Chromium; gerçek D0 SQLite prefix, gerçek FastAPI 127.0.0.1:17301, Next.js 127.0.0.1:17300. Pre/post SQLite dosya SHA kontrolü. Özgün U3 source 2a3f2b8e... testinden geçici oluşturulan aynı-response `fetch.clone().text()` uyumluluk sürümü: UI/navigasyon/snapshot/TTL/ekran görüntüsü ve dış erişim yasağı testleri. Özgün CDP `Response.text()` PASS değil; tam W8 smoke/owner acceptance değildir.
3. `mi03-t1-d0`: mevcut GATE-01 30 kesin kaynak dosyası, G6A kaynak overlay'i sadece geçici dizinde, özgün 7+35=42 SQLite test; 0 fail/skip. Gerçek IAM–ORG–T1 korumalı PostgreSQL COMMIT **NOT_RUN**.

**Kaydedilen başarılı gerçek bulut koşumu:** [run 44613960595](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44613960595), commit `403d180fb6bf2cd739dc0d8880e3b1d3b37006e0`, üç CI job PASS. Browser sonucu **SSE uyumluluk tanılama** statüsündedir. Tarayıcı artifact ID `14573164214`, 1.440.083 bayt, yedi günlük saklama. Bu kanıt üretim kullanıcı işlemi, tam W8 veya güvenlik kabulü oluşturmaz. Doküman checksum yazım düzeltmesi sonraki CI branch commit'inde yapıldı; bu yalnız dokümantasyon değişikliğidir.

## Arıza teşhis zinciri ve çözüm
- Run 44610698699: Next.js tek başına, D0 backend yok → `shared-snapshot` HTTP 503. İlk U3 FAIL geçerli.
- Run 44612266079: `pip check`, FastAPI için `opentelemetry-api` eksiğini yakaladı → sürüm sabitlenerek eklendi.
- Run 44612869954: gerçek SQLite/ASGI ve 200 yanıtlar sağlandı; Chromium'un SSE için `Network.getResponseBody` kaynağı bulunamıyor → özgün CDP U3 FAIL.
- Run 44613836033: ilk test-uyumluluk helper'ında Python kaçış biçimi hatası → yalnız helper mekanik düzeltmesi.
- Run 44613960595: kaynak ve 42 T1 PASS, Next/TS PASS, gerçek FastAPI+SQLite + Chromium **same-fetch SSE compatibility diagnostic PASS**. Native CDP sürüm sorunu açık.

## Dosya, sembol, API, DB ve bağımlılık envanteri
Teknik delta: [TECHNICAL_CATALOG.json](TECHNICAL_CATALOG.json). Yeni ürün sınıfı/API/DB tablosu/şema yok. CI helper fonksiyonları `assert_checkout`, `git_blob`, `run`; SSE helper `blob`, `main`. Yeni CI bağımlılıkları yalnız CI dosyasında, ürün requirements/package dosyalarında değişiklik yok. Kullanılan endpointler `GET /demo/v1/lifecycle/shared-snapshot` ve `GET /api/demo/shared-snapshot` salt okunur. `lifecycle-prefix.d0.sqlite` geçici test kaydı; otoritatif tenant/store değil.

## Güncel engeller ve sonraki görev
- MI-01 Unified owner: `w8_mi_common_02.py` için bütün `audit/prepare/install/test/smoke` zincirini fresh wheelhouse/fingerprint ve sahibi onayından sonra çalıştır; formel W8 kabulü henüz yok. Native Chromium SSE/CDP response body problemine sahip denetiminde çözüm gerek; geçici CI uyumluluk kanıtı yerine konmaz.
- MI-03/04: GATE02 `durable_ops.py` sürüm/atama yetkisi ve claim zincirini sahibi uzlaştırmalı; özgün 10 Memory–T1, gerçek PostgreSQL RLS/üç DB ve protected commit bağımsız test kapıları. CI'de bunlar NOT_RUN/HOLD. Birim ve gerçek korumalı testleri karıştırma.
- MI-10: draft PR #4 son koşumları/readback'i izle; yeni kapsam açma, otomatik merge/devreye alma yok; sadece yeniden koşulan testlere göre kanıt kaydı güncelle.
- Resmî ürün ve güvenlik kabul değişimi 0. Önceden dondurulmamış kriter/payda yüzünden yeni genel geliştirme yüzdesi **HESAPLANAMADI**; geçmiş oranlar korunur.

## Güvenlik, bakım, geri dönüş
Workflow `contents:read` ve exact same-repo PR branch sınırlı. `workflow_dispatch` default branch, `push`, `pull_request_target`, OIDC, token/yazma, gerçek sırlar, model provider, harcama, PROD, `main` merge, dış iş etkisi kapalıdır. Hata halinde ilgili step exit code, job log, commit, SHA, Python/Node ve artifact incelenir; başarısız adım atlanıp PASS gösterilemez. Geri dönüş taslak PR'ı kapatmak veya izolasyon dalında normal revert; hiçbir korunan geçmiş force push/silme yok. İzin istisnasının iptali normatif kayıttan ayrıca kararlaştırılır.

[Gerçek koşum kanıtı](EVIDENCE.json) • [Teknik katalog](TECHNICAL_CATALOG.json) • [Taslak PR #4](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/4)

## Son kaynak ve test geri okuması
Dokümandaki özgün U3 kaynak blob dizgisinin düzeltilmesi sonrasında CI dalı `3b073024d99665cd1cd2a242856f4e3f8b1e682f` için bağımsız yeni GitHub koşumu [44614849105](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44614849105) **3/3 job PASS**. Kaynak 538/538 ve 17/17, özgün T1 7+35=42/42, npm lock/Next build/typecheck, geçici gerçek SQLite + FastAPI ve Chromium U3 same-response SSE uyumluluk akışı PASS. Beş ekran görüntüsü artifact `mi10-browser-44614849105` (`14573758241`, 1.440.083 bayt). Bu yeni koşum önceki 44613960595 sonuçlarını geçersiz kılmaz; tekrar regresyondur ve benzersiz test sayılarına ikinci kez eklenmez. Native Chromium CDP SSE yanıt gövdesi sorunu ve tüm korumalı kabul kapıları **HOLD**. Bu kayıt, CI'yi main veya ürün dalına terfi ettirmez.
