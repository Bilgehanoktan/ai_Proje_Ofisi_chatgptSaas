# MI-01 / W8 — PR36 gerçek Windows tam zincir doğrulama runbook'u (2026-11-21)

## Hedef / delil sınırı
- Önceki **PR35 Windows**: C04 PASS, C06 PASS, C07 **ATTEMPTED_FAIL** (iki eski P10J16 navigasyon testi); C08 NOT_RUN.
- **PR36** (bu dal): birebir SHA-256/Git blob sabitlenmiş P10J16 testi Windows üzerinde **8/8 PASS** (`NODE_EXIT_CODE 0`), ama **tam PR36 C07/Next.js build ve C08 NOT_RUN**.
- Bu turun amacı PR36 için **yeni, izole** G3/C04/C06/C07/C08 kanıtı elde etmek ve önceki test ortamını değiştirmemek. **Bağımsız C05 güvenlik/IV, owner kabulü, gerçek yetkiler, CI izni ve main/product-dev merge ayrı HOLD'dur.** Tek kullanıcının tamamlama talebi bu sınırları değiştirmez.
- Güncel ürün dalı referansı: `integration/product-dev@254e0188998d0d245bd8ee4eb901aead02951a66`. PR36 ayrı kalır.

## Kullanıcıya teslim edilen doğrudan Python çalıştırıcısı
- Konuşma eki: `AIOS_W8_PR36_FRESH_WINDOWS_VALIDATION_20261121.py` (script source bu GitHub dalına otomatik aktarılmış değildir; yerel teslimat).
- **SHA256:** `035b8000ab0f84d3b8602fa3a90954ff3a7a7cdf0748d143e513775e30c4e576`, **25,478 bytes** (Python 3.11+).
- Hazırlık: statik Python `py_compile` PASS, AST kontrolünde dosya silme, policy bypass veya `eval/exec` yok; **önceki gerçek 3972-byte PR35 P10J16 testi üzerinden üç değişiklikle birebir PR36 4029-byte SHA256/Git blob üretimi PASS**. Bu hazırlık kanıtıdır, Windows'ta tam test yapılmış değildir.

Windows PowerShell 5.1'de indirilen yardımcıyı içeriğini inceleyip SHA-256 ile doğrulayarak yürütmek (imzasız `.ps1` betiği yürütülmez; `ExecutionPolicy` değişmez):

```powershell
$file = Join-Path $env:USERPROFILE 'Downloads\AIOS_W8_PR36_FRESH_WINDOWS_VALIDATION_20261121.py'
$expected = '035b8000ab0f84d3b8602fa3a90954ff3a7a7cdf0748d143e513775e30c4e576'
if (!(Test-Path -LiteralPath $file)) { throw 'PR36_PY_HELPER_NOT_FOUND' }
if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'PR36_PY_HELPER_SHA_MISMATCH' }
py -3 $file --mode preflight
if ($LASTEXITCODE -ne 0) { throw 'PR36_PREFLIGHT_HOLD' }
py -3 $file --mode run
if ($LASTEXITCODE -ne 0) { throw 'PR36_FULL_RUN_HOLD' }
```

C08 için açıkça doğrulanmış Chrome executable yolu mevcutsa `--mode run --chromium 'C:\Program Files\Google\Chrome\Application\chrome.exe'` argümanı ile **aynı yeni aşamada** tam tarayıcı çalıştırması talep edilir. C07 başarılı fakat bu argüman yoksa yeni aşamadaki `PR36_W8_STATUS.json` üzerinden aşağıdaki ayrı smoke moduyla devam edilebilir (sadece tek defa, önceki C08 girişimi yoksa):

