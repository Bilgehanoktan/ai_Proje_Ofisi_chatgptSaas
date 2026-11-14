# Teknik katalog v1.18 — 0159-B
Yetkili geçmiş: docs/0158/TEKNIK_KATALOG_DELTA_v1_17.md; v1–v1.17 korunur. Yeni indeksler statik kaynaktan üretilmiştir; runtime kabulü değildir.
- FILE_CATALOG.json: 84 ürün kaynak kaydı (72 korunmuş, 12 yeni), releases/SOURCE_MANIFEST_0159B.json türevi.
- MODULE_CATALOG.json, CLASS_CATALOG.json, FUNCTION_CATALOG.json, DEPENDENCY_CATALOG.json: Python AST; FRONTEND_CATALOG.json: TS AST.
- API_CATALOG.json: 6 salt okunur D0 GET; DATABASE_CATALOG.json: R03 HOLD; EVENT_CATALOG.json: örnek olaylar; SECURITY_CATALOG.json: sınırlar.
- ERROR_CATALOG.json: statik aday literal indeks, eksiksiz runtime hata sözlüğü değil; TEST_CATALOG.json: 48 aday NOT_RUN; TRACEABILITY_MATRIX.json: 24 alan.
Teşhis: önce dosya hashini, sonra import/symbol, ilgili D/R kararı, hata ve test kaydını incele. Geri dönüş: 0159-A parent commit veya onaylı revert; eski grant/cache etkinleşmez. API, DB, bağımlılık pinleri değişmedi.
