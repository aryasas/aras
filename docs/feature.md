# Aras Framework Features

This document outlines the key features and architectural components of the Aras framework, including the recent **Aras Pro** enhancements.

## Core Architecture

-   **Metadata-driven Design:** Built on FastAPI and SQLAlchemy, enabling dynamic behavior and low-code extensibility through metadata.
-   **Hierarchical Structure:** A strict 3-level hierarchy ensures modularity and clear separation of concerns.
-   **Tiered Core Logic:** Prevents circular dependencies by organizing the core into Tiers (0: Utilities, 1: Logic, 2: API).

## Application Lifecycle Management

-   **`manage.py` CLI:** A central command-line interface for managing applications.
    -   `sync`: Synchronizes code-defined metadata to the DB registry and migrates the schema.
    -   `install <file>`, `uninstall <name>`, `activate`, `deactivate`, `discover`, `check`.

## Key Features & Capabilities

### Data & API Layer

-   **Generic CRUD Operations:** Automated generation of FastAPI endpoints via `RouterFactory`.
-   **Enhanced Querying:** Pagination, advanced filtering, and global search.
-   **Global Search & Command Center (Aras Pro):**
    -   **`CommandPalette`:** Integrated `CMD+K` interface for instant access to records, apps, and actions.
    -   **Robust Multi-Resource Search:** The `/search` API uses heuristic type detection and supports `__searchable_fields__` for fine-grained control.
    -   **Intelligent Labeling:** Automatically resolves display labels (username, number, title) for search results.
-   **Computed Properties (Aras Pro):** 
    -   **`@Aras.computed_field` Decorator:** Allows defining dynamic, read-only fields on models that are automatically serialized in API responses.
    -   **Serialization Flexibility:** Computed fields are seamlessly integrated into `to_dict()` and UI metadata.
-   **Advanced Relationship Management (Aras Pro):**
    -   **Many-to-Many (M2M) Support:** Automated M2M handling via `__m2m__` attribute, supporting bridge table synchronization and association management.
    -   **MultiSelect UI:** Dedicated `MultiSelectCombobox` for managing M2M relationships in the UI.
-   **Advanced Import Mapping (Aras Pro):**
    -   **Field Mapping UI:** Users can now map CSV columns to specific resource fields during the import process.
    -   **Background Processing:** Imports are handled via Celery for zero-latency user experience.
-   **Permissions & RBAC:** Integrated Role-Based Access Control.
-   **Auto-Migration:** Automatic database schema updates based on models.

### UI & Presentation Layer (Aras Pro Upgrades)

-   **Dynamic Analytics & Dashboard (Aras Pro):**
    -   **Pluggable Dashboard Widgets:** Support for Stat, List, and Chart widgets.
    -   **Interactive Data Visualization:** Built-in SVG-based charting engine supporting Bar and Pie charts with zero external dependencies.
    -   **Real-time Aggregation:** Widgets automatically fetch and group data from resources.
-   **Pro Layout Engine:**
    -   **Sections & Tabs:** Models can define `__layout__` to group fields into logical sections in the UI.
    -   **Dynamic Rendering:** `DynamicForm` automatically renders these layouts, reducing scroll fatigue.
-   **Advanced Conditional UI Visibility (Aras Pro):**
    -   **Safe `LogicEvaluator`:** A secure, recursive-descent logic engine for evaluating field dependencies (e.g., `total_amount > 5000 && status != 'Draft'`).
    -   **No-Eval Security:** Avoids unsafe JS execution, ensuring system stability.
-   **Pluggable UI Registry:**
    -   **`SchemaRegistry`:** A global registry for field components. Developers can easily register custom widgets (e.g., Color Pickers, Maps) without modifying core components.
-   **Real-time Validation:** Automated mapping of backend Pydantic errors (422) to UI field-level feedback.

### System & Extensibility

-   **Custom Model Actions Framework:**
    -   **`@Aras.model_action` Decorator:** Declarative business logic methods exposed as API endpoints.
    -   **UI Integration:** Actions appear as "Quick Action" (Zap icon) buttons in form headers.
