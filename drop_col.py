from api.core.lib.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        # Try to drop the foreign key '1'
        conn.execute(text("ALTER TABLE erp_config_companies DROP FOREIGN KEY `1`"))
        print("Dropped foreign key '1'")
    except Exception as e:
        print(f"Failed to drop foreign key '1': {e}")
    
    try:
        # Try to drop the index if it still exists
        conn.execute(text("ALTER TABLE erp_config_companies DROP INDEX ix_erp_config_companies_company_id"))
        print("Dropped index")
    except Exception as e:
        print(f"Failed to drop index: {e}")

    try:
        # Try to drop the column
        conn.execute(text("ALTER TABLE erp_config_companies DROP COLUMN company_id"))
        print("Dropped column company_id")
    except Exception as e:
        print(f"Failed to drop column: {e}")
    
    conn.commit()
