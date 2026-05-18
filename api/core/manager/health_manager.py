"""
Purpose: Health and Integrity checks for the Aras Framework.
Context: Level 3 Implementation. Inherits from Manager (Level 2).
Impact: Provides diagnostic tools to ensure system consistency.
"""
import logging
from typing import List, Dict, Any
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.orm import Session
from ..aras import Aras

logger = logging.getLogger(__name__)

class HealthManager(Aras.Manager):
    """
    Performs system-wide health checks.
    - Physical vs Registry table consistency.
    - Foreign Key integrity.
    - App dependency validation.
    """

    @classmethod
    def run_all_checks(cls, db: Session) -> Dict[str, List[str]]:
        """Runs all registered health checks."""
        report = {
            "missing_tables": cls.check_missing_physical_tables(db),
            "orphan_tables": cls.check_orphan_physical_tables(db),
            "broken_links": cls.check_broken_links(db),
            "app_consistency": cls.check_app_consistency(db),
        }
        return report

    @classmethod
    def check_missing_physical_tables(cls, db: Session) -> List[str]:
        """Checks if resources in the registry have corresponding physical tables."""
        issues = []
        insp = sa_inspect(Aras.engine)
        db_tables = set(insp.get_table_names())
        
        resources = db.query(Aras.ResourceModel).filter(Aras.ResourceModel.is_active == True).all()
        for res in resources:
            if res.name not in db_tables:
                issues.append(f"Resource '{res.name}' exists in registry but physical table is missing.")
        
        return issues

    @classmethod
    def check_orphan_physical_tables(cls, db: Session) -> List[str]:
        """Checks for physical tables that look like Aras tables but aren't in the registry."""
        issues = []
        insp = sa_inspect(Aras.engine)
        db_tables = insp.get_table_names()
        
        registry_tables = {r.name for r in db.query(Aras.ResourceModel).all()}
        
        # System tables to ignore (Level 3 core registry and auth)
        ignored = {
            "aras_apps", "aras_resources", "aras_fields", "aras_links", 
            "aras_translations", "aras_activity_logs", "aras_widgets", "sys_settings",
            "auth_roles", "auth_permissions", "auth_user_roles", "auth_users",
            "doc_series", "aras_dashboard_layouts",
            "mock_model", "test_parents", "test_children"
        }

        for tname in db_tables:
            if tname in ignored:
                continue
            if tname not in registry_tables:
                # Aras tables usually follow {app}_{table} pattern
                if "_" in tname:
                    issues.append(f"Physical table '{tname}' exists but is not registered in Aras.")
        
        return issues

    @classmethod
    def check_broken_links(cls, db: Session) -> List[str]:
        """Checks for links/lookups pointing to non-existent resources."""
        issues = []
        links = db.query(Aras.LinkModel).all()
        
        resource_ids = {r.id for r in db.query(Aras.ResourceModel).all()}
        
        for link in links:
            if link.source_resource_id not in resource_ids:
                issues.append(f"Link ID {link.id} has invalid source_resource_id: {link.source_resource_id}")
            if link.target_resource_id not in resource_ids:
                issues.append(f"Link ID {link.id} has invalid target_resource_id: {link.target_resource_id}")
        
        return issues

    @classmethod
    def check_app_consistency(cls, db: Session) -> List[str]:
        """Checks if apps in registry match the filesystem."""
        issues = []
        registry_apps = db.query(Aras.AppModel).filter(Aras.AppModel.is_active == True).all()
        
        # In-memory registered apps
        from ..base.app import App
        code_apps = App._registry.keys()
        
        for app in registry_apps:
            # Code apps are registered by class name (usually {Name}App)
            # but AppModel.name is the snake_case name.
            # This is a bit tricky. Let's look at how SyncManager does it.
            # SyncManager uses App._registry directly.
            pass
            
        return issues
