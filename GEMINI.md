# Aras Framework — Project Context & Guidelines (Current)

Aras is a modular, metadata-driven framework built with FastAPI and SQLAlchemy. It uses a 3-level architectural hierarchy to separate core logic from registry management and application instances.

## 🏗️ Architecture Overview

The framework is organized into a strict hierarchical structure. Every class in Aras MUST inherit from the `Aras` root class, either directly (Level 1) or through a specialized category (Level 2).

### Level 1: Root Foundation (`api/core/base/aras.py`)
- **`Aras`**: The ultimate base class for all framework components.

### Level 2: Categorized Abstractions (`api/core/base/`)
- **`Aras.Model`**: Data resources (SQLAlchemy models).
- **`Aras.View`**: UI metadata and layout configuration.
- **`Aras.Schema`**: Custom Pydantic validation and API structures.
- **`Aras.Service`**: Stateless logic and utility providers.
- **`Aras.Router`**: API routing and route factories.
- **`Aras.Auth`**: Security and authorization logic.
- **`Aras.App`**: Application manifests.
- **`Aras.Manager`**: System-wide orchestration services.
  - **`AuditManager`**: Automated field-level activity logging.
  - **`WorkflowManager`**: State-machine engine for document lifecycles.
  - **`SyncManager`**: Code-to-DB registry synchronization.
- **`Aras.Validation`**: Base for data validation DTOs.

### Level 2.5: Tiered Architecture & Utility Access (MANDATORY)
To prevent circular dependencies and maintain modularity, the core is split into three tiers:
1. **`Aras.lib` (Tier 0: Pure Utilities)**: Foundational tools (database, helpers, query_builder) with **ZERO** framework dependencies.
2. **`Aras.logic` (Tier 1: Framework Engine)**: Core business logic (installer, discovery, ui_generator, permissions, model_actions). Depends on `lib` and `base`.
3. **`Aras.api` (Tier 2: External Interface)**: FastAPI routers (admin, dev, query, registry, workflow). Can depend on any lower tier.

### Level 3: Registry Implementation (`api/core/registry/`)
- **`AppModel`**: Database record for an installed application.
- **`ResourceModel`**: Database record for a data table/model.
- **`FieldModel`**: Database record for field-level metadata and UI overrides.
- **`LinkModel`**: Database record for relationships (Lookups and Child Tables).
- **`TranslationModel`**: Database record for UI-level metadata translations.
- **`WidgetModel`**: Database record for dashboard widget definitions.
- **`DashboardLayoutModel`**: Database record for user-specific dashboard layouts and configurations.

---

## 📁 Project Structure

- **`api/`**: The backend framework and application logic.
  - **`core/`**: The engine of Aras.
  - **`apps/`**: Pluggable application modules (e.g., `dev`, `erp`).
  - **`manage.py`**: The primary CLI for framework management.
- **`ui/`**: The frontend React (TypeScript) dashboard.
- **`docs/`**: Technical documentation and progress logs (see `docs/feature.md` for detailed feature list).
- **`aras-old/`**: **LEGACY** version of the framework (Flask-based). Do not use for new features.

---

## 🚀 App Lifecycle Management

### 1. Installation (`install`)
- Supports **YAML**, **JSON**, and **ZIP** bundles.
- Scaffolds a new directory in `api/apps/`.
- **MANDATE**: Table names MUST be prefixed with the app name (e.g., `inventory_products`).

### 2. Synchronization (`sync`)
- Scans `api/apps/` for registered `Aras.App` classes.
- Upserts metadata into the Registry DB.
- **Auto-Migration**: Automatically handles physical schema changes (safe for SQLite).

### 3. Feature: Zero-Code Customization (Hybrid Metadata)
Aras provides a **Hybrid Metadata** system via `UIGenerator`.
1. **Auto-Detection**: Scans SQLAlchemy models for types, labels, and relations.
2. **DB Overrides**: Users can override labels, hide fields, or change UI types via the `ResourceModel` and `FieldModel` registries at runtime.

### 4. Feature: Workflow Engine
Models using the `workflow` feature benefit from a state-machine engine:
- **States & Transitions**: Defined in code, manageable via API.
- **Permission Gating**: Integrated with RBAC.
- **Dynamic UI**: Action buttons automatically appear in forms based on status.

---

## 🚀 New Core Features & Enhancements (May 2026)

To make Aras more robust, complete, and low-code, the following enhancements have been integrated:

-   **Enhanced Internationalization (i18n):**
    -   Dedicated `TranslationService` for managing and retrieving translations for metadata (app names, resource titles, field labels).
    -   API endpoints support a `lang` parameter for dynamically translated UI metadata.
-   **Centralized Background Task Processor:**
    -   Integration with Celery for asynchronous processing of long-running tasks.
    -   `TaskManager` provides a unified API for enqueuing and monitoring tasks (e.g., asynchronous CSV imports).
-   **Dynamic Dashboard Builder:**
    -   `DashboardLayoutModel` allows user-specific, customizable dashboard layouts.
    -   CRUD APIs for managing user dashboards, including setting a default layout.
-   **Advanced Logging and Monitoring:**
    -   Structured logging using `pythonjsonlogger` for improved observability.
    -   Enhanced global exception handling ensures consistent error responses and detailed logging.
-   **Custom Model Actions Framework:**
    -   `@action` decorator for declarative definition of custom business logic methods on models.
    -   Automatic API exposure for these actions (`POST /resource/{item_id}/action/{action_name}`) with integrated permission checks and input validation.

---

## 🛠️ CLI Reference (`api/manage.py`)

Run from the `api/` directory.

| Command | Argument | Description |
| :--- | :--- | :--- |
| `sync` | - | Sync code manifests to DB registry and migrate schema. |
| `install` | `<file>` | Install app from .yaml, .json, or .zip. |
| `uninstall`| `<name>` | Purge app files and registry records. |
| `activate` | `<name>` | Mark app as active. |
| `deactivate`| `<name>` | Mark app as inactive. |
| `discover` | - | List all apps currently registered in code. |
| `check` | - | Run framework health and integrity checks. |

---

## ⚠️ Development Mandates

1. **Table Naming**: Always use `{app_name}_{table_name}` for `__tablename__`.
2. **Registry Sync**: After changing `app.py` or `models.py`, you MUST run `python manage.py sync`.
3. **Integrity Checks**: Regularly run `python manage.py check`.
4. **Environment**: Ensure `sys.path` includes the `api/` directory.
5. **NoForeground**: Never run long-running commands (servers) in the foreground in this environment.
