# AI Company OS — MI-P0 / Office post-fetch stall bağımsız negatif QA
Tarih: 20.11.2026 · Durum: **4/4 gerçek yerel izolasyon testi PASS**, W8 ve ürün kabulü **HOLD**.

## Neden ve çakışma taraması
- Ürün ana kaynağı: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` (553 dosya/552 manifest); değişmedi.
- Office sahibi: taslak [PR #22](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/22) head `668dcb08f2e9d77ea17dad0b07ff29ebbd775c0b`; ana yolu `product/ai-company-os-frontend/app/api/demo/office-workbench/route.ts`; orijinal Git blob **`ae42ecccdda987c00537696f2698f49c374ec927`**, SHA256 **`bf03304a9e8705d68c9c8987f7c03a928eb27b728d9daca44d33b86b2b9677aa`**, 2114 byte.
- Önceki bağımsız QA [PR #23](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/23) ilk iki senaryoda `controller.abort()` çağrısını `fetch()` içinden **Response dönmeden önce** yaptı. Bunlar önceki hatalı owner versiyonunu durdurmaya yararlıydı; fakat **reader.read veya reader.cancel'in fiilen başlatıldığını garanti etmez**. Sonraki PR22 R2 değişikliği bu açık senaryolara yerel yeşil sonuç verdi. Bu tur distinct post-fetch doğrulamasıdır; önceki testleri, PR #22 veya #23 kodunu değiştirmez.
- W8 PR #20, G2/G9 PR #19, manifest PR #21, güvenlik PR #10, G7 PR #24 ve farklı D0 proxy PR #26 kendi sahiplerinde devam eder. Aynı source path'de çift yazar **yok**.

## Yapılan gerçek çalışma / test sınırları
1. GitHub'dan alınan **özgün** PR22 R2 `route.ts` bayt düzeyinde Git blob ve SHA256 eşleşmesiyle yerel kaynağa yerleştirildi.
2. Sadece `officeWorkbenchProjection` parser ve `localBackendPort` için küçük test doubles yaratıldı. Ana route TypeScript kaynağı **değiştirilmedi**. Dış ağ kullanılmadı; `fetch` test içinden taklit edildi.
3. Node **v22.16.0**, yerel `tsc 5.8.3 --strict` ile özgün `route.ts` derlemesi **PASS**; proje-pinned TypeScript 5.9.3 veya full Next.js `NOT_RUN`.
4. **4/4 PASS, sıfır hata/skip:** POSTFETCH-READ: Response dönüp reader.read başladığında askıya al, daha sonra abort → HTTP **503**; POSTFETCH-CANCEL: 5000 byte aşımı sonrası reader.cancel başladı ve durdu, daha sonra abort → HTTP **503**; FETCH-INFLIGHT: canlı sinyalde fetch başladı ve durdu, daha sonra abort → HTTP **503**; VALID-STUB-200: stub parser ile geçerli JSON ve abort yok → HTTP **200**.
5. Ham TAP: `exact-4-after-fetch.tap` Git blob `c494648a1a5d36fee83ac6a413fd0a8f5a6b670e`, SHA256 `70aed7e77755f24d86e485c2102ca9ca18e8360d91eceff9a24c4d63dc899cac`. Test dosyası `17a8bc564dfc0eceba7c15d899267e7244f88ef7`, tekrar çalıştırıcı `f0ca14943bd397befa2835b36ffc53142998fd66`; üç dosya GitHub geri okumasıyla doğrulandı.

Bu 4 test **izole/yerel negatif QA** sınıfındadır. Gerçek 2500ms duvar saati SLA ölçümü, gerçek parser/port, tam W8, native Chromium, gerçek PostgreSQL, IAM, IV, üretim güvenliği/kabulü değildir. Önceki PR22/23 test sayılarıyla toplama yapıp `MVP` kabul puanı yaratma.

## Teknik katalog, API/DB/event/dependency sınırı
| Dosya/simge | Sorumluluk | Yeni özellik |
|---|---|---|
| `test_postfetch_stall.cjs` — `runWithControlledAbort` | Global fetch ve abort sinyali ile kontrol edilebilir, watchdog'lu izole Node testi | İlk iki senaryoda **read ve cancel bayraklarının çağrıldığını** assert eder; 3 negatif + 1 pozitif |
| `test_postfetch_stall.cjs` — `responseWithReader` | Response'un gerçek body okuyucu portunu test doubles ile izler | reader.read/reader.cancel kontrolü, HTTP durum doğrulama |
| `run_postfetch_check.sh` | Sahip kaynağını SHA256 kontrol eder, geçici kopyada tsc strict derler, dört testi çalıştırır ve temp'i temizler | Node 22.16.0, tsc 5.8.3 ve QA test SHA256 mismatch durumunda `exit 2` |
| `EVIDENCE.json` / `exact-4-after-fetch.tap` | Ham kanıt, sürümler ve kapsam sınırlamaları | Test kaynakları değişirse yeniden yürütülmesi gerekir |

**Ürün API değişikliği = 0; yeni DB tablo/migration = 0; event değişikliği = 0; npm/pip bağımlılığı değişikliği = 0; ek CI = 0; bağımsız yetki değişikliği = 0.** Mevcut TypeScript route'unun `GET` yüzeyi ve 4096-byte body sınırı korunur. Bu teslimatta ürün `route.ts` dosyasına commit yoktur; yalnız ayrı QA test ve dokümantasyon.

## Tekrar çalıştırma (izinli izole host)
```bash
bash docs/master-integration/MI-P0-OFFICE-POSTFETCH-NEGATIVES-20261120/run_postfetch_check.sh \
  /absolute/path/to/pr22/route.ts /absolute/path/outside/checkout/postfetch.tap