```powershell
py -3 $file --mode smoke --run-root 'E:\AIOS\W8\PR36_W8_FRESH_<timestamp>' --chromium 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

### Kaynak ve güvenlik sınırları
1. Betik salt-okunur `E:\AIOS\W8\W8_AGENTFIX_LOCAL_20261121_002919\stage` içindeki **552** PR35 manifest girdisini SHA-256 ve kritik Git blob ile doğrular; eski test `8bb0a81933001c64558df9e630af93390b1549714370750e8cb43bea2cef2bee`, panel `7d75044a6b8083467b9acf77d996e3adf35c2debdde74d5a88c3157bc4c30dcc`.
2. Yerel özgün `w8_unified_u3.py` için PR35 Git blob `735f093106d1e774b58188917286b37ddd36e804`, kök `w8_unified.py` `162a2387e5cdea6828a0cbbf0dab247bc4678551` ve `w8_p10j24.py` `0728ba08494bb8d67c7cec42fe27dd8606bdc7f3` zorunludur. Bu özgün runner dosyaları önceki izole çalışma sırasında `stage` yanındaki `source/repo/checkout` veya kullanıcının `Downloads` klasöründe aranır; yoksa betik HOLD verir ve **sahte/yeniden üretilmiş yetkisiz runner oluşturmaz**. Gerçek yer `--runner-dir <folder>` ile belirtilebilir.
3. Sadece `E:\AIOS\W8\PR36_W8_FRESH_<timestamp>\source` altında **yeni temiz kaynak** üretilir; test SHA256 `c9b66a7d45fb298647ad1d74179f61dcc37733beb41bea08894e1f4036fc1431` / Git blob `f55f72ffc1ec9c5de81b4be0fd13d2a5f01d5fe5`, manifest Git blob `9660da1104617b4764d5f1e32009e4e3405b47f8` ve adapter Git blob `1609d857b46ea973180c45271d87fcc92083f0a6` doğrulanır. Diğer ürün dosyaları byte-exact kopyadır.
4. **Özgün** `w8_unified_u3.py audit` tam 552 SHA256 + alt kaynak pinlerini, `prepare` taze npm lock/wheelhouse/fingerprint üretimini uygular. **Yeni `REVIEW.json` bağımlılık matrisi PR35'ten yalnızca `manifest_blob` bakımından farklıysa** aynı bağımlılıkların önceki yerel onay kaydıyla eşlendiği kanıtlanır ve `install/test` sürdürülür. Herhangi bir Python wheel SHA / npm lock SHA / sürüm / kaynak/provenans farkında HOLD; otomatik bağımlılık/yetki yükseltmesi yok.
5. C06 orijinal **offline hash-locked pip install**, frozen npm `npm ci`, `pip check`; C07 orijinal ardışık test grupları + **Next.js build/tsc**; C08 yalnız **açık belirtilmiş gerçek Chrome/Chromium executable** ile loopback `127.0.0.1` ve gerçek tarayıcı scriptleri. Sistem genelinde environment/policy değişmez; yalnız betik Python sürecinin TEMP/TMP/TMPDIR değişkenleri yeni E klasörüne ayarlanır.
6. Özgün PR35 stage kaynak SHA değerleri işlem sonunda tekrar kontrol edilir. Dosya silme, kalıcı izin değiştirme, repo merge, GitHub Actions değişikliği veya PROD harcama/erişim yoktur. Her yeni çalışma **ayrı klasörde** tutulur; eski .log, .json ve manifest/pinler saklanır.

## Kanıt toplama, sorun teşhisi ve geri dönüş
- Yeni: `E:\AIOS\W8\PR36_W8_FRESH_<timestamp>\PR36_W8_STATUS.json` ve `PR36_W8_NATIVE_FULL.log`. **Kullanıcı bunları paylaşmadıkça Windows tam sonuçlar NOT_RUN olarak kalır**.
- `EXACT_PR35_RUNNER_CHAIN_MISSING`: eski pinli `w8_unified_u3.py` ve atasını içeren klasör bulunamadı. Yeni kod yazıp pin kandırılmaz; mevcut arşiv/git checkout içinde `--runner-dir` ile özgün kaynak bulunmalıdır.
- `REVIEW_DEPENDENCY_DRIFT_HOLD`: npm lock/wheelhouse/provenans değişmiş; C06 çalıştırılmaz. Yeni özgün dependency/owner review gerekebilir.
- `*_FAILED_EXIT_*`: özgün komutun kendi satırları logta; başarısız adım atlanmaz, build/smoke PASS sayılmaz.
- `C08_NOT_RUN`: Chrome executable belirtilmedi; C07 PASS olsa da C08 tamamlanmış sayılmaz.
- **Geri dönüş:** yeni `PR36_W8_FRESH_<timestamp>` klasörü kullanıcı sahipliğinde arşivlenebilir; eski PR35 stage ve PR35/36 kod, bağımlılık ve karar kayıtları değiştirilmez. Betik otomatik silme işlemi yapmaz.
- **Katalog:** yeni ürün sınıfı/API/DB/bağımlılık yok; bakım/doğrulama çalışma aracı, `tests/integration/w8_unified_u3.py`, `product/SOURCE_MANIFEST.json`, `ui-p10j16-office-composition.test.cjs` ve Windows test delilleriyle ilişkilendirilmiştir. Kaynak kod, test kanıtı, tasarım ve ürün kabulü birbirine karıştırılmaz.

## Devir — doğrulanmış mevcut kayıt
- PR36 hedef Windows regresyonu **8/8 PASS_ACTUAL_LOCAL**; **yeni tam original C04/C06/C07/C08 henüz kullanıcı tarafından koşturulmadı**.
- Bağımsız C05/owner güvenlik **HOLD**; kanonik W8 kabulü **3/8 → 3/8 (değişim 0)**; ağırlıklı geliştirme **HESAPLANAMADI**. Genel proje yüzdesi üretilmez.
- Sonraki gerçek görev, kullanıcı Windows yeni `PR36_W8_FRESH` JSON/log kanıtını doğrulamak; başarı halinde ayrı sahip/IV kabulü ve kontrollü entegrasyon aday değerlendirmesi. Otomatik merge/CI/security activation yok.

- Yürütme sona erdiğinde (başarılı/başarısız) JSON raporuna kanıt olarak `native_log_sha256`, `native_log_bytes` ve `original_PR35_source_hashes_preserved` eklenir; Python sürecinin geçici değişkenleri hata durumunda da geri alınır. Bu yardımcı değişikliğinin kendisi tam Windows test sonucu değildir.
