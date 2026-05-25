# Backend QA — Half A (Exhaustive)

## Summary
- critical: 2 | high: 3 | medium: 4 | low: 5

## Critical
- **Missing `__init__.py` in Core Packages**: The following directories in `api/core/` are missing `__init__.py` files: `base/`, `manager/`, `registry/`, `migrations/`. This breaks `pkgutil.walk_packages` discovery and standard Python packaging conventions.
- **Duplicate `Note` Model**: There are two conflicting `Note` models:
  1. `api/apps/core/models.py` -> `Note` (table `erp_core_notes`, for document attachments).
  2. `api/apps/notes/models.py` -> `Note` (table `notes_note`, for a standalone notes app).

## High
- [api/core/auth/service.py:53] **Token Purpose Gap**: `get_current_user` and `get_portal_subscription` do not verify the `purpose` claim in JWT. A `password_reset` token could potentially be used to bypass authentication if the `sub` claim matches a username or tenant ID.
- [api/apps/crm/app.py, api/apps/asset/app.py] **Incomplete App Registration**: `CRM` and `Asset` apps do not use `autodiscover_models` and do not import `views`. This means their Views are not registered in the UI registry, and models are manually listed (anti-pattern per `aras.md`).
- [api/core/logic/installer.py:118] **Legacy `__title__` Usage**: The dynamic app installer still generates models with `__title__`, which is officially removed in favor of `View.title`.

## Medium
- [api/core/logic/auto_migrate.py] **Orphaned Tables**: `auto_migrate` iterates only over models defined in code. It detects and drops extra columns, but does NOT drop orphaned tables (e.g., `saas_customer_signup` will persist in DB forever).
- [api/core/logic/router_factory.py:183,322,352,390,438] **Bare `except:` blocks**: Multiple instances of bare `except:` catching everything without specific handling or logging.
- [api/core/logic/discovery.py] **Ungated Debug Prints**: `discovery.py` uses `print()` for route registration and error logging instead of the framework's logging system.
- [api/apps/base/saved_filter_router.py:20, api/apps/config/vocabulary_router.py:14] **Pydantic Deprecation**: Class-based `config` is deprecated in Pydantic V2.

## Low
- [api/core/lib/storage.py:10] **Hardcoded Path**: `UPLOAD_DIR = "storage/uploads"` is a hardcoded relative path.
- [api/apps/accounting/app.py] **Manual Router Wiring**: `Accounting` app manually wires `accounting_api_router`, while `RouterFactory` should ideally handle standardized endpoints.
- **Missing Views**: Child models like `InflowInvoiceLine`, `PaymentAllocation`, and `Stage` do not have explicit Views. While often intended, `JournalEntryLine` *has* a View, creating an inconsistency in when line items get views.
- **`core` app anomaly**: `api/apps/core/` exists and contains the document-linked `Note` model, but has no `app.py`. It functions as a model container rather than a full framework app.

---

## SaaS Consistency Check
- **Option-C verified**: `Subscription` model contains `email`, `company_name`, `full_name`, `phone`, `notes`.
- `approve` action correctly creates `User` via `User.hash_password`.
- `approve` action returns `display_token` as a `/portal/setup?token=...` link.
- **Frontend Alignment**: Verified `CustomerSignup.tsx`, `CustomerPortal.tsx`, and `CustomerPortalSetup.tsx`. 
  - Payloads for `/signup`, `/portal/login`, and `/portal/setup` match backend DTOs.
  - `CustomerPortalSetup.tsx` correctly parses `token` from URL params.
  - `CustomerSignup.tsx` ignores `subscription_id`/`signup_id` in response (safe but incomplete).

---

## Applications Audit

### 1. Accounting (`api/apps/accounting/`)
- **Models**: `Account`, `FiscalPeriod`, `JournalEntry`, `JournalEntryLine`, `InflowInvoice`, `InflowInvoiceLine`, `InflowInvoiceCharge`, `OutflowInvoice`, `OutflowInvoiceLine`, `OutflowInvoiceCharge`, `Payment`, `PaymentAllocation`, `GoodsReceiptNote`, `GoodsReceiptLine`.
- **Table Prefix**: `erp_accounting` (Consistent).
- **Views**: `AccountView`, `FiscalPeriodView`, `JournalEntryView`, `JournalEntryLineView`, `InflowInvoiceView`, `OutflowInvoiceView`, `PaymentView`.
- **Missing Views**: All line item and charge models except `JournalEntryLine`.

### 2. Asset (`api/apps/asset/`)
- **Models**: `AssetCategory`, `Asset`.
- **Table Prefix**: `erp_asset` (Consistent).
- **Views**: `AssetCategoryView`, `AssetView`.
- **Issues**: Fails to use `autodiscover_models` and `import views` in `app.py`.

### 3. Base (`api/apps/base/`)
- **Models**: `SavedFilter`.
- **Table Prefix**: `erp_base` (Consistent).
- **Bases**: `DocumentBase`, `LineItemBase`, `MasterDataBase`, `ConfigBase`, `ErpBase` (All abstract).
- **Routers**: `saved_filter_router`, `series_router`.

### 4. Config (`api/apps/config/`)
- **Models**: `Organization`, `Currency`, `Uom`, `PriceType`, `Charge`, `ExchangeRate`, `Setting`, `ModeOfPayment`, `OrganizationPaymentAccount`, `PrintTemplate`, `Notification`, `OrganizationVocabulary`, `OrganizationPostingRule`.
- **Table Prefix**: `erp_config` (Consistent).
- **Views**: `OrganizationView`, `CurrencyView`, `UomView`, `PriceTypeView`, `ChargeView`, `ExchangeRateView`, `SettingView`, `ModeOfPaymentView`, `PrintTemplateView`, `NotificationView`.

### 5. Core (`api/apps/core/`)
- **Models**: `Note` (table: `erp_core_notes`).
- **Issues**: No `app.py`. Redundant with `api/apps/notes`.

### 6. CRM (`api/apps/crm/`)
- **Models**: `Pipeline`, `Stage`, `Lead`, `Activity`.
- **Table Prefix**: `erp_crm` (Consistent).
- **Views**: `PipelineView`, `LeadView`, `ActivityView`.
- **Issues**: Fails to use `autodiscover_models` and `import views` in `app.py`. `Stage` view is missing.

---

## Verbatim Command Outputs

### 1. Import Check
```
cd api && python -c "import apps.saas, apps.web, apps.accounting, apps.asset, apps.config, apps.core, apps.crm, apps.base; print('ok')"
ok
```

### 2. Pytest Collection
```
cd api && python -m pytest -q --collect-only 2>&1 | tail -40
=============================== warnings summary ===============================
apps/base/saved_filter_router.py:20
  /Users/aras/Dev/aras/api/apps/base/saved_filter_router.py:20: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class SavedFilterResponse(BaseModel):

apps/config/vocabulary_router.py:14
  /Users/aras/Dev/aras/api/apps/config/vocabulary_router.py:14: PydanticDeprecatedSince20: Support for class-based `config` is deprecated, use ConfigDict instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2 Migration Guide at https://errors.pydantic.dev/2.13/migration/
    class VocabularyItem(BaseModel):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
```
