# AI Company OS — MI-P0 / PR #25 R2 | Kanıta dayalı sürüm geçişi denetimi
20 Kasım 2026 · **REVIEW ONLY / HOLD** · Ürün kodu değiştirilmedi.

## Kaynak ve sahiplik
- **Tek kanonik geliştirme ürünü:** `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`, 553 dosya, 552 manifest girdisi; ürün Git tree `f4cdcf68115917ab69ba6441414539fe32a59369`.
- **Önceki test kontrolü:** PR #25 R1, 20/20 yerel sentetik Python testi. İlk denetim ofiste 0/3 ve G7'de 0/7 durumunu *sabit başarılı-kabul etmeme koşulu* olarak kullanıyordu; bu nedenle sonradan 3/3 veya 7/7 kanıt geldiğinde doğru yeni değerlendirme üretmesi mümkün değildi.
- **Bu değişiklik:** PR #25 mevcut izole dalının kendi `scripts/governance/` dosyaları. Diğer PR kaynaklarına dokunulmadı.

## Ne / neden / nerede / nasıl?
1. **`scripts/governance/verify_release_readiness.py`:** 8 aktif inceleme sahibi PR'ını (#10, #19, #20, #21, #22, #23, #24, #26) tekil tam Git SHA ile doğrular. Eksik/tekrarlı PR fail-closed. Eski PR başlarını *yanlış PASS yerine HOLD* olarak raporlar; aktif PR başı değişmesini sahte ürün kabulüne çevirmez.
2. Aynı dosyadaki `_digest()` SHA-256 biçim doğrulayıcı, `_source_receipt()` tam kaynak SHA/digest ilişkilendirici, `audit()` kanıt muhasebesi. Office 3/3 gelecekte PASS olacaksa **son PR #22 kaynağı**, PR #23 bağımsız QA PR başı, 3/3 ve ham test log SHA-256 birlikte zorunlu. G7 7/7 için **sahip PR #19 kaynağı + ham 7'li test log** zorunlu. Bunlar hâlâ *metadata doğrulaması*dır, bağımsız rapor sahibinin onayı değildir.
3. MVP 11 ve IV 7 kapısı başarıya yükseltilecekse kanonik kriterin tamamı ve kaynak bağlı kanıt kaydı zorunludur. Genel 15/35/20/20/10 gelişme oranına sahip onaysız 315 taslak kriter yüklenmez.
4. **`scripts/governance/test_verify_release_readiness.py`:** R1 20 testten R2 **32/32** yerel gerçek unittest kontrollü girdisine geçildi. +12 yeni test; canlı ürünün fonksiyonel testi değildir. Özellikle kısmi QA 2/3, eski QA SHA, sahte 7/7, imzasız IV/MVP PASS ve **tüm kontrollere PASS dense bile `release_approved:false`** güvencesi sınandı.
5. **İlerleme ve devir:** `progress/PROGRAM_GLOBAL_SNAPSHOT_20261120_R3.json` eski R1/R2'yi silmez; 8 sahip PR başını ve 24 alan/10 grup/11 MVP ilişkilendirmesini günceller. `progress/MI_P0_RELEASE_BLOCKERS_20261120_R2.json` 9 HOLD/FAIL/NOT_RUN kapısını tutar. Tüm veriler anlık gözlem; diğer sohbetler ilerleyince yeni tura yeniden doğrulanır.

## Kanıt / dosya katalogu
| Dosya | Git blob | Gerçek durum |
|---|---|---|
| `scripts/governance/verify_release_readiness.py` | `2e8f086f848c2829b342583734b62c1a2f3ce938` | Python derleme + yerel test |
| `scripts/governance/test_verify_release_readiness.py` | `683045dfdce7aeb13bb3ab34d34ab5f2eb1264ca` | **32/32 PASS**, 0 skip |
| `docs/master-integration/MI-P0-RELEASE-EVIDENCE-GATE-20261120/LOCAL_UNITTEST_R2.log` | `5034d072d883c42faad2dac77992f841b397f3ec` | Yerel gerçek stdout; GitHub byte-exact |
| `progress/PROGRAM_GLOBAL_SNAPSHOT_20261120_R3.json` | GitHub geri okuma ile ayrı doğrulanacak | 8 açık sahip PR, 10 grup, 24 alan, 11 MVP |
| `progress/MI_P0_RELEASE_BLOCKERS_20261120_R2.json` | GitHub geri okuma ile ayrı doğrulanacak | W8 / G7 / Office / PG / IV / MVP HOLD |