```
Ön koşul: PR22'nin **tam blob eşleşen** 2114-byte owner `route.ts` dosyası, Node v22.16.0, global TypeScript 5.8.3. Betik ağ kullanmaz ve workspace'te kaynak yazmaz; bağımlılıkları sadece geçici klasörde taklit eder. Başka TypeScript sürümü veya farklı route blob'u varsa `HOLD`, otomatik repin yok.

## Arıza teşhisi / bakım / geriye dönüş
- `ROUTE_SOURCE_BLOB_MISMATCH_HOLD`: PR22 HEAD ve route blob değişti. Sahip yeniden doğrulaması olmadan sabit SHA'yı değiştirme.
- `QA_TEST_BLOB_MISMATCH_HOLD`: QA test dosyası değişti. İmzalanmamış yeni fixture ile sonucu yeşil sayma.
- `NODE_VERSION_HOLD` / `TSC_VERSION_HOLD`: yerel araç eşitliği yok; bu tur test sonucu başka ortama taşınamaz.
- `TIMEOUT_NO_RESPONSE`: abort hâlâ askıdaki işlemde nihai HTTP 503 vermiyor. Error log'u sakla, PR22 sahibine ilet; fail-closed.
- **Rollback:** Bu taslak PR'ı kapat veya yalnız yeni izole QA dosyalarını normal revert et. PR22/23 ve `integration/product-dev`/main kodları, gerçek yetkiler ve geçmiş kanıtlar korunur.

## Merkezi devir / ileri iş
MI-05 sahibi PR22 bağımsız **post-fetch 4/4** kanıtını gözden geçirir; MI-01 sahibi tam W8 C04/C05/C06-C08, orijinal TS pinleri ve gerçek native browser kabulünü gerçekleştirir. G2/G9 source/manifest/owner ve gerçek PG/issuer/sink/IV güvenlik kapıları ayrı **HOLD**. Kanonik kabul Core **12/16**, UI **21/40**, MVP **0/11**, IV **0/7**; değişim **0 yüzde puan**. 15/35/20/20/10 ağırlıklı genel geliştirme, 10 grup paydasından onaylı 0 olduğu için **HESAPLANAMADI**. Yeni CEO izni gerektiren CI, PROD veya bağımsız kabul yapılmadı.
