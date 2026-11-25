# Teknik katalog — 0163 / R9 delta

Kaynak adayı, gerçek çalışma yok. R8 üzerinde 3 yeni dosya + 1 replacement; manifest 125 kaynak kaydı. API/DB/event/bağımlılık sürümü değişmedi.

|Dosya|Semboller|İşlev|
|---|---|---|
|product/ai-company-os-frontend/components/dashboard/AgentDetail.tsx|Role (type), RoleButton, AgentDetail (default)|controlled role selection and details|
|product/ai-company-os-frontend/components/dashboard/OfficePanel.tsx|SnapshotFloor (type), Display (type), OfficePanel (default)|controlled floor/display and isolated static geometry|
|product/ai-company-os-frontend/components/dashboard/OperationPanel.tsx|panelTabs, Panel (type), OperationPanel (default)|controlled operation tabs|
|product/ai-company-os-frontend/features/ceo-dashboard/Dashboard.tsx|Dashboard (default), DashboardView, resetContext, changeFloor, changeDisplay, navigate, openStation, openRole, changeDetail, stationList|single presentation owner, controlled children|

## Bağımlılıklar
- product/ai-company-os-frontend/components/dashboard/AgentDetail.tsx: features/uiCatalog.json
- product/ai-company-os-frontend/components/dashboard/OfficePanel.tsx: react (type), next/link, office/scenes/OfficeScene, office/engine/geometry (type), fixtures/office.snapshot.json (type)
- product/ai-company-os-frontend/components/dashboard/OperationPanel.tsx: react (type)
- product/ai-company-os-frontend/features/ceo-dashboard/Dashboard.tsx: react, next/link, CorePreview, validateDemoLayout, core.preview.json, office.snapshot.json, company.catalog.json, uiCatalog.json, SnapshotStrip, MetricsStrip, OfficePanel, AgentDetail, OperationPanel

## Doğrulama ve hata teşhis
TSX parser 4/4, tip kontrolü ve browser NOT_RUN. 0162D D01–D12 açık, JOIN_HOLD. [Bakım ve rollback](../../docs/0163/MAINTENANCE_ROLLBACK.md). [JSON katalog](TECHNICAL_CATALOG_0163.json).
