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

## 2026-11-21 — PR36 gerçek Windows bağımlılık farkı ve R2 okuma aracı

**Kullanıcının gerçek Windows PowerShell 5.1 çıktısı:**
- Disk ön kontrolü: C: **3.36 GiB** / E: **6.38 GiB** boş (çalışma *öncesi*).
- Özgün PR35 552 kaynak SHA256 denetimi **PASS**; özgün W8 runner `E:\\AIOS\\W8\\W8_AGENTFIX_LOCAL_20261121_002919\\source\\tests\\integration` altında bulundu.
- PR36 552 kaynak/manifest Git blob yeniden üretimi **PASS**.
- Yeni çalışma: `E:\\AIOS\\W8\\PR36_W8_FRESH_20261121_010329`.
- **G3:** özgün PR36 552 kaynak audit exit=0.
- **C04 hazırlığı:** özgün yeni `prepare` exit=0, ancak `REVIEW.json` dosyaları karşılaştırıldığında `manifest_blob` dışındaki alanlar da farklı: **`REVIEW_DEPENDENCY_DRIFT_HOLD`**. Bu farkın kesin alanı/sürümü henüz okunmadı. C04 **prepare PASS**, fakat yeni bağımlılık onayı **HOLD**.
- **C06:** yeni kurulum **NOT_RUN**; **C07 tam test/Next.js build NOT_RUN**, **C08 browser NOT_RUN**. PR36 hedef Windows 8/8 PASS önceki delil olarak korunuyor. **C05 bağımsız HOLD**, W8 kabulü **3/8 değişmedi**.
- Kullanıcı Windows çıktı markerı `ORIGINAL_STAGE_SOURCE_HASHES_PRESERVED` gösteriyor; eski stage test ve manifest SHA256'ları doğrulanmış.
- **Önemli uygulama hatası:** R1 yardımcısı `REVIEW_DEPENDENCY_DRIFT_HOLD` sonrasında `return` ile *sıfır* çıkış kodu dönebilir. Dolayısıyla PowerShell wrapper `PR36_VALIDATION_HOLD` üretmemiş olması **başarı değildir**. Kaynak/bağımlılık kilidi yine güvenli şekilde durmuştu. R2 bu yanlış yeşili giderir.
- **R2 salt okunur teşhis dosyası:** `AIOS_W8_PR36_FRESH_WINDOWS_VALIDATION_R2_20261121.py`, SHA256 `9751b0068f10f16dbfa1a7de143d48debe926a4dfefdc847d89f3902e2856808`, **28,578 bayt**; oluşturulan conversation artifact, GitHub ürün kaynaklarının parçası değil. Yeni `--mode review-diff --run-root E:\\AIOS\\W8\\PR36_W8_FRESH_20261121_010329` salt okunur şekilde eski/yeni `REVIEW.json` alanlarını, Python wheel SHA'larını ve `python.lock` farklarını raporlar; hiçbir paketi kurmaz/silmez, izin değiştirmez. R2 ayrıca bir sonraki `--mode run` çağrısında dependency drift varsa **nonzero exit** döndürür. R2'nın Python AST, CLI --help, PR36 exact-source yeniden kurma statik kontrolleri PASS; **Windows R2 çalışması henüz NOT_RUN**.
- R2 teşhis çalıştırılması için kullanıcı önce indirilen dosyanın SHA256'sını doğrulamalı, ardından `py -3 $file --mode review-diff --run-root 'E:\\AIOS\\W8\\PR36_W8_FRESH_20261121_010329'` çalıştırmalı. Eski R1 `--mode run` tekrar çağrılmamalı. Mevcut `stage` / `REVIEW.json` / `.log` / `.json` korunmalı.
- Bir sonraki karar, **gerçek fark alanlarına** göre: sadece ortam metadatasıysa yeterli doğrulama ve yeni fingerprint; wheel/lock SHA veya paket sürümü farkıysa eski onaylı wheelhouse kilidini koruyan kaynakta yetkili ve kanıtlı re-review gerekir. Fark görülmeden onayı otomatik yeniden kullanma veya `REVIEW.json` elle düzeltme **YASAK/HOLD**.

**Teknik katalog etkisi:** Backend/API/DB, runtime, ürün UI veya bağımlılık sürümü güncellenmedi. Yalnızca W8 dış test yardımcısının durum kodu/doğrulama aracına R2 bakım düzeltmesi, kanıt/handover ve hata teşhisi kaydedildi. Eski sürümler ve kararlar aynen korunur.

