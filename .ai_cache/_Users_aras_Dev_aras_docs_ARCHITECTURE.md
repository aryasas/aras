# Aras Architecture & Lifecycle

## 1. Core Framework (`arasCore`)

TODO: saat ini banyak file framework yang masih didalam aras/lib. Ini harus dirubah ke ArasCore/lib

- `app_factory.py`: `create_app()` initializes Flask, registers extensions, blueprints, error handlers, then loads all active built apps.
- `blueprints.py`: Auto-discovers and registers `app_*` modules. `app_admin` must register last.
- `manager.py`: Contains `BaseView`, `CrudView`, `ViewManager`. `CrudView` auto-generates list/create/edit/delete routes (route include API).
- `extensions.py`: Initializes SQLAlchemy, LoginManager, CSRF, Marshmallow, Mail, Cache, Migrate.

## 2. Built-in Apps (`arasCore/arasAdmin/`)

TODO: endpoint (termasuk api) dihandle oleh arasCore dan app hanya memberitahu nama-nama endpointnya

- Follows the pattern: `models.py` → `forms.py` → `routes.py`/`views.py`  TODO: ini harus benar-benar matang diawal agar kedepan mudah untuk dikembangkan dan perlu coding minim jika ada penyesuaian. jika memang 1 app.
- `app_admin/registry.py`: `ModuleRegistry` wires up a `CrudView` into the admin sidebar.
- Modules: `app_auth`, `app_admin`, `app_notes`, `app_basic`.

## 3. Dynamic App Manager (`aras/app_manager/`)

TODO: ini masih harus banyak modifikasi. Termasuk support untuk install module dari file upload dengan format yang bagus, mudah ditulis (pilihkan antara json, yaml, py atau lainnya) → file ini nanti mencakup semua yang dibutuhkan arasCore, diantaranya: nama app, nama url, menu, template (jika ada), database schema (database nanti dibuat oleh arasCore via app builder - kecuali jika ada custom besar dan memang lebih efisien dibuat file model, untuk erp mana yang lebih baik?). Nanti bisa 2 arah, yang sudah dibuat via app builder → dibuat filenya, yang dari file → dibuat oleh app builder. Maka dari itu app_manager sangat penting untuk ekosistem aras ini. Di app builder harus ditambah kolom template, jika ada template, maka bisa menggunakan template terpisah dari admin untuk url non /admin. Dan sebaiknya dirubah namanya menjadi app manager, dan dijadikan bagian langsung dari aras core (bukan blueprint) atau jika lebih baik blueprint, maka jangan ditampilkan di halaman app_manager (tidak bisa di stop/run)

- `models.py`: Defines `AppBuilderApp` (app definition) and `AppBuilderField` (column definitions).
- `factory.py`: Core engine. Uses `make_dynamic_model()` and `make_dynamic_form()` via Python's `type()` to generate SQLAlchemy models and WTForms classes at runtime.
- `loader.py`: `load_all_built_apps()` queries active apps and calls `register_built_app()`.

## 4. Person App

TODO: ini kita buat dulu minimal sebagai bagian dari social. untuk bisa merencanakan koneksi dengan yang lainnya. Jika full, ada contoh app lama (yang belum compatible dengan aras framework saat ini di aras/ app_basic. pertimbangkan untuk menggabungkan parameter data person ke app_social. ini agar integritas data terjaga (1 orang tidak memiliki 2 data) hanya koneksi atau link). persiapkan dulu aras frameworknya dengan baik

## Built App Lifecycle

1. User defines app/fields in UI → saved to `app_builder_app` / `app_builder_field`.
2. Activation → `register_built_app()` triggers dynamic model/form creation, builds DB table, registers Blueprint.
3. Live endpoints created at `/admin/<endpoint>/` (UI) and `/api/<endpoint>/` (REST).
