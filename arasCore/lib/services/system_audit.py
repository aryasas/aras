# -*- coding: utf-8 -*-
import os
import time
from sqlalchemy import inspect as sa_inspect, text
from flask import current_app
from arasCore.lib.core.extensions import db
import importlib

class SystemAudit:
    @staticmethod
    def run_all():
        report = {
            "timestamp": time.time(),
            "sections": [],
            "summary": {"status": "ok", "warning_count": 0, "critical_count": 0}
        }
        
        try:
            report["sections"].append(SystemAudit.check_database() or {"title": "Database", "items": []})
            report["sections"].append(SystemAudit.check_apps() or {"title": "Apps", "items": []})
            report["sections"].append(SystemAudit.check_rbac() or {"title": "RBAC", "items": []})
            report["sections"].append(SystemAudit.check_environment() or {"title": "Environment", "items": []})
            report["sections"].append(SystemAudit.check_storage() or {"title": "Storage", "items": []})
        except Exception as e:
            # Fallback if any check completely crashes
            report["sections"].append({"title": "System Error", "items": [{"label": "Error", "value": str(e), "status": "critical"}]})
        
        # Overall status
        all_ok = True
        warning_count = 0
        critical_count = 0
        
        for section in report["sections"]:
            # Ensure items exists and is a list
            if not isinstance(section.get("items"), list):
                section["items"] = []
                
            for item in section["items"]:
                if item.get("status") == "warning":
                    warning_count += 1
                elif item.get("status") == "critical":
                    critical_count += 1
                    all_ok = False
        
        report["summary"] = {
            "status": "ok" if all_ok and warning_count == 0 else "warning" if all_ok else "critical",
            "warning_count": warning_count,
            "critical_count": critical_count
        }
        
        return report

    @staticmethod
    def check_database():
        section = {"title": "Database Health", "items": []}
        try:
            start = time.time()
            db.session.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000
            section["items"].append({
                "label": "Connectivity",
                "value": f"OK ({latency:.2f}ms)",
                "status": "ok" if latency < 100 else "warning"
            })
        except Exception as e:
            section["items"].append({
                "label": "Connectivity",
                "value": str(e),
                "status": "critical"
            })
            return section

        # Check for drifts
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
            
            missing_tables = []
            column_drifts = []
            
            for tbl_name, model in seen.items():
                if tbl_name not in existing_tables:
                    missing_tables.append(tbl_name)
                    continue
                
                live_cols = {c["name"]: c for c in inspector.get_columns(tbl_name)}
                sa_table = model.__table__
                for col in sa_table.columns:
                    if col.name not in live_cols:
                        column_drifts.append(f"{tbl_name}.{col.name} (missing)")
                    else:
                        live_type = str(live_cols[col.name]["type"]).upper()
                        try:
                            target_type = col.type.compile(dialect=db.engine.dialect).upper()
                        except Exception:
                            target_type = str(col.type).upper()
                        
                        live_type = live_type.replace("TINYINT(1)", "BOOLEAN").replace("INTEGER", "INT")
                        target_type = target_type.replace("TINYINT(1)", "BOOLEAN").replace("INTEGER", "INT")
                        
                        if live_type != target_type and not (live_type.startswith(target_type) or target_type.startswith(live_type)):
                            column_drifts.append(f"{tbl_name}.{col.name} (type mismatch)")

            section["items"].append({
                "label": "Missing Tables",
                "value": f"{len(missing_tables)} detected",
                "status": "ok" if not missing_tables else "critical",
                "details": missing_tables
            })
            section["items"].append({
                "label": "Model Drifts",
                "value": f"{len(column_drifts)} detected",
                "status": "ok" if not column_drifts else "warning",
                "details": column_drifts
            })
        except Exception as e:
            section["items"].append({"label": "Schema Check", "value": str(e), "status": "critical"})

        return section

    @staticmethod
    def check_apps():
        section = {"title": "App Integrity", "items": []}
        from arasCore.admin.models import AppManagerApp
        from arasCore.lib.services.blueprints import get_helper_registry

        try:
            apps = AppManagerApp.query.all()
            helper_registry = get_helper_registry()
            
            no_manifest = []
            active_no_manifest = []
            
            for a in apps:
                helper = helper_registry.get(a.slug)
                if not helper:
                    pkg_name = f"app.{a.slug}"
                    try:
                        mod = importlib.import_module(f"{pkg_name}.manifest")
                        helper = getattr(mod, "helper", None)
                    except ModuleNotFoundError:
                        helper = None
                
                if not helper:
                    no_manifest.append(a.slug)
                    if a.is_active:
                        active_no_manifest.append(a.slug)

            section["items"].append({
                "label": "App Manifests",
                "value": f"{len(no_manifest)} apps without manifest",
                "status": "ok" if not active_no_manifest else "warning",
                "details": active_no_manifest
            })
        except Exception as e:
            section["items"].append({"label": "App Check", "value": str(e), "status": "critical"})

        return section

    @staticmethod
    def check_rbac():
        section = {"title": "RBAC Consistency", "items": []}
        try:
            from arasCore.auth import User, Role
            user_count = User.query.count()
            role_count = Role.query.count()
            
            # Orphaned users (no roles)
            orphans = User.query.filter(~User.roles.any()).count()
            
            section["items"].append({
                "label": "Users & Roles",
                "value": f"{user_count} users, {role_count} roles",
                "status": "ok"
            })
            section["items"].append({
                "label": "Orphaned Users",
                "value": f"{orphans} users with no roles",
                "status": "ok" if orphans == 0 else "warning"
            })
        except Exception as e:
            section["items"].append({"label": "RBAC Check", "value": str(e), "status": "critical"})
        return section

    @staticmethod
    def check_environment():
        section = {"title": "Security & Environment", "items": []}
        
        is_debug = current_app.config.get("DEBUG")
        section["items"].append({
            "label": "Debug Mode",
            "value": "Enabled" if is_debug else "Disabled",
            "status": "warning" if is_debug else "ok"
        })
        
        env = os.getenv("ARAS_MODE", "production")
        section["items"].append({
            "label": "Flask Environment",
            "value": env,
            "status": "ok" if env == "production" else "warning"
        })
        
        secret_key = current_app.config.get("SECRET_KEY")
        is_default_secret = secret_key == "dev-key" or not secret_key
        section["items"].append({
            "label": "Secret Key",
            "value": "Default/Unset" if is_default_secret else "Configured",
            "status": "critical" if is_default_secret else "ok"
        })
        
        return section

    @staticmethod
    def check_storage():
        section = {"title": "Storage & Files", "items": []}
        upload_path = current_app.config.get("UPLOAD_FOLDER", "uploads")
        
        exists = os.path.exists(upload_path)
        writable = os.access(upload_path, os.W_OK) if exists else False
        
        section["items"].append({
            "label": "Upload Folder",
            "value": "Writable" if writable else "Not Writable/Missing",
            "status": "ok" if writable else "critical"
        })
        
        return section