## 2026-11-21 — R2 dependency-review root-cause: Python ABI cp313 vs cp314

**Genuine native user output** from `Yapıştırılan metin(20261121-101607).txt` SHA256 `0af80d2c80d324fe5eccc5631c1134f5edd16465e4b1a4e9cf3f08ec887c00bc` (R2 `review-diff` **READ_ONLY_COMPLETE**); inputs are the old PR35 and new PR36 `REVIEW.json` plus Python locks in their recorded E: stage paths.

- `manifest_blob` changes exactly as intended: PR35 `2d1d0bf94d464ffe79d8072453a2e19722485854` -> PR36 `9660da1104617b4764d5f1e32009e4e3405b47f8`. **This is NOT a dependency change.**
- `node`, `npm_lock_sha256`, `npm_packages`, `platform` all **SAME**; `test-tools.txt` SHA **SAME**.
- `python`: **3.13.17 -> 3.14.3** because R2/R1 were invoked with `py -3`, which selected the machine's *newer default Python 3.14.3*. The W8 adapter uses its Python process's `sys.executable` for fresh C04 package download and all subsequent subprocess stages; PR36 product code/requirements did not change.
- Wheels are **ABI-specific**. Four packages changed from `cp313` -> `cp314` despite identical *package versions*: `cffi 2.1.1`, `greenlet 3.5.6`, `pydantic_core 2.50.5`, `rpds_py 2026.9.1`; 8 filenames differ (old+new for each).
- Python lock SHA changed as a **consequence** of the four ABI wheel hash changes: PR35 `dfc5da1b553c71ae209d31e70209de699503973dbc8146ba611e35703f5367a5`; PR36/Python3.14 `a74aacd1df83144811d19f7ccc04517905325764cc4d994738f373f5044b428f`. All package version strings in the displayed lock diff were unchanged.
- `REVIEW_DIFFERENT_FIELD_COUNT 4` = `manifest_blob`, `python`, `python_lock_sha256`, `wheels`. R2 diagnostic did not install packages, modify sources or permissions.

**Minimal controlled remediation:** DO NOT alter product requirements, Python packages, manifests, REVIEW files, checksum gates or the existing two Windows stages. Reuse the already SHA-pinned **R2 helper unchanged** with *explicit Python **3.13.17*** using `py -3.13` in a **new** fresh PR36 stage. First read-only assert `sys.version_info[:3] == (3,13,17)` (not just 3.13), and C>=2GiB/E>=4GiB. If py launcher lacks exact 3.13.17, **HOLD** and report `py -0p`; do not silently fall back to 3.14. If the 3.13-run C04 regenerated wheel inventory differs for any other reason, original R2 fail-closed compares all old/new `REVIEW.json` fields other than intended manifest and **HOLD** without installing. No manual writing to `python.lock` or `REVIEW.json`.

User PowerShell 5.1 direct commands (not an unsigned PS1, no execution policy adjustment):

```powershell
& {
  $ErrorActionPreference='Stop'
  $file=Join-Path $env:USERPROFILE 'Downloads\AIOS_W8_PR36_FRESH_WINDOWS_VALIDATION_R2_20261121.py'
  $expected='9751b0068f10f16dbfa1a7de143d48debe926a4dfefdc847d89f3902e2856808'
  if (!(Test-Path -LiteralPath $file) -or
      (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
      throw 'PR36_R2_HELPER_INTEGRITY_HOLD'
  }
  & py -3.13 -c 'import sys; print(sys.version); assert sys.version_info[:3] == (3,13,17), "PYTHON_3_13_17_REQUIRED"'
  if ($LASTEXITCODE -ne 0) { throw 'PYTHON_3_13_17_NOT_AVAILABLE_HOLD' }
  if ((Get-PSDrive C).Free -lt 2GB -or (Get-PSDrive E).Free -lt 4GB) { throw 'DISK_PREFLIGHT_HOLD' }
  $chrome='C:\Program Files\Google\Chrome\Application\chrome.exe'
  if (Test-Path -LiteralPath $chrome) {
      & py -3.13 $file --mode run --chromium $chrome
  } else {
      & py -3.13 $file --mode run
  }
  if ($LASTEXITCODE -ne 0) { throw 'PR36_FULL_RUN_HOLD_CHECK_NEW_STATUS_AND_LOG' }
}
```

