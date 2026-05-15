import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'api'))
from core.lib.database import engine
from sqlalchemy import text

def fix_table(table_name, json_columns):
    with engine.connect() as conn:
        print(f"Fixing {table_name}...")
        for col in json_columns:
            default_val = '[]'
            if col == 'layout' or col == 'config':
                default_val = '{}'
                
            update_query = text(f"UPDATE {table_name} SET {col} = :default_val WHERE {col} = '' OR {col} IS NULL")
            res = conn.execute(update_query, {"default_val": default_val})
            conn.commit()
            print(f"  Updated {res.rowcount} rows in {col}")

if __name__ == "__main__":
    fix_table("aras_apps", ["menu_groups", "config"])
    fix_table("aras_resources", ["features", "scoped_by", "layout"])
    fix_table("aras_links", ["config"])
