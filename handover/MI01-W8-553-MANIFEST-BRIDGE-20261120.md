# Devir — MI-01 W8 553 manifest bağlama adayı

**Eylem ve neden:** MI01 tam 553 W8 için eski 539 manifest kimlik uyuşmazlığını kaynak ve Git blob düzeyinde doğruladım. Eski çalışma dosyasına dokunmadan iki yeni dosyalı izole `review/mi01-w8-553-manifest-bridge-20261120` inceleme dalını oluşturdum, GitHub commit `ebee7053f55e9c3dd1c70053a2c3244929723906`; yerelde 6/6 *yardımcı* test PASS.

**Sınır:** Tam W8 / prepare / wheelhouse / approval / install / build / original browser smoke hiç çalıştırılmadı. Başka sohbetin bu anda çalıştığını gösteren canlı kayıt yok, ama MI-01 sahibi ve PR14 ayrıdır; onların dosyalarını üzerine yazma. Açık bloklar: W8 C04-C08, bağımlılık fingerprint/owner, exact checkout ve browser. Aday ürün kabulü değildir.

**Yapılacak:** MI-01 kaynak sahibi exact 553 branch `a80932b6d5e99667889dfaa25b682feb267c6cba` üzerine inceleme dalı üzerinden (otomatik merge değil) adaptörü gözden geçirir; W8 clean checkout audit + wheelhouse prepare; hash/metadata/lisans/zafiyet owner signoff; sonrasında original install/test/smoke. GitHub Actions için yeni izin gerek, mevcut PR4/6 istisnaları genişletilemez.

**Geri dönüş:** `review/mi01-w8-553-manifest-bridge-20261120` inceleme dalını normal sil/revert, product-dev/main ve eski W8 değişmedi.

**İlerleme:** Operasyonel W8 3/8 -> 3/8, ağırlıklı MI-01 HESAPLANAMADI, ürün kabul delta 0.
