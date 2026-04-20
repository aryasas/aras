# Aras Architecture & Lifecycle

## 1. Core Framework (`aras/lib/`)
- `app_factory.py`: `create_app()` initializes Flask, registers extensions, blueprints, error handlers, then loads all active built apps.
- `blueprints.py`: Auto-discovers and registers `app_*` modules. `app_admin` must register last.
- `manager.py`: Contains `BaseView`, `CrudView`, `ViewManager`. `CrudView` auto-generates list/create/edit/delete routes.
- `extensions.py`: Initializes SQLAlchemy, LoginManager, CSRF, Marshmallow, Mail, Cache, Migrate.

## 2. Built-in Apps (`aras/app_*/` & `arasCore/arasAdmin/`)
- Follows the pattern: `models.py` → `forms.py` → `routes.py`/`views.py`
- `app_admin/registry.py`: `ModuleRegistry` wires up a `CrudView` into the admin sidebar.
- Modules: `app_auth`, `app_admin`, `app_notes`, `app_basic`.

## 3. Dynamic App Manager (`aras/app_manager/`)
- `models.py`: Defines `AppBuilderApp` (app definition) and `AppBuilderField` (column definitions).
- `factory.py`: Core engine. Uses `make_dynamic_model()` and `make_dynamic_form()` via Python's `type()` to generate SQLAlchemy models and WTForms classes at runtime.
- `loader.py`: `load_all_built_apps()` queries active apps and calls `register_built_app()`.

## Built App Lifecycle
1. User defines app/fields in UI → saved to `app_builder_app` / `app_builder_field`.
2. Activation → `register_built_app()` triggers dynamic model/form creation, builds DB table, registers Blueprint.
3. Live endpoints created at `/admin/<endpoint>/` (UI) and `/api/<endpoint>/` (REST).
