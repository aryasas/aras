# antigravity
"""Add level column and unique constraint to core_settings.

Relocates security keys from core namespace to admin namespace, setting level='admin'.
Sets core and core_config namespaces to level='framework'.
Sets other namespaces to level='app'.

Run: python -m core.migrations.add_settings_level
"""
import sys
sys.path.insert(0, ".")
from core.lib.database import SessionLocal
from sqlalchemy import text

# Keys of the security section to be relocated from 'core' -> 'admin'
SECURITY_KEYS = (
    'session_timeout_minutes',
    'access_token_expire_minutes',
    'password_reset_expire_minutes',
    'enforce_2fa',
    'password_min_length',
    'password_require_uppercase',
    'password_require_number',
    'password_require_symbol',
    'max_login_attempts',
    'lockout_minutes',
    'allow_signup',
    'rbac_enabled',
    'cors_origins'
)

# Guarded DDL for Postgres
SQL_ADD_COLUMN = """
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'core_settings' AND column_name = 'level'
  ) THEN
    ALTER TABLE core_settings ADD COLUMN level VARCHAR(20) DEFAULT 'app' NOT NULL;
  END IF;
END $$;
"""

SQL_CONSTRAINTS = """
DO $$
BEGIN
  -- Drop the old unique constraint if it exists
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'uq_core_settings_namespace_key' AND table_name = 'core_settings'
  ) THEN
    ALTER TABLE core_settings DROP CONSTRAINT uq_core_settings_namespace_key;
  END IF;

  -- Create the new unique constraint if it doesn't exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE constraint_name = 'uq_core_settings_namespace_key_level' AND table_name = 'core_settings'
  ) THEN
    ALTER TABLE core_settings ADD CONSTRAINT uq_core_settings_namespace_key_level UNIQUE (namespace, key, level);
  END IF;
END $$;
"""

SQL_BACKFILL_SECURITY = """
UPDATE core_settings
SET namespace = 'admin', level = 'admin'
WHERE namespace = 'core' AND key = ANY(:keys);
"""

SQL_BACKFILL_FRAMEWORK = """
UPDATE core_settings
SET level = 'framework'
WHERE namespace IN ('core', 'core_config');
"""


# antigravity
def run():
    db = SessionLocal()
    try:
        # 1. Add level column
        db.execute(text(SQL_ADD_COLUMN))
        db.flush()

        # 2. Backfill security keys
        db.execute(text(SQL_BACKFILL_SECURITY), {"keys": list(SECURITY_KEYS)})

        # 3. Backfill framework level settings
        db.execute(text(SQL_BACKFILL_FRAMEWORK))
        db.flush()

        # 4. Update constraints
        db.execute(text(SQL_CONSTRAINTS))
        
        db.commit()
        print("Migration complete: level column added, backfilled and constraints updated.")
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run()
