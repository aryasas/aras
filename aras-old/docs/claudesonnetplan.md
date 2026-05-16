Open-Core Split: Aras ERP Licensing Engine + Community Edition

 Context

 Aras akan mengadopsi model Open-Core 3-tier:
 - Aras Framework (arasCore) → MIT/Apache-2.0, gratis
 - Aras ERP Community Edition → AGPL/BSL, self-host gratis, 1 user, modul terbatas
 - Aras ERP Pro/SaaS → Proprietary/Subscription, unlimited users, semua modul

 Saat ini tidak ada sistem licensing sama sekali. Semua modul selalu aktif tanpa pembatasan.

 Scope implementasi: Fase 1+2 — Licensing Engine (DB + License Server) + CE manifest split.

 ---
 CE vs Pro Feature Split

 Community Edition (Gratis)

 ┌───────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
 │   Modul   │                                                           Resource yang Diizinkan                                                           │
 ├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ erp_pos   │ POS terminal, sessions, shift entries                                                                                                       │
 ├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ erp_stock │ Product, UOM, UOM-conversion, Product-category, Product-bundle, Price-type, Price-list-item, Promo-bundle, Stock-movement (single location) │
 ├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ erp_crm   │ Customer, Contact saja (bukan Lead/Pipeline/Activity)                                                                                       │
 ├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ erp_acc   │ Account (Chart of Accounts), Journal Entry, Sales Invoice, Purchase Invoice, Payment                                                        │
 ├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ erp_core  │ Company (single only), Currency, Sequence, Setting                                                                                          │
 ├───────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
 │ Reports   │ Sales Report, Purchase Report, P&L Statement                                                                                                │
 └───────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

 Pro Only (Semua CE + tambahan)

 ┌───────────────────────────────────────────────────────┐
 │                     Fitur Premium                     │
 ├───────────────────────────────────────────────────────┤
 │ Multi-company (parent_id hierarchy)                   │
 ├───────────────────────────────────────────────────────┤
 │ Multi-location stock (StockLocation, ProductLocation) │
 ├───────────────────────────────────────────────────────┤
 │ Delivery/Logistics (DeliveryTrip, DeliveryOrder)      │
 ├───────────────────────────────────────────────────────┤
 │ CRM Pipeline (Lead, Pipeline, Stage, Activity)        │
 ├───────────────────────────────────────────────────────┤
 │ Reconciliation, FX Rate, Bank management              │
 ├───────────────────────────────────────────────────────┤
 │ Custom Fields                                         │
 ├───────────────────────────────────────────────────────┤
 │ Print Templates                                       │
 ├───────────────────────────────────────────────────────┤
 │ Audit Trail                                           │
 ├───────────────────────────────────────────────────────┤
 │ Advanced Reports                                      │
 ├───────────────────────────────────────────────────────┤
 │ Unlimited users                                       │
 └───────────────────────────────────────────────────────┘

 ---
 Implementation Plan

 Step 1: DB Models untuk Licensing

 File: arasCore/lib/licensing/models.py (new)

 Buat 2 tabel:
 class ArasLicense(ArasModel):
     __tablename__ = "aras_license"
     edition = db.Column(db.String(20), default="community")  # "community" | "pro" | "enterprise"
     instance_id = db.Column(db.String(64), unique=True)       # UUID untuk instance ini
     license_key = db.Column(db.String(256), nullable=True)    # Encrypted license key dari server
     seats = db.Column(db.Integer, default=1)                  # Max active users
     valid_until = db.Column(db.Date, nullable=True)           # None = lifetime/community
     last_verified = db.Column(db.DateTime, nullable=True)     # Kapan terakhir cek ke server
     is_verified = db.Column(db.Boolean, default=False)        # Verified by license server

 class ArasFeatureGate(ArasModel):
     __tablename__ = "aras_feature_gate"
     feature_key = db.Column(db.String(64), unique=True)       # e.g. "erp.crm.lead"
     min_edition = db.Column(db.String(20), default="pro")     # "community" | "pro" | "enterprise"
     is_enabled = db.Column(db.Boolean, default=True)          # Override per-instance

 Migration: arasCore/lib/migrations/m017_licensing.py (new)

 Step 2: LicenseManager

 File: arasCore/lib/licensing/manager.py (new)

 class LicenseManager:
     EDITION_RANK = {"community": 0, "pro": 1, "enterprise": 2}

     def get_license() -> ArasLicense    # Fetch/cache current license
     def get_edition() -> str            # "community" | "pro" | "enterprise"
     def is_pro() -> bool
     def can_use(feature_key: str) -> bool   # Check feature_key against edition
     def check_seat_limit() -> bool      # True if active users < seats
     def verify_online(license_key) -> dict  # POST ke Aras License Server
     def _generate_instance_id() -> str  # UUID stabil berdasarkan machine

 Feature keys yang akan digunakan:
 - "erp.crm.lead" — Lead/Pipeline/Activity
 - "erp.stock.multi_location" — StockLocation, ProductLocation
 - "erp.stock.delivery" — DeliveryTrip, DeliveryOrder
 - "erp.acc.reconciliation" — Reconciliation
 - "erp.core.multi_company" — Company parent_id
 - "erp.core.custom_fields" — Custom Fields
 - "erp.users.unlimited" — > 1 active user

 Step 3: Feature Gate di Manifest

 File: aras/erp/manifest.py (modify)

 Tambah parameter pro_only=True ke ResourceDef yang premium, dan gunakan LicenseManager untuk filter:

 # Di arasCore/lib/services/app_helper.py — tambah field ke ResourceDef:
 @dataclass
 class ResourceDef:
     ...
     feature_key: str = None   # e.g. "erp.crm.lead" — None = always available

 # Di aras/erp/manifest.py — tandai resource premium:
 ResourceDef("crm/lead", CrmLead, feature_key="erp.crm.lead"),
 ResourceDef("crm/pipeline", CrmPipeline, feature_key="erp.crm.lead"),
 ResourceDef("stock/location", StockLocation, feature_key="erp.stock.multi_location"),

 Step 4: Filter di build_sidebar_menu() dan Blueprint Loader

 File: arasCore/admin/services.py — fungsi build_sidebar_menu() (L253)

 from arasCore.lib.licensing.manager import LicenseManager

 def build_sidebar_menu():
     ...
     # Filter resources berdasarkan feature_key
     visible_resources = [
         r for r in resources
         if r.feature_key is None or LicenseManager.can_use(r.feature_key)
     ]

 File: arasCore/lib/services/blueprints.py — fungsi _register_helper() (L40)

 Saat mount admin route, skip resources yang tidak diizinkan oleh license.

 Step 5: Seat Limit Check

 File: arasCore/admin/routes/__init__.py — before_app_request hook

 @admin_bp.before_app_request
 def before_request():
     g.user = current_user
     g.license = LicenseManager.get_license()  # Inject ke semua template
     ...

 File: arasCore/admin/routes/users.py — users_new()

 Cek seat limit sebelum aktivasi user baru:
 if not LicenseManager.check_seat_limit():
     flash("Seat limit reached. Upgrade to Pro for unlimited users.", "error")
     return redirect(...)

 Step 6: License Management UI

 File: arasCore/admin/routes/settings.py — tambah route license_settings()

 Halaman /admin/settings/license/ menampilkan:
 - Edition saat ini (Community / Pro)
 - Instance ID (untuk registrasi)
 - Seats used / seats total
 - Valid until date
 - Input field untuk activate Pro license key
 - Button "Verify Online"

 Template: templates/admin/setting/setting_license.html (new)

 Step 7: Middleware — Block API juga

 File: arasCore/lib/api_handler.py — dalam register_api_model() dan request handlers

 Tambah check di universal API agar resource dengan feature_key yang tidak diizinkan return 403 Forbidden.

 ---
 Critical Files to Modify

 ┌──────────────────────────────────────────────┬──────────────────────────────────────────────────────────┐
 │                     File                     │                          Action                          │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/licensing/models.py             │ CREATE — ArasLicense + ArasFeatureGate models            │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/licensing/manager.py            │ CREATE — LicenseManager singleton                        │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/licensing/__init__.py           │ CREATE — exports                                         │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/migrations/m017_licensing.py    │ CREATE — migration for new tables                        │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/__init__.py                         │ MODIFY — import m017, call licensing init after DB setup │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/services/app_helper.py          │ MODIFY — add feature_key field to ResourceDef            │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/admin/services.py L253              │ MODIFY — filter by feature_key in build_sidebar_menu     │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/services/blueprints.py L40      │ MODIFY — skip locked resources in _register_helper       │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/admin/routes/__init__.py            │ MODIFY — inject g.license in before_app_request          │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/admin/routes/users.py               │ MODIFY — seat limit check on user activation             │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/admin/routes/settings.py            │ MODIFY — add license_settings route                      │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ arasCore/lib/api_handler.py                  │ MODIFY — block locked resources in API                   │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ aras/erp/manifest.py                         │ MODIFY — add feature_key to premium ResourceDefs         │
 ├──────────────────────────────────────────────┼──────────────────────────────────────────────────────────┤
 │ templates/admin/setting/setting_license.html │ CREATE — license management UI                           │
 └──────────────────────────────────────────────┴──────────────────────────────────────────────────────────┘

 ---
 Execution Order (Sequential)

 1. Create arasCore/lib/licensing/ package (models + manager + init)
 2. Create migration m017 + register di arasCore/__init__.py
 3. Add feature_key field ke ResourceDef dataclass
 4. Modify build_sidebar_menu() — filter by license
 5. Modify _register_helper() — skip locked blueprints
 6. Tag premium ResourceDefs di aras/erp/manifest.py
 7. Add seat limit check di users route
 8. Add g.license di before_app_request
 9. Block locked resources di API handler
 10. Create license settings UI

 ---
 Verification

 1. Set edition="community" di DB → Lead/Pipeline, multi-location, reconciliation hilang dari sidebar + API return 403
 2. Activate Pro license key → semua fitur muncul kembali
 3. Community + 1 user sudah aktif → aktivasi user ke-2 ditolak
 4. /admin/settings/license/ menampilkan info edition + form aktivasi
 5. Jalankan: flask shell → from arasCore.lib.licensing.manager import LicenseManager; print(LicenseManager.get_edition())

 ---
 Out of Scope (Fase ini)

 - Actual license server infrastructure (hanya stub endpoint lokal untuk development)
 - Payroll module (belum ada)
 - CMS / Online Store module (belum ada)
 - Billing/payment integration
 - Multi-tenant SaaS infrastructure
