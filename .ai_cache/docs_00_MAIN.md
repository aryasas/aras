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

- `models.py`: Defines `AppBuilderApp` (`mgr_app`), `AppBuilderTable` (`mgr_table`), `AppBuilderColumn` (`mgr_column`). Table prefix `mgr_` untuk semua metadata app manager.
- `factory.py`/`services.py`: Core engine. Uses `make_table_model()` and `make_table_form()` via Python's `type()` to generate SQLAlchemy models and WTForms classes at runtime. Tabel dinamis yang dibuat user menggunakan prefix `ab_{app}_{table}`.
- `loader.py`: `load_all_built_apps()` queries active apps and calls `_register_built_app()`.

## Konvensi Tablename

| Prefix | Digunakan untuk |
|--------|----------------|
| `auth_` | Auth: users, roles, permissions |
| `mgr_` | App Manager metadata: `mgr_app`, `mgr_table`, `mgr_column`, `mgr_field`, `mgr_menu` |
| `adm_` | Admin built-in: messages, notifications, activity, posts |
| `core_` | Core app: company, setting, currency, tax, dll |
| `ab_` | Tabel dinamis buatan user via App Manager (`ab_{app}_{table}`) |
| `{app}_` | Built-in apps: `notes_`, `basic_`, `acc_`, `soc_`, dll |

## 4. Person App

TODO: ini kita buat dulu minimal sebagai bagian dari social. untuk bisa merencanakan koneksi dengan yang lainnya. Jika full, ada contoh app lama (yang belum compatible dengan aras framework saat ini di aras/ app_basic. pertimbangkan untuk menggabungkan parameter data person ke app_social. ini agar integritas data terjaga (1 orang tidak memiliki 2 data) hanya koneksi atau link). persiapkan dulu aras frameworknya dengan baik

## Built App Lifecycle

1. User defines app/fields in UI → saved to `mgr_app` / `mgr_table` / `mgr_column`.
2. Activation → `_register_built_app()` triggers dynamic model/form creation, builds DB table (`ab_{app}_{table}`), registers Blueprint.
3. Live endpoints created at `/admin/{url}/` (UI), `/{url}/` (web public), dan `/api/{url}/` (REST).


# Project Instructions

- Tidak perlu menjelaskan dan menjawab pada setiap tugas yang sedang dijalankan. Cukup laporan di akhir dengan singkat.
- Anda harus mengikuti alur yang framework yang benar (LIHAT docs/00_MAIN.md)
- Sebelum limit, berhenti dan lakukan update ke docs/progress.md

# Rules for AI / LLM
- BE CONCISE: Zero conversational filler. Output minimal explanations.
- LIMIT I/O: Only read the specific docs/*.md file relevant to the current task. Track read files.

# KEY CONCEPT (FOR  AI HOW TO WORK)
# MUST AND MUST BE FOLLOW
- DO NOT rewrite entire files — output specific diffs or targeted function replacements.
- Use absolute imports from aras or arasCore.
- CRITICAL FILE READING OVERRIDE: You are strictly FORBIDDEN from using your native Read, View, or cat tools to read code files.
- To read ANY file, you MUST use the terminal to execute: python3 smart_read.py <filepath>
- If you need to view token efficiency, execute: python3 smart_read.py stats
- To read ANY file, you MUST use the terminal to execute: ./smart_read.sh <filepath>
- This script handles deduplication and diffing automatically.
- DONT WASTE TOKEN/USAGE.