**Expected stages and measurement:** new `E:\AIOS\W8\PR36_W8_FRESH_<new_timestamp>`, fresh real G3/C04; if identical lock/wheels/3.13 interpreter, R2 reports `C04_REVIEW_MATCH_EXCEPT_PR36_MANIFEST_PASS`, followed by C06 offline installation and C07 full original Next.js build; C08 real browser only if explicitly supplied Chrome path exists. New raw `PR36_W8_STATUS.json` and `PR36_W8_NATIVE_FULL.log` must be reviewed *before* any state is changed to PASS. **As of this document no new 3.13.17 run has occurred**; C06/C07/C08 remain NOT_RUN, independent C05 HOLD. W8 acceptance 3/8 unchanged; weighted dev HESAPLANAMADI.

**Source catalogue and rollback:** No product/module/API/DB/event/dependency source changed; only W8 execution selection is corrected by a version guard. Old PR35/Python3.13 stage and aborted PR36/Python3.14 stage retained untouched for evidence. Existing R2 verified SHA256 `9751b0068f10f16dbfa1a7de143d48debe926a4dfefdc847d89f3902e2856808`. Future failure means stop at the exact stage, inspect the new native log/status rather than trying to suppress a pin error.


## 2026-11-21 — Exact Python 3.13.17 fresh PR36 attempt: dependency HOLD remains

**New authentic user PowerShell 5.1 evidence**: user big-paste `Yapıştırılan metin(20261121-101941).txt`, 16,896 bytes, SHA256 `d42f5819d0a03c4e3e9c5e78f3118845721b405cc8f0b45390d167c69dbb0988` (uploaded conversation file; native log/JSON not independently read back).
- Python command `py -3.13 -c ...` reported **3.13.17**, exact version guard **PASS**.
- Before full run: C free **2.81 GiB**, E free **6.33 GiB**, capacity preflight PASS. These figures are *pre-run*, not post-prep.
- Same R2 helper with SHA256 `9751b0068f10f16dbfa1a7de143d48debe926a4dfefdc847d89f3902e2856808` was successfully verified and executed as `py -3.13 ... --mode run`.
- Fresh isolated stage `E:\AIOS\W8\PR36_W8_FRESH_20261121_131906`; prior PR35 original source 552 SHA256 **PASS**, exact original W8 runner **FOUND**, PR36 reconstructed Git blob pins **PASS**.
- Real `G3_PR36_552_SOURCE_AUDIT exit=0` and `C04_PR36_FRESH_PREPARE exit=0`.
- **`REVIEW_DEPENDENCY_DRIFT_HOLD` still occurred despite exact Python 3.13.17.** Old/new review path printed; **the precise remaining field(s) have not yet been inspected**. Do **not** infer why the new 3.13.17 wheel/PyPI set still differs; this is separate from the already confirmed earlier Python-3.14 ABI mismatch.
- Corrected R2 fail-closed status was proven: `W8_PR36_HOLD: RuntimeError REVIEW_DEPENDENCY_DRIFT_HOLD`, outer PowerShell `PR36_FULL_RUN_HOLD_CHECK_LOG`. The old R1 zero-exit defect did **not** recur.
- **C06 PR36 NOT_RUN; full C07/Next build NOT_RUN; C08 browser NOT_RUN.** Old PR35 C04/C06 PASS remain historical for old pinned stage, PR36 scoped Windows P10J16 **8/8 PASS**, independent C05 security **HOLD**. W8 canonical product acceptance **3/8 → 3/8**, weighted development **HESAPLANAMADI**. No product code, source branch, CI, security policy or authority change.

**Next required diagnostic (READ ONLY):** reuse original exact R2 helper, select `--mode review-diff --run-root 'E:\AIOS\W8\PR36_W8_FRESH_20261121_131906'` with SHA pin; prints *this* stage's field-by-field old/new `REVIEW.json` and Python lock/wheel hashes. Never rerun `--mode run` or mutate `REVIEW.json`/wheelhouse until the actual remaining difference is observed, classified and owner-reviewed. If it is resolution drift (new releases), plan an independent isolated **exact prior approved 3.13 wheelhouse** replay with integrity check and new manifest approval, not a bypass. If only metadata differs, examine R2 comparator before any mutation. Preserve both prior stages and native evidence. Update central record and PR #36 handover with the actual diff; no user decision repeated.

