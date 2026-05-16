❯ check what is fragile and unstabble and have to make it stable                                                   

⏺ I'll scan the codebase for fragile and unstable patterns.

⏺ reviewer(Codebase fragility audit)
  ⎿  Done (136 tool uses · 89.0k tokens · 5m 36s)
  (ctrl+o to expand)

⏺ Here's the prioritized fragility report:
         
  ---
  Fragility Audit — Prioritized Findings

  BLOCKERS (fix first)

  1. SQL Injection via raw text(f"...") — 3 locations
  - arasCore/admin/routes/apps.py:794,799,808,813 — system_table + display_col from request.args injected directly
  into SQL. Admin-authenticated but still injectable.
  - arasCore/admin/home_service.py:103,117,142 — widget config from DB injected into SQL.
  - arasCore/lib/ui/widget_registry.py:50,71,92,96 — same pattern, backtick-only "quoting" doesn't prevent
  injection.
  
  2. int(os.getenv("DB_PORT")) crashes when DB_PORT unset
  - arasCore/lib/cli/cli_db.py:16 — int(None) raises TypeError. Change to int(os.getenv("DB_PORT", 3306)).
  
  3. import mariadb at top-level in cli_db.py
  - If the mariadb package is not installed, importing cli_db fails, breaking the entire CLI chain. Should be a
  lazy import inside the command function.
  
  4. Flask private URL map mutation — not thread-safe
  - arasCore/admin/services.py:149-157 — Direct writes to flask_app.url_map._rules and _rules_by_endpoint (private
  Flask internals). Breaks on Flask version bumps and is not thread-safe under hot-reload.

  ---
  HIGH (structurally fragile)

  5. arasCore hardcodes app.erp internals
  - arasCore/admin/crud_factory.py:864 — from app.erp.erp_main.models.report import ErpReport inside framework
  code. If erp is uninstalled, this silently returns None.
  - arasCore/lib/cli/cli.py:24 — from app.erp.cli import ... in CLI registration. Framework/app boundary violated.

  6. _DEFERRED_VIEWS list race — silent drops on concurrent autodiscover
  - arasCore/arasgen.py:1241-1350 — Module-level list mutated by metaclass during import, then replaced by
  autodiscover(). Two concurrent autodiscovers drop items silently.
  
  7. Boot-time auto_migrate failures swallowed silently
  - arasCore/__init__.py:97,117 — Both migration passes caught with bare except Exception. Early-pass failure logs
  at debug level only; app boots with potentially missing columns.
  
  8. DB write inside resolve_label read path
  - arasCore/arasgen.py:268-283 — _seed_mgr_column commits to DB during serialization. If session is in a
  dirty/failed state, this silently rolls back and returns wrong label with no error surfaced.

  9. Bare except: swallowing KeyboardInterrupt/SystemExit
  - arasCore/admin/routes/settings_modules/core.py:120,194
  - arasCore/lib/core/context.py:16

  ---
  MEDIUM

  10. Duplicate event handler registration on re-import
  - app/erp/__init__.py:37-38 — on("framework.remigrate", handler) at module level. Test reloads or double imports
  register the handler multiple times; seed runs N times.
  
  11. Dev SQL console bypassable regex
  - arasCore/admin/routes/dev.py:171-174 — SELECT-only check not anchored; /* INSERT */ or UNION can bypass when
  DEBUG=True.

  12. None-exporting stub imports
  - arasCore/lib/arasgen/ stubs re-export from arascore.arasgen. If arasgen.py fails, stubs silently export None
  with no error.

  13. TODO filter silently ignored in list views
  - arasCore/admin/crud_factory.py:830 — Saved view filters are never applied. Silent wrong behavior.

  14. Subprocess hangs on corrupt backup restore
  - arasCore/lib/services/backup.py:156 — No timeout on proc.communicate(); corrupt gzip leaves subprocess hanging
  indefinitely.

  ---
  Quickest wins: Fix #2 (DB_PORT default) and #3 (lazy mariadb import) — both are one-liners. #1 (SQL injection)
  needs an allowlist for system_table. #9 (bare except:) just needs except Exception.

  Want me to fix any of these?
