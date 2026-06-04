"""Rename legacy framework/config tables to the new core_* / accounting_* names."""
import sys

sys.path.insert(0, ".")

from sqlalchemy import text

from core.lib.database import SessionLocal

RENAMES = {
    "base_saved_filters": "core_saved_filters",
    "config_organizations": "core_organizations",
    "config_currencies": "core_currencies",
    "config_print_templates": "core_print_templates",
    "config_notifications": "core_notifications",
    "config_workflow_templates": "core_workflow_templates",
    "config_workflow_states": "core_workflow_states",
    "config_workflow_transitions": "core_workflow_transitions",
    "config_workflow_actions": "core_workflow_actions",
    "config_user_access": "core_user_access",
    "config_org_vocabulary": "accounting_org_vocabulary",
    "config_org_posting_rules": "accounting_org_posting_rules",
}


def _rename_sql(old_name: str, new_name: str) -> str:
    return f"""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{old_name}')
  THEN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{new_name}') THEN
      EXECUTE 'DROP TABLE ' || quote_ident('{new_name}') || ' CASCADE';
      RAISE NOTICE 'Dropped transient {new_name} before rename';
    END IF;
    ALTER TABLE {old_name} RENAME TO {new_name};
    RAISE NOTICE 'Renamed {old_name} to {new_name}';
  ELSE
    RAISE NOTICE 'No rename needed for {old_name}';
  END IF;
END $$;
"""


def run():
    db = SessionLocal()
    try:
        for old_name, new_name in RENAMES.items():
            db.execute(text(_rename_sql(old_name, new_name)))
        db.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run()
