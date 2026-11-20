# AI Company OS — W8 553 değişmez npm kilidi / hazırlık düzeltmesi

**20 Kasım 2026 · MI-01/Unified aday dalı · SAHİP İNCELEMESİ GEREKLİ · ürün kabulü DEĞİL**

## Mevcut engel ve gerçek değişiklik

Kanonik `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66` 553 ürün dosyası / 552 manifest ile birleştirilmiş. Önceki `tests/integration/w8_unified.py` özgün `prepare` aşaması, ürün içinde kilit bulunmadığından `npm install --package-lock-only` çağrısıyla ağdan transitif npm bağımlılıklarını **yeniden çözümleyebiliyor**; W8 C04 için değişmez, incelenmiş kilit gerek. C04–C08 hiçbirisi kabul edilmedi.

Bu aday, eski özgün npm lock'u **yeni bir kilit üretmeden** kaynak ağacına bayt düzeyinde taşıyor ve yalnız W8 U3 üst adaptörü üzerinden özgün `prepare` npm kilidi üretim çağrısını kontrollü bir kopya işlemiyle değiştiriyor. Python wheel indirmesi ve özgün W8 testleri aynen kalıyor, yetki genişlemesi yok.

## Teknik katalog: yollar ve semboller

| Yol | Amaç |
| --- | --- |
| `tests/integration/w8_unified_u3.py` | Yalnız üst W8 adaptörüne değişmez helper bağlantısı; 23 mevcut ata kaynak aynı |
| `tests/integration/w8_frozen_npm.py` | `verify_frozen_npm_inputs` (lock/root/hash/provenance), `FrozenNpmPrepareHook` (yalnız tek npm lock yazımı), `install_into_w8` (original prepare wrapper) |
| `tests/integration/locks/mi01-frozen-npm/package-lock.json` | Mevcut `docs/ORG-07C-R8-INTEGRATION/original-lock/package-lock.json` ile **aynı Git blob** |
| `tests/integration/test_w8_frozen_npm.py` | Gerçek çalışan 15 synthetic mekanik test ve negatif güvenlik kontrolleri |
| `docs/master-integration/MI01-W8-FROZEN-NPM-20261120/EVIDENCE.json` | Makine-okunur sonuç/pin/rollback |
| `docs/master-integration/MI01-W8-FROZEN-NPM-20261120/ARCHITECTURE_CATALOG_HANDOVER.md` | Mimari, dosya/sembol/bağımlılık/test ve devir |

**Özgün lock:** Git blob `4cd33f437df85d7e74c7946a0999f76adf2e31fe`, 33.618 bayt, SHA-256 `036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88`. npm lock v3, 61 transitif girdi; doğrudan ürün `package.json` blob `55a6d296ee20daad2cd36f4552f9feb3f4440ba3`, PostCSS 8.5.32 ve Sharp 0.35.5 overrides kontrol edildi.

**Davranış:** onaylı lock veya package.json değişirse hazırlık hiçbir aşamaya başlamadan `HOLD`; symlink / registry / integrity / override / lock graph mismatch `HOLD`; birden fazla npm kilidi üretme çağrısı veya beklenmedik registry `HOLD`; başarısız pip hazırlığında sahte `REVIEW.json` bırakılmaz. Sonraki `install/test/smoke` özgün onay token mekanizması değişmez.

## Gerçek test ayrımı

Container Python 3.13.5 üzerinde yeni `w8_frozen_npm.py` mekanikleri için **15/15 mevcut sentetik unittest PASS** (0 hata, 0 skip). Sınamalar: geçerli kilit, SHA/byte bozulması, package.json değişimi, direct/development pins, overrides, kötü registry, eksik integrity, symlink, paket sayısı, tek kullanımlık kopya, ikinci çağrı, yanlış cwd/registry, üzerine yazma, diğer komutlar, hata halinde sahte REVIEW temizliği.

**Özgün W8 C04 `prepare` hâlâ NOT_RUN:** bu konteyner GitHub/PyPI/npm DNS'e erişemiyor, tam 553 checkout ve wheelhouse/REVIEW hazır değil. Bu 15 test eski C01–C03 veya yeni C04-C08 PASS değildir; Next/TS/native U3 browser, PostgreSQL ve A bağımsız güvenlik kabulü **HOLD**.

