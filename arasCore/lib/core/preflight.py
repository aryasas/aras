# -*- coding: utf-8 -*-
"""
arasCore/lib/core/preflight.py
==============================
Pre-flight schema validation for development mode.
"""
import os
import click
import logging
from sqlalchemy import inspect as sa_inspect
from arasCore.lib.core.extensions import db

logger = logging.getLogger(__name__)

def run_preflight_check(app):
    """
    Checks for:
    1. Pending dynamic migrations (from schema_migrator)
    2. Drifts in code-based models (from fix-db logic)
    
    Only prints warnings to stdout if inconsistencies are found.
    """
    if not app.config.get("DEBUG") and os.getenv("FLASK_ENV") != "development":
        return

    with app.app_context():
        # 1. Check Dynamic App Migrations
        try:
            from arasCore.admin.models import AppManagerApp
            from arasCore.lib.services.schema_migrator import diff_app, get_pending
            
            active_apps = AppManagerApp.query.filter_by(is_active=True).all()
            total_pending = 0
            for app_obj in active_apps:
                # Refresh diff
                diff_app(app_obj.id)
                pending = get_pending(app_obj.id)
                total_pending += len(pending)
            
            if total_pending > 0:
                print(f"\n\033[93m[PREFLIGHT] WARNING: {total_pending} unapplied dynamic migrations detected.\033[0m")
                print("\033[93m             Run 'flask aras migrations' in the Admin UI or via CLI.\033[0m\n")
        except Exception as e:
            logger.debug(f"[preflight] dynamic check failed: {e}")

        # 2. Check Code-based Model Drifts
        try:
            inspector = sa_inspect(db.engine)
            existing_tables = set(inspector.get_table_names())
            
            drifts = []
            seen = {}
            for mapper in db.Model.registry.mappers:
                cls = mapper.class_
                tbl = getattr(cls, "__tablename__", None)
                if tbl and tbl not in seen:
                    seen[tbl] = cls
            
            for tbl_name, model in seen.items():
                if tbl_name not in existing_tables:
                    continue
                
                live_cols_raw = inspector.get_columns(tbl_name)
                live_cols = {c["name"]: c for c in live_cols_raw}
                sa_table = model.__table__
                for col in sa_table.columns:
                    if col.name not in live_cols:
                        drifts.append(f"{tbl_name}.{col.name} (missing)")
                    else:
                        # Simple type drift check
                        live_type = str(live_cols[col.name]["type"]).upper()
                        try:
                            target_type = col.type.compile(dialect=db.engine.dialect).upper()
                        except Exception:
                            target_type = str(col.type).upper()
                        
                        # Basic normalization
                        live_type = live_type.replace("TINYINT(1)", "BOOLEAN").replace("INTEGER", "INT")
                        target_type = target_type.replace("TINYINT(1)", "BOOLEAN").replace("INTEGER", "INT")
                        
                        if live_type != target_type and not (live_type.startswith(target_type) or target_type.startswith(live_type)):
                            drifts.append(f"{tbl_name}.{col.name} (type drift)")
            
            if drifts:
                print(f"\033[93m[PREFLIGHT] WARNING: {len(drifts)} code-model drifts detected.\033[0m")
                print(f"\033[93m             Sample: {', '.join(drifts[:3])}{'...' if len(drifts)>3 else ''}\033[0m")
                print("\033[93m             Run 'flask aras fix-db' to synchronize.\033[0m\n")
        except Exception as e:
            logger.debug(f"[preflight] code-drift check failed: {e}")