**Current log locations:** `E:\AIOS\W8\PR36_W8_FRESH_20261121_131906\PR36_W8_STATUS.json` and `PR36_W8_NATIVE_FULL.log`. No independent hash of those files received yet. Rollback is retaining all previous source and stage directories; no deletion performed.


## 2026-11-21 — Certifi-only wheel resolution drift; pinned PR35 graph reuse R3

### Confirmed evidence, not inferred
Actual native Windows PowerShell 5.1 `R2 --mode review-diff` output on **exact** 3.13.17 PR36 source run `E:\AIOS\W8\PR36_W8_FRESH_20261121_131906`:
- PR36 intended source-only `manifest_blob` change `2d1d0bf94d464ffe79d8072453a2e19722485854` → `9660da1104617b4764d5f1e32009e4e3405b47f8`.
- **SAME** `node`, `npm_lock_sha256`, `npm_packages`, `platform`, `python` (3.13.17), `test-tools.txt`; no differences in other 27 Python wheel versions/hashes in output.
- **Only dependency resolution drift:** old approved `certifi==2026.10.23` wheel `certifi-2026.10.23-py3-none-any.whl` SHA256 `e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1` vs new downloaded `certifi==2026.11.20`, wheel `certifi-2026.11.20-py3-none-any.whl` SHA256 `7422df25243767b9877031a2248cb14d09ddac9beee846f4cef3d5c9191d488f`. No other locked-package line differs.
- Old PR35 `python.lock` SHA256 `dfc5da1b553c71ae209d31e70209de699503973dbc8146ba611e35703f5367a5`; newer PR36 C04 Python3.13 `python.lock` SHA256 `523b06d49b2069d072801a095f9f77d6a27aa65e7e3b95e7360de5ed16bad461`. Three `REVIEW.json` fields differ: **manifest_blob** (intended), **wheels** (only certifi), and **python_lock_sha256** (only certifi).
- `REVIEW_DIFFERENT_FIELD_COUNT 3`, `READ_ONLY_REVIEW_DIFF_COMPLETE_NO_INSTALL_NO_SOURCE_MUTATION`. Therefore **the 3.13.17 fix is confirmed** and repeated PyPI dependency resolution remains non-deterministic; no API, product code, or package specification change is required.

### Existing dependency graph reuse, not an upgrade/waiver
New separate **local/dev helper artifact**, `AIOS_W8_PR36_CERTIFI_PIN_REPLAY_20261121.py`: **17,000 bytes; SHA256 `9b69846def5ebd9be6bd75b0945c65b63c3ca4f13d9bb4cc032de1908bb86b4a`**. This artifact is delivered in the conversation and is *not* an automatically deployed GitHub source file.

- Uses already approved original PR35 `REVIEW.json` SHA256 `bac9b49d277f7bf8509d928f2b4ed06aab4cbfd82ea0f450349db9998d08f403`, old `python.lock` and exact SHA-pinned 28-wheel inventory, **without taking any new package versions**. Also checks the PR36 prepared source's 552 product/manifest pins, original P10J24 and U3 adapter blob pins, and exact R2 SHA256 `9751b0068f10f16dbfa1a7de143d48debe926a4dfefdc847d89f3902e2856808`.
- **Fail closed** if source/input folders are symlinks, Python ≠ 3.13.17, C free less than 2 GiB or E less than 4 GiB, REVIEW fields differ beyond intended source manifest + certifi, any of the previously approved wheel SHA256 mismatch, or any `python.lock` line differs beyond certifi.
- Does **not mutate** PR35 successful stage, prior failed PR36 Python3.14 stage, or prior failed PR36 Python3.13 stage; copies already materialized PR36 source/prepare data to an **independent new folder** `E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_<timestamp>`. The copied stage omits *only* the newly resolved certifi wheel, generated `python.lock`, and generated `REVIEW.json`; inserts **byte-for-byte original approved `certifi` wheel and `python.lock`**. The changed source manifest remains PR36.
- Import **exact Git-pinned original PR36 W8 adapter** and call its native `lock_inventory(stage)`, `write_json`, `reviewed(stage, fingerprint)` for a **new** PR36 manifest-bound review record. Compare every other field except intended `manifest_blob` against the previously approved PR35 graph. The tool does **not** bypass original W8 review/approval checks or forge success markers.
- Runs original fresh G3 on this new copy, then original C06 **offline hash-locked install**, C07 full source regression/Next.js build; original C08 browser only if explicit local signed-off Chrome/Chromium executable exists. Independent C05 remains HOLD. No script execution policy change, main/product-dev merge, secret, PROD, CI edit, dependency upgrade or destructive cleanup.
- Original and aborted input stage integrity is checked again in the `finally` block. Output `PR36_CERTIFI_REPLAY_STATUS.json` and `PR36_CERTIFI_REPLAY_NATIVE.log` hold stage-specific real evidence including final SHA256/log size. The helper is **prepared, syntax/static + CLI + positive/negative certifi-delta fixture PASS**; **ACTUAL WINDOWS R3 C06/C07/C08 NOT_RUN until user executes and returns logs**.

