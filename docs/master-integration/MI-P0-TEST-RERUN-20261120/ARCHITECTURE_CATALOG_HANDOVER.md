# AI Company OS — 20.11.2026 fiilî test tekrar koşumu ve teknik devir
Durum: **21/21 gerçek seçili yerel test PASS**; tam ürün W8 / kanonik kabul **HOLD**.

## Kapsam ve kaynak sürümleri
- GitHub merkezî standart `planning/master-integration-governance/docs/master-integration/WORKING_STANDARD.md`, raporlama standardı `planning/project-wide-progress-reporting/progress/REPORTING_STANDARD_20261118.md`, proje talimatları ve güncel kuyruğu okundu. Ana geliştirme kaynağı `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 dosya / 552 manifest girdisi; **değişmedi**.
- Office owner PR #22 R2 route kaynak Git blob `ae42ecccdda987c00537696f2698f49c374ec927`, SHA-256 `bf03304a9e8705d68c9c8987f7c03a928eb27b728d9daca44d33b86b2b9677aa`; PR #28'deki izole test paketi ZIP'i baştan doğrulandı. Orijinal TS route 2114 byte ve projenin gerçek parser/port modülleri **test doubles** ile karşılandı, route kodu değiştirilmedi. Node 22.16.0, global tsc 5.8.3; proje pinli tsc 5.9.3 **NOT_RUN**.
- G7 PR #24 immutable helper ve 16 `unittest` senaryosu, SHA256 runner `da4a644f3d6f189ac6a94fc8a645acde40df6489199f6a702aedf7f87a29a691`, test `b5bc7017e86c03070316bd49a628b8df73c04a5d24ac520348d2b9fbccc02bfc`; Python 3.13.5. **Gerçek G7 yedi özgün ürün testi değildir.**

## Fiilî koşum
| Kriter | Sonuç | Kanıt |
|---|---|---|
| Office paket ZIP integrity | **5/5 PASS** | `sha256sum -c MANIFEST.sha256` log |
| Office timeout + after-fetch read/cancel + pozitif stublu JSON | **5/5 PASS**, exit 0, fail/skip 0 | `office-new-run.tap` SHA256 `62da0bb1728c922236806fd143a7eade10befe7f651b071d62ae10f45fa360c1`, Git blob `cb20ec50e169fb4dfc1fbf81a9a233941d960066` |
| Office native `AbortSignal.timeout(2500)` | **503**, 2508.055562 ms, izole Node | Test 5, gerçek monotonic 2500ms timer; canlı Next/PROD SLA değil |
| G7 helper 16 Python unittest | **16/16 PASS**, exit 0 | `g7-new-run.log` SHA256 `5ed5bc42a35920800303061bb92d2e379312bf4863559c7a3c45df736233414f`, Git blob `07d7497dd1617841fe4bfd15b1d019b5beb09dae` |
| Tam immutable 553 W8 C04-C08 | **NOT_RUN/HOLD** | Checkout yok; Python/npm wheelhouse/lock supply-chain onayı yok; github.com DNS çözümlenemedi |
| Güncel ORG'de özgün G7 7 vaka | **0/7 NOT_RUN** | PR19 immutable 562 kaynak checkout yok; helper 16 bunu kanıtlamaz |
| Korunan PostgreSQL/issuer/sink/IV | **HOLD** | Bağımsız sahip ve yetki kabulü yok |

**21/21 toplamı yalnız yeni gerçek yerel koşumda çalıştırılan iki seçili test paketidir.** Önceki PR22/PR23/PR28 ve PR19 CI testlerinden çift kredi alınmaz. Tam Next.js derleme, orijinal browser ve ürün kabulü burada koşulmadı.

## Teknik katalog ve mimari değişim
| Yol / sembol | Ne için kullanıldı | Değişiklik |
|---|---|---|
| `PR22 product/ai-company-os-frontend/app/api/demo/office-workbench/route.ts::GET` | İzole deadline, read/cancel/fetch, valid stub | Özgün kaynak byte-exact; **0 ürün değişimi** |
| `PR28 test_postfetch_stall.cjs` `node:test` | Beş gerçek test, native 2500ms timer | Kopya test, **0 source değişimi** |
| `PR24 test_verify_current_org_g7.py::IsolatedRunnerGuards` | 16 stdlib negatif/pozitif kaynak koruması | Kopya test, **0 owner değişimi** |
| `PR24 verify_current_org_g7.py` | Immutable checkout, old/current ORG import guard | Bu tur yalnız helper; 7 original case **NOT_RUN** |
| `docs/master-integration/MI-P0-TEST-RERUN-20261120/EVIDENCE.json` | SHA ve PASS/NOT_RUN durumu | Yeni review/evidence kaydı |
| `office-new-run.tap`, `g7-new-run.log` | Yeni koşum ham logları | Yeni review/evidence kaydı |

Yeni ürün fonksiyonu/API/DB tablo/migration/event/bağımlılık/CI workflow/gerçek grant yok. İlerleme ağırlığı 15/35/20/20/10, grup paydaları **0/10 onaylı**: genel önce/güncel **HESAPLANAMADI**. Kanonik Core **12/16**, UI **21/40**, MVP **0/11**, IV **0/7**; delta **0 yüzde puan**.

## Teşhis, bakım, rollback, sonraki görev
1. `sha256sum` veya blob uyuşmazlığında dur; kaynağı/eski raporu sessizce yeniden pinleme.
2. Office'de test başarısızsa ham TAP ve Node/tsc versiyonlarını sakla, PR22 owner'a bildir; izole parser/port ile gerçek browser farkını kapat.
3. G7 özgün testler için PR19 **93e6c84db1a061ee914aa2c1d543620404515c0b** immutable tam kaynak checkout ve owner-reviewed bağımlılık gerekir; historical fixture 7/7'yi current product 7/7 diye etiketleme.
4. W8 owner PR #20 önce kanonik 553 üzerinde C04 `prepare` + C05 supply-chain owner onayı + C06–C08 install/build/native browser yürütür. Ardından PR19 G2/G9 owner varyant kararı ve ilgili 562/557 manifest uyarlamaları gözden geçirilir. Strict PG/issuer/sink/IV bağımsız.
5. Rollback: Bu isolated doküman/log PR'ını kapat veya yalnız bu yolları normal revert et. Ana `integration/product-dev`, `main`, sahip kaynakları ve güvenlik izinleri **değişmedi**. `AI_Company_OS_TEST_RUN_REPORT_20261120.zip` yerel teslimat SHA256 `5b6a946a957c0947886b296cc2770f5dd1969aab84fa5491cb4515f649b36582`.
