import pytest
import os
import re
from core.base.app import App
from core.base.model import Model

def test_table_naming_rules():
    """Assert framework models use core_* and app models use <app_name>_*."""
    errors = []
    
    # Test registry/framework models
    for name, cls in Model._registry.items():
        if not hasattr(cls, "__tablename__"):
            continue
            
        module_name = cls.__module__
        table_name = cls.__tablename__
        
        if table_name.startswith("aras_") or table_name.startswith("erp_"):
            errors.append(f"Model {cls.__name__} in {module_name} uses deprecated prefix: {table_name}")
            
        if "core." in module_name:
            if not table_name.startswith("core_"):
                # some legacy core tables might be exempt (like translations, numbering_sequences but we renamed them)
                errors.append(f"Framework model {cls.__name__} in {module_name} must start with 'core_': {table_name}")
                
        if "apps." in module_name:
            # find app name from module path apps.<app_name>
            parts = module_name.split(".")
            if len(parts) > 1:
                app_name = parts[1]
                if not (table_name.startswith(f"{app_name}_") or table_name.startswith("core_")):
                    errors.append(f"App model {cls.__name__} in {module_name} must start with '{app_name}_' or 'core_': {table_name}")

    if errors:
        pytest.fail("\n".join(errors))

def test_no_legacy_prefixes_in_source():
    errors = []
    # Patterns to match: ForeignKey("erp_...", info={"target_resource": "erp/..."
    patterns = [
        r'ForeignKey\([\'"](erp_[^\'"]+|aras_[^\'"]+)[\'"]\)',
        r'[\'"]target_resource[\'"]\s*:\s*[\'"](erp/[^\'"]+|aras/[^\'"]+)[\'"]',
        r'[\'"]table[\'"]\s*:\s*[\'"](erp_[^\'"]+|aras_[^\'"]+)[\'"]',
        r'resource\s*:\s*[\'"]?(erp_[^\'s"\'\}]+|aras_[^\'s"\'\}]+)[\'"]?',
    ]
    
    for root, _, files in os.walk("api"):
        for f in files:
            if not (f.endswith(".py") or f.endswith(".yaml") or f.endswith(".json")):
                continue
            path = os.path.join(root, f)
            # Skip migrations and this test file itself
            if "alembic/versions" in path or "tests/test_naming_rules.py" in path or "node_modules" in path:
                continue
            
            with open(path, "r") as file:
                content = file.read()
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        errors.append(f"Found legacy prefix matching '{pattern}' in {path}: {matches}")
                
    if errors:
        pytest.fail("\n".join(errors))

def test_no_legacy_db_names_in_source():
    """Assert no 'aras_tenant_', 'aras_dev', 'aras_control' string literals appear in source."""
    errors = []
    patterns = [
        r'["\']aras_tenant_',
        r'["\']aras_dev["\']',
        r'["\']aras_control["\']',
    ]
    
    # Path sub-strings to allow
    allow_paths = [
        "api/core/lib/config.py",
        "api/core/migrations/rename_naming_series.py",
        "api/core/logic/auto_migrate.py",
        "tests/test_naming_rules.py"
    ]
    
    for root, _, files in os.walk("api"):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            
            if any(path.endswith(allowed) for allowed in allow_paths):
                continue
                
            with open(path, "r") as file:
                content = file.read()
                for pattern in patterns:
                    if re.search(pattern, content):
                        errors.append(f"Found legacy DB name pattern '{pattern}' in {path}")
                        
    if errors:
        pytest.fail("\n".join(errors))