User direct PowerShell 5.1 invocation:

```powershell
& {
  $ErrorActionPreference = 'Stop'
  $file=Join-Path $env:USERPROFILE 'Downloads\AIOS_W8_PR36_CERTIFI_PIN_REPLAY_20261121.py'
  $sha='9b69846def5ebd9be6bd75b0945c65b63c3ca4f13d9bb4cc032de1908bb86b4a'
  if (!(Test-Path -LiteralPath $file) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sha) { throw 'PR36_R3_FILE_SHA_HOLD' }
  $chrome='C:\Program Files\Google\Chrome\Application\chrome.exe'
  if (Test-Path -LiteralPath $chrome) {
      & py -3.13 $file --mode run --chromium $chrome
  } else {
      & py -3.13 $file --mode run
  }
  if ($LASTEXITCODE -ne 0) { throw 'PR36_R3_HOLD_READ_NEW_NATIVE_STATUS' }
}
```

### Rollback, acceptance, catalog and next
No existing project file is overwritten; only new temporary workspace is created and on failure **retained** for review/rollback (manual owner decision). Entire previous stages, architecture/decisions/security permissions stay unchanged. A success in G3/C06/C07/C08 would provide original **local test evidence**, still **not** independent C05, owner acceptance, main/product-dev merge or production approval. **W8 canonical product acceptance = 3/8 → 3/8 pending original fresh output; weighted development % = HESAPLANAMADI (no frozen denominators).** Product symbol/API/DB/event/contract/dependency catalogs unchanged; external testing tool and its provenance have been added to the W8 maintenance and handover runbook. If there is a remaining original test failure, investigate its exact `PR36_CERTIFI_REPLAY_NATIVE.log` instead of rerunning old successes. Do not count a hypothetical PASS.


## 2026-11-21 — Actual C06 PASS, C07 blocked at exact historical Core 0207

### Latest actual Windows evidence (user pasted PowerShell 5.1)
- Runner `AIOS_W8_PR36_CERTIFI_PIN_REPLAY_20261121.py` was SHA256 checked as `9b69846def5ebd9be6bd75b0945c65b63c3ca4f13d9bb4cc032de1908bb86b4a`, Python **3.13.17**, disk preflight C **2.12 GiB**, E **6.28 GiB**. The previously approved 28-wheel SHA256 inventory and exact certifi-only delta **PASS**. Old source `552/552` **PASS**.
- Fresh isolated stage `E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808` (previous old/failed stages preserved); new manifest-bound original W8 REVIEW fingerprint `341e179afda3e344ac32b3f4643860e44c7dd350cfb66ac59ac5edc98c79a1b3` **PASS** for original PR35-approved graph and intended PR36 source change only.
- `G3_PR36_EXACT_SOURCE_AUDIT exit=0` **PASS**. `C06_PR36_OFFLINE_LOCKED_INSTALL exit=0` **PASS ACTUAL WINDOWS** (hash-locked pip and npm original).
- `C07_PR36_ORIGINAL_FULL_TEST_AND_NEXT_BUILD exit=1`. Latest test suite TAP summary printed **43/43 PASS**, but the original W8 runner subsequently invokes the exact 0207 source-bound historical validator: `stage/.venv/Scripts/python.exe stage/tests/integration/run_core_0207.py --source <separate temp history> --report stage/core29-p10f.json` which **exited 1**. It is the first identified terminal failure at this point; full original C07 and Next.js build **not passed/reached**, C08 **NOT_RUN**.
- The core 0207 original `run_core_0207.py` Git blob `b019a5e60cfff4183b00e99f252ffe00bc164eda` always writes a JSON report (unless abnormal failure), with `status`, `reason`, and sometimes `dependency_versions`. **Report contents have not yet been supplied; do not mark direct dependency mismatch proven.**
- GitHub **source-level concrete incompatibility**: historical `tests/integration/core_0207_source_lock.json` Git blob `223f6fbd28cf4c428c07eb60dda4a36f644fa58c` requires `fastapi==0.163.0`, `starlette==1.10.0`, **`cryptography==46.0.4`**, `uvicorn==0.34.2`. Current PR36 `requirements-history-signatures.txt`/wheel lock is intentionally pinned to **`cryptography==50.0.2`** by PR34 security patch. This **may cause** `DIRECT_DEPENDENCY_PIN_MISMATCH` but requires exact `core29-p10f.json` `reason` before deciding how to fix. **Do not downgrade cryptography 50.0.2, tamper with historical 0207 lock/source, enable `--diagnostic-unpinned` as an acceptance shortcut, or reuse the failed C07 stage to claim fresh build PASS.**
- Native evidence paths: `E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808\PR36_CERTIFI_REPLAY_STATUS.json`, `PR36_CERTIFI_REPLAY_NATIVE.log`, `stage\core29-p10f.json`. The PowerShell excerpt and existing original stage are the only evidence presently read; JSON/log file byte SHA not independently received.
- Important preservation: `ORIGINAL_PR35_AND_FAILED_PR36_STAGES_PRESERVED` printed. R3 exits nonzero as intended, error `C07_PR36_ORIGINAL_FULL_TEST_AND_NEXT_BUILD_FAILED_EXIT_1`. Owner PR36 Windows P10J16 prior targeted 8/8 PASS remains valid, not a full C07 pass.