## Değişiklik / kaynak / bakım / geri dönüş

Bu dalda ürün kaynakları `product/`, `SOURCE_MANIFEST.json`, API/DB/sınıf/üretim bağımlılıkları, `.github` CI iş akışları ve `main` **değiştirilmez**. Git blob/branch ayrımı korunur; otomatik merge veya güvenlik aktifleştirme yok.

**Sonraki gerçek görev:** MI-01 sahibi kaynak adayını ve özgün npm kilidini denetlesin; izinli tam 553 checkout ortamında C04 wheelhouse/Python lock/REVIEW fingerprint üretsin. C05 bağımlılık sahibi **onayı olmadan** C06–C08 `install/test/smoke` yapılmaz. C05 sonrası native Chromium, SQL/HTTP ve 52 ekran kanıtları özgün W8 testleriyle doğrulanır. Ürün ile G2/G9 güvenlik varyantı sahiplikleri ayrıdır.

**İlerleme:** MI01 W8 operasyonel **3/8 → 3/8**, Core 12/16, UI 21/40, MVP **0/11**, IV **0/7**, güvenlik A-AT **0/8**. 15/35/20/20/10 ağırlıklı global geliştirme onaylı kriter paydası olmadığından **HESAPLANAMADI** (önceki = güncel; delta yok). Bu PR yeni kabul kriteri kapatmaz.

**Rollback:** taslak PR'ı kapat veya yalnız bu inceleme dalının commit'ini normal revert et. W8 root pinli ata modüller ve ürün kaynak ağacı değişmediğinden önceki çalışan test kapsamı etkilenmez.

## R2 — Bağımsız gerçek test tekrar koşumu ve 4 yeni bütünleşik simülasyon (20.11.2026)

- Gerçek konteyner Python **3.13.5** içinde, kaynakları Git blob pinleriyle birebir karşılaştırılmış `w8_frozen_npm.py` **257ba8f1**, önceden commit'li `test_w8_frozen_npm.py` **efa2e0aa** ve yeni `tests/integration/test_w8_frozen_npm_integration.py` **7a3baa89** beraber koşuldu.
- Komut: `python -m unittest -v test_w8_frozen_npm.py test_w8_frozen_npm_integration.py`. Ham sonuç: **Ran 19 tests in 0.015s, OK**; önceki 15/15 → güncel **19/19**, delta +4 sentetik yöntem; mevcut testler yeni kriter olarak ikinci kez sayılmaz.
- Yeni 4 kontrol: değişmez npm kilidinin Python bağımlılığı çağrısından önce stage'e yazılması ve npm çözümleyici çağrısının hiç yürütülmemesi; bozuk package pininin stage oluşturulmadan engellenmesi; aynı kilidin ikinci kez oluşturulmasının engellenmesi ve sahte `REVIEW.json` izinin temizlenmesi; pip başarısızlığında W8 yürütücüsünün ilk durumuna dönmesi.
- İndirilebilir/reprodüksiyon için ham günlük: `docs/master-integration/MI01-W8-FROZEN-NPM-20261120/TEST_RESULT_ACTUAL_19.txt` — SHA-256 `985f6cbed8fa47ac3edb90b40ca142bc52150767423793cc624f0d7703e4086e`; Git blob `1df01ccd1a719c190d0ef550bacc9e6b86e181c6`. İkinci test dosyası da aynı PR içinde. `docs/` kanıtı sahibi onayı değildir.
- **W8 C04-C08 hâlâ açık:** Tam 553 kaynakla özgün wheelhouse/prepare, gerçek Next.js/backend build ve Chromium smoke **NOT_RUN**, C05 supply-chain **HOLD_OWNER**. 15/35/20/20/10 genel gelişme paydaları ratifiye değil (**HESAPLANAMADI**); MVP 0/11, bağımsız IV 0/8, ürün kabul değişimi 0.

**R2 bakım/rollback:** Aynı PR'daki ek 4 test + kanıt ve bu ek normal commit revert ile geri dönebilir. Mevcut `product/`, W8 ata modülleri, `integration/product-dev`, `.github`, `main` veya güvenlik izinlerine yazılmadı.