**Kaynak katalogu:** Yeni Python sınıfı, DB, SQL, API, event, npm/pip bağımlılığı, provider, müşteri verisi, CI akışı veya bağımsız yetki yok. Eski `EvidenceError`, `_sha`, `_object`, `_pairs`, `audit`, `main` arayüzü korunur. Yeni iki iç işlev: `_digest` ve `_source_receipt`.

## Güncel ayırımlar
- **Office PR #22:** Owner R2 37/37 seçili yerel PASS, eski PR #23 bağımsız 0/3 negatif FAIL (önceki PR #22 source SHA). Yeni head üzerinde aynı bağımsız negatifler **NOT_RUN**; mevcut release kapısı **HOLD**.
- **PR #26:** Üç D0 proxy'de 27/27 yeni ve 33/33 özgün seçili test PASS, 555 dosyalık ayrı ürün adayı; **553'e henüz aktarılmadı**.
- **G2/G9 PR #19:** 562 izole kaynakta 72/72 tarihsel seçili sentetik D0 PASS. PR #24 G7 16/16 helper PASS ama **yeni ORG üzerinde 7 özgün test 0/7 NOT_RUN**.
- **W8 PR #20:** C01-C03 3/8, C04 NOT_RUN, C05 HOLD, C06-C08 NOT_RUN.
- **Güvenlik PR #10:** Bağımsız root/issuer/sink yetkilendirmesi, korumalı PostgreSQL restore ve IV hâlâ HOLD. **MVP 0/11, IV 0/7**.
- **Genel geliştirme:** Önceki HESAPLANAMADI, güncel HESAPLANAMADI, delta HESAPLANAMADI. 10/10 grubun kriterleri henüz owner ratifikasyonu bekliyor; tasarım 15 + kod 35 + fonksiyonel 20 + entegrasyon 20 + kabul 10 ağırlıkları değişmedi.

## Tekrarlama, bakım, teşhis
```bash
python -B -m unittest -v scripts/governance/test_verify_release_readiness.py
python -B scripts/governance/verify_release_readiness.py \
  --current progress/MASTER_INTEGRATION_CURRENT.json \
  --snapshot progress/PROGRAM_GLOBAL_SNAPSHOT_20261120_R3.json \
  --evidence progress/MI_P0_RELEASE_BLOCKERS_20261120_R2.json \
  --require-review-eligible
```
İlk komut izole stdlib testlerini çalıştırır. İkinci komut için en son merkezi JSON, R3 snapshot ve R2 evidence dosyaları **aynı temiz dal/worktree'de** olmalıdır. Ağsız yerel testte bu üç tam GitHub JSON'u ayrı otomatik senkronize edilmedi; tam gerçek GitHub JSON ile CLI koşumu **NOT_RUN**. Gerçek farklı pin halinde exit 3; tutarlı ama HOLD halinde exit 2; flagsiz 0 yalnız *denetim tamamlandı*, ürün PASS değildir.

**Geri dönüş:** İki `scripts/governance/` dosyasının R2 değişikliklerini izole PR #25 içinde normal `revert` ile geri al veya PR'ı kapat. `integration/product-dev`, `main`, diğer PR'lar ve önceki kayıtlar değiştirilmez.

**Sonraki gerçek adımlar:** Önce MI-01 PR #20 W8 C04–C08, buna paralel MI-05 Office güncel bağımsız QA, MI-04 PR #19/#24 yeni ORG G7, MI-02 bağımsız root/sink/PG/IV. Bunlar kaynak sahiplerinin görevleridir; otomatik merge ya da PROD yetkisi çıkartılmadı.