### Safe and minimal diagnostic — read only (no rerun)
```powershell
& {
    $ErrorActionPreference='Stop'
    $root='E:\AIOS\W8\PR36_W8_CERTIFI_LOCKED_20261121_132808'
    $report=Join-Path $root 'stage\core29-p10f.json'
    $venv=Join-Path $root 'stage\.venv\Scripts\python.exe'
    if (!(Test-Path -LiteralPath $report)) { throw 'CORE29_REPORT_NOT_FOUND' }
    Write-Output '=== ORIGINAL CORE 0207 RESULT ==='
    Get-Content -LiteralPath $report -Raw -Encoding UTF8 |
        ConvertFrom-Json | ConvertTo-Json -Depth 12
    Write-Output '=== STAGE DIRECT DEPENDENCY VERSIONS ==='
    & $venv -c 'import importlib.metadata as m,json; keys=("fastapi","starlette","cryptography","uvicorn"); print(json.dumps({k:m.version(k) for k in keys},indent=2))'
    if ($LASTEXITCODE -ne 0) { throw 'VENVDIRECT_PACKAGE_READ_FAILED' }
    Write-Output '=== NATIVE EVIDENCE HASHES ==='
    Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $root 'PR36_CERTIFI_REPLAY_NATIVE.log'),(Join-Path $root 'PR36_CERTIFI_REPLAY_STATUS.json'),$report |
        Select-Object Path,Hash
}
```

### Next correction boundary / QA rules
- If the report says `DIRECT_DEPENDENCY_PIN_MISMATCH`, classify as a **historical test runner/runtime environment contract collision**, not a real product test failure. Historical 0207 test needs an explicitly source-pinned, **isolated** compatible environment or an owner-reviewed **new** compatibility contract for current cryptography; the existing historical lock cannot be weakened to fit current crypto silently. Do not introduce vulnerable cryptography 46.0.4 into the current product runtime or shared 28-wheelhouse.
- If the report identifies another reason, analyze it before patching. Preserve current fresh stage (including C06 result) as immutable evidence. A follow-up original C07 build needs its own clean candidate/test construction; a failure does not create `BUILD_TEST_OK`.
- **Current W8 canonical product acceptance 3/8 → 3/8 (delta 0)**, weighted development **HESAPLANAMADI**, C05 independent security **HOLD**, C08 **NOT_RUN**. No product code/API/DB/schema or dependency changes in this turn; documentation/evidence and prospective bounded test-tool fix only.

### Rollback/handover
Original PR35 and both earlier PR36 failed runs, as well as newly generated R3 stage/locks/logs, remain available. No automatic deletion, force-push, CI workflows, privilege change or production action. Stage root and SHA pins are above for future independent replay. Next task is to classify actual `core29-p10f.json` and then open a scoped MI-01 owner candidate for historical source/environment bridge if required.