-   **Centralized Background Task Processor:** Celery-powered task queue via `TaskManager`.
-   **Workflow Engine:** State-machine engine for document lifecycles.
-   **Advanced Logging and Monitoring:** Structured JSON logging and global exception handling.

---

## Framework Security Hardening

### Configuration & Secrets

-   **Centralized Settings (`api/core/lib/settings.py`):** Single source of truth for all environment config. Reads from `.env` via `python-dotenv`. `settings.validate()` is called at startup before any framework imports.
-   **Fail-Loud in Production:** `RuntimeError` if `SECRET_KEY` or `ARAS_ADMIN_PASSWORD` is missing in production mode. In development mode, an ephemeral key is generated with a warning.
-   **No Hardcoded Secrets:** All JWT keys, DB URLs, admin passwords, and CORS origins are env-driven. The `.env` file is the only place to configure these.

### API Security

-   **CORS Fixed:** `allow_origins=["*"]` + `allow_credentials=True` violated the CORS spec and was rejected by browsers. Now uses `settings.CORS_ORIGINS` (defaults to `http://localhost:5173`).
-   **All Admin/Dev Endpoints Authenticated:** Every `/api/v1/admin/*` and `/api/v1/dev/*` endpoint requires `require_admin` dependency (403 for non-admins, 401 for unauthenticated).
-   **Sidebar Authenticated:** `GET /api/v1/sidebar` requires `get_current_user`.
-   **File Download Protected:** `GET /api/v1/files/download/{filename}` requires auth + path traversal protection via `os.path.basename()`.
-   **Full RBAC on Query Endpoints:** `POST /{resource}/query` and `GET /search` both enforce `RBAC.has_permission()` for non-admin users. Global search uses a single bulk `get_readable_resources()` call to avoid N+1 queries.
-   **`require_admin` Single Source of Truth:** Defined once in `api/core/auth/service.py`; imported everywhere.

### Pydantic v2 Compliance

-   All `class Config: from_attributes = True` replaced with `model_config = ConfigDict(from_attributes=True)`.
-   All `@validator` decorators replaced with `@field_validator` + `@classmethod`.
-   All `.dict()` calls replaced with `.model_dump()` across `router_factory.py`, `installer.py`, and `dashboard.py`.

### Test Infrastructure

-   **`api/conftest.py`:** Session-scoped fixtures: `client` (TestClient), `admin_token`, `admin_headers`. Uses SQLite in-memory DB for isolation.
-   **`tests/test_auth_security.py`:** Verifies all secured endpoints return 401 without auth and 200 with admin token. Covers admin, dev, sidebar, and query endpoints.

### Performance Fixes

-   **N+1 RBAC Eliminated:** `global_search` now calls `RBAC.get_readable_resources()` once (single JOIN query) before the resource loop.
-   **Search Field Caching:** `_get_search_fields()` caches results on `model_class._search_fields_cache` — column iteration happens only once per model per process lifetime.
-   **Settings Seed Bulk Query:** Startup settings seed uses a single `IN` query instead of 8 individual SELECTs.
-   **Dead DB Connection Fixed:** `get_framework_info` no longer opens an unused DB connection.

### Frontend Reliability

-   **`ui/src/lib/resourceUtils.ts`:** `cleanResourcePath()` utility replaces 12+ inline path-normalization occurrences across `DynamicForm`, `ListView`, and `MetadataService`.
-   **React Error Boundary (`ErrorBoundary.tsx`):** Wraps the entire app; prevents blank screen on component errors. "Try Again" button resets state.
-   **MetadataService Caching:** In-memory `Map` cache with `clearCache()` and `invalidate()` methods. Prevents redundant `/metadata/` requests on re-navigation.
-   **API Error Shape Normalization (`api.ts`):** Response interceptor unifies `{message}` (backend custom handler) and `{detail}` (FastAPI 422) into a single `.detail` field.
-   **ERP Bootstrap Decoupled:** `erp_orders` widget removed from framework seed. App name reads from `settings.APP_NAME` env var.
