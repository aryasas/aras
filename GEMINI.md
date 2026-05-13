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
- **`Aras.Validation`**: Base for data validation DTOs.

### Level 2.5: Tiered Architecture & Utility Access (MANDATORY)
To prevent circular dependencies and maintain modularity, the core is split into three tiers:
1. **`Aras.lib` (Tier 0: Pure Utilities)**: Foundational tools (database, helpers, query_builder) with **ZERO** framework dependencies.
2. **`Aras.logic` (Tier 1: Framework Engine)**: Core business logic (installer, discovery, ui_generator). Depends on `lib` and `base`.
3. **`Aras.api` (Tier 2: External Interface)**: FastAPI routers (admin, dev, query). Can depend on any lower tier.

### Level 3: Registry Implementation (`api/core/registry/`)
- **`AppModel`**: Database record for an installed application.
- **`ResourceModel`**: Database record for a data table/model.
- **`FieldModel`**: Database record for field-level metadata and UI overrides.
- **`LinkModel`**: Database record for relationships (Lookups and Child Tables).

---

## 📁 Project Structure

- **`api/`**: The backend framework and application logic.
  - **`core/`**: The engine of Aras.
  - **`apps/`**: Pluggable application modules (e.g., `admin`, `erp`, `inventory`).
  - **`manage.py`**: The primary CLI for framework management.
- **`ui/`**: The frontend React (TypeScript) dashboard.
- **`docs/`**: Technical documentation and progress logs.
- **`aras-old/`**: **LEGACY** version of the framework (Flask-based). Do not use for new features, use olnly for reference.

---

## 🚀 App Lifecycle Management

### 1. Installation (`install`)
- Supports **YAML**, **JSON**, and **ZIP** bundles.
- Scaffolds a new directory in `api/apps/`.
- **MANDATE**: Table names MUST be prefixed with the app name (e.g., `inventory_products`) to avoid SQLAlchemy MetaData collisions.

### 2. Synchronization (`sync`)
- Scans `api/apps/` for registered `Aras.App` classes.
- Upserts metadata into the Registry DB.
- **Deactivation**: If an app exists in the DB but is missing from the filesystem, it is marked as `is_active=False`.

### 3. Activation & Deactivation (`activate` / `deactivate`)
- Toggles the `is_active` flag in the `aras_apps` registry.
- **Behavior**: Deactivated apps are hidden from the UI but their data and files remain intact.

### 4. Uninstallation (`uninstall`)
- **Clean Purge**: Removes the app directory, drops all associated physical SQL tables, and deletes all registry records (Apps, Resources, Fields, Links).

---

## 🛠️ CLI Reference (`api/manage.py`)

Run from the `api/` directory or use `python api/manage.py` from root.

| Command | Argument | Description |
| :--- | :--- | :--- |
| `sync` | - | Sync code manifests to DB registry. |
| `install` | `<file>` | Install app from .yaml, .json, or .zip. |
| `uninstall`| `<name>` | **Destructive**: Remove files and purge DB/Tables. |
| `activate` | `<name>` | Mark app as active in registry. |
| `deactivate`| `<name>` | Mark app as inactive in registry. |
| `discover` | - | List all apps currently registered in code. |
| `check` | - | Run framework health and integrity checks. |

---

## ⚠️ Development Mandates

1. **Table Naming**: Always use `{app_name}_{table_name}` for `__tablename__`.
2. **Registry Sync**: After changing `app.py` or `models.py`, you MUST run `python manage.py sync`. This now automatically handles physical schema migrations.
3. **Dependencies**: Use `Aras.App.models` to list all models belonging to an app for registration.
4. **Environment**: Ensure `sys.path` includes the `api/` directory when running scripts from the root.
5. **Metadata Syncing**: The `sync` process automatically handles `ui_type` defaults to `'string'` if not explicitly defined or if set to `None`, ensuring compatibility with the registry's non-null constraints.
6. **Integrity Checks**: Regularly run `python manage.py check` to ensure consistency between the registry, codebase, and physical database.


## ⚠️ Mandates

1. If you use and create tools. and it can be generic, create it in tools/ and dont delete it for future reuse.
2. Always add to docs/feature.md for new feature added
