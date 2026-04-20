<project_context>
# Aras: Flask Low-Code CRUD Builder
Auto-generates UI, DB, REST. Stack: Python 3.9+, Flask, MariaDB, Celery.
Run: `flask run` (port 8080)
</project_context>

<documentation_index>
- **Framework rules & app contract:** Read `docs/MAIN.md` (WAJIB, sumber kebenaran tunggal)
- **Status implementasi & TODO aktif:** Read `docs/progress.md`
</documentation_index>

<key_classes>
- `AppHelper` (`arasCore/lib/app_helper.py`) — declaration untuk code-based app di manifest.py
- `ResourceDef` / `MenuGroup` / `CustomRoute` / `SubHandler` (`arasCore/lib/app_helper.py`) — komponen AppHelper
- `AppManagerApp` / `AppManagerTable` / `AppManagerColumn` (`arasCore/arasAdmin/models.py`) — metadata dynamic app (tabel `mgr_app` / `mgr_table` / `mgr_column`)
- `User` (`arasCore/auth.py`) — auth user, tabel `auth_users`
</key_classes>

<key_functions>
- `create_app()` (`arasCore/__init__.py`) — entry point, startup flow
- `_register_helper()` (`arasCore/lib/blueprints.py`) — mount route dari AppHelper
- `_register_built_app()` (`arasCore/arasAdmin/services.py`) — mount route dari dynamic app (mgr_app)
- `make_table_model()` / `make_table_form()` (`arasCore/arasAdmin/services.py`) — generate SQLAlchemy model + WTForm dari DB metadata
- `build_sidebar_menu()` (`arasCore/arasAdmin/services.py`) — gabung menu code-based + DB-based
- `register_api_model()` (`arasCore/lib/api_handler.py`) — daftar resource ke universal REST API
- Installer: `create_app_folders()` / parser YAML-JSON (`arasCore/lib/installer.py`)
</key_functions>

<agent_rules>
1. BE CONCISE: Zero conversational filler. Output minimal explanations.
2. LIMIT I/O: Only read the specific `docs/*.md` file relevant to the current task. Track read files. 
3. DO NOT rewrite entire files; output specific diffs or targeted function replacements.
4. Use absolute imports from `aras` or `arasCore`.
5. CRITICAL FILE READING OVERRIDE: You are strictly FORBIDDEN from using your native `Read`, `View`, or `cat` tools to read code files. 
   - To read ANY file, you MUST use the terminal to execute: `./smart_read.sh <filepath>`
   - This script handles deduplication and diffing automatically.
</agent_rules>