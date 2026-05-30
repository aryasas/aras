import os
import json
import argparse
import logging
from sqlalchemy import create_engine, text

# gemini-2-5-flash

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def _get_admin_connection():
    """Return a SQLAlchemy engine connected to the postgres admin DB."""
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    pw = f":{password}" if password else ""
    url = f"postgresql+psycopg2://{user}{pw}@{host}:{port}/postgres"
    return create_engine(url, isolation_level="AUTOCOMMIT")

def rename_dbs(dry_run=False):
    admin_engine = _get_admin_connection()
    renamed_count = 0
    
    try:
        with admin_engine.connect() as conn:
            result = conn.execute(text("SELECT datname FROM pg_database WHERE datname LIKE 'aras_tenant_%'"))
            dbs = [r[0] for r in result.fetchall()]
            
            if not dbs:
                logger.info("No databases matching 'aras_tenant_%%' found.")
                return 0
                
            for old_name in dbs:
                new_name = old_name.replace("aras_tenant_", "tenant_", 1)
                logger.info(f"Plan: {old_name} -> {new_name}")
                
                if not dry_run:
                    # Terminate active connections
                    conn.execute(text("""
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE datname = :db AND pid <> pg_backend_pid()
                    """), {"db": old_name})
                    
                    # Rename database
                    conn.execute(text(f'ALTER DATABASE "{old_name}" RENAME TO "{new_name}"'))
                    logger.info(f"Renamed: {old_name} -> {new_name}")
                    renamed_count += 1
    except Exception as e:
        logger.error(f"Error during DB rename: {e}")
        if not dry_run:
            raise
    finally:
        admin_engine.dispose()
    
    return renamed_count

def update_registry(dry_run=False):
    # This project uses a JSON registry for tenants
    registry_path = os.getenv("TENANT_REGISTRY_PATH") or os.path.join("api", "data", "tenant_registry.json")
    if not os.path.exists(registry_path):
        # try root data dir
        registry_path = os.path.join("data", "tenant_registry.json")
        if not os.path.exists(registry_path):
            logger.warning(f"Registry not found at {registry_path}")
            return 0
            
    try:
        with open(registry_path, "r") as f:
            registry = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load registry: {e}")
        return 0
        
    updated_count = 0
    for tenant_id, info in registry.items():
        old_url = info.get("db_url", "")
        if "aras_tenant_" in old_url:
            new_url = old_url.replace("aras_tenant_", "tenant_")
            info["db_url"] = new_url
            
            if "meta" in info and info["meta"].get("db_name"):
                info["meta"]["db_name"] = info["meta"]["db_name"].replace("aras_tenant_", "tenant_")
                
            logger.info(f"Registry Update Plan: {tenant_id} URL -> {new_url}")
            updated_count += 1
            
    if not dry_run and updated_count > 0:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=4)
        logger.info(f"Saved registry updates to {registry_path}")
        
    return updated_count

def main():
    parser = argparse.ArgumentParser(description="Rename tenant databases from aras_tenant_* to tenant_*")
    parser.add_argument("--dry-run", action="store_true", help="List actions without executing")
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be applied.")
        
    renamed = rename_dbs(args.dry_run)
    updated = update_registry(args.dry_run)
    
    logger.info(f"Summary: Renamed {renamed} DBs, updated {updated} registry entries.")

if __name__ == "__main__":
    main()
