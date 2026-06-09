# claude-opus-4-8
"""Collapse the duplicate organization/instance config into a single source of truth.

Historically organization config was scattered across THREE stores:

  A. core_organizations (multi-row model) ............ per-org/branch identity  [KEPT]
  B. core_config_values via `core_config.*` sections .. global single-value     [REMOVED]
  C. core_settings via `core` sections ................ global single-value      [CANONICAL]

B duplicated both A (company identity) and C (smtp/branding/localization). This migration
deletes B, folding its instance-wide values into C (the `core` namespace settings hub) and
dropping the per-org identity rows (now owned solely by A).

Field-level mapping  core_config_values(scope_key, field_key)  ->  core settings(namespace.section.key):

  core_config.smtp.host            -> core / email / smtp_host
  core_config.smtp.port            -> core / email / smtp_port
  core_config.smtp.username        -> core / email / smtp_user
  core_config.smtp.password        -> core / email / smtp_password
  core_config.smtp.use_tls         -> core / email / smtp_use_tls
  core_config.smtp.from_address    -> core / email / from_address
  core_config.smtp.from_name       -> core / email / from_name
  core_config.branding.primary_color -> core / branding / primary_color
  core_config.branding.accent_color  -> core / branding / accent_color
  core_config.branding.login_logo    -> core / branding / logo_url
  core_config.branding.favicon       -> core / branding / favicon_url
  core_config.localization.date_format   -> core / general / default_date_format
  core_config.localization.time_format   -> core / general / default_time_format
  core_config.localization.number_format -> core / general / default_number_format
  core_config.localization.first_day_of_week -> core / general / first_day_of_week
  core_config.tax.*                -> dropped (tax is per-org, configured on Charge/Org)
  core_config.company.*            -> dropped (identity owned by core_organizations)

`core_config.numbering.*` and `core_config.menu.*` stay put (internal, string-literal keys).

Target-wins: if the `core` setting already holds a value, the old value is discarded.
Idempotent: re-running is a no-op once the `core_config.*` rows are gone.

Run: python -m core.migrations.move_platform_config
"""
from sqlalchemy import text
from core.lib.database import engine, SessionLocal
from core.registry.settings_service import SettingsService

# (old_scope_key, old_field_key) -> (target_section_key, target_field_key)
_MAP = {
    ("core_config.smtp", "host"): ("email", "smtp_host"),
    ("core_config.smtp", "port"): ("email", "smtp_port"),
    ("core_config.smtp", "username"): ("email", "smtp_user"),
    ("core_config.smtp", "password"): ("email", "smtp_password"),
    ("core_config.smtp", "use_tls"): ("email", "smtp_use_tls"),
    ("core_config.smtp", "from_address"): ("email", "from_address"),
    ("core_config.smtp", "from_name"): ("email", "from_name"),
    ("core_config.branding", "primary_color"): ("branding", "primary_color"),
    ("core_config.branding", "accent_color"): ("branding", "accent_color"),
    ("core_config.branding", "login_logo"): ("branding", "logo_url"),
    ("core_config.branding", "favicon"): ("branding", "favicon_url"),
    ("core_config.localization", "date_format"): ("general", "default_date_format"),
    ("core_config.localization", "time_format"): ("general", "default_time_format"),
    ("core_config.localization", "number_format"): ("general", "default_number_format"),
    ("core_config.localization", "first_day_of_week"): ("general", "first_day_of_week"),
}

# scope_keys whose rows are deleted without relocation (per-org or identity data).
_DROP = ("core_config.company", "core_config.tax", "core_config.localization",
         "core_config.smtp", "core_config.branding")


# claude-opus-4-8
def run():
    moved = dropped = 0
    db = SessionLocal()
    try:
        for (old_scope, old_field), (_section, target_key) in _MAP.items():
            row = db.execute(text(
                "SELECT value_json FROM core_config_values "
                "WHERE scope_key = :s AND field_key = :f AND deleted_at IS NULL"
            ), {"s": old_scope, "f": old_field}).fetchone()
            if row is None:
                continue
            existing = SettingsService.get(db, "core", target_key, default=None)
            if existing in (None, ""):
                # value column is JSON/text; SettingsService re-serializes on set.
                SettingsService.set(db, "core", target_key, row[0])
                moved += 1
        db.commit()
    finally:
        db.close()

    with engine.begin() as conn:
        for scope in _DROP:
            res = conn.execute(text(
                "DELETE FROM core_config_values WHERE scope_key = :s"
            ), {"s": scope})
            dropped += res.rowcount or 0
            conn.execute(text(
                "DELETE FROM core_config_value_audit WHERE scope_key = :s"
            ), {"s": scope})

    print(f"Config consolidation complete: folded {moved} value(s) into the `core` namespace, "
          f"dropped {dropped} legacy core_config.* row(s).")


if __name__ == "__main__":
    run()
