import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'api'))

from core import Aras
from apps.erp.config.models import Company
from apps.erp.accounting.models import Account # Import explicitly
from core.logic.ui_generator import UIGenerator

# Discover apps first
Aras.logic.discovery.discover_apps(package_path="apps")

# Generate metadata for Company
meta = UIGenerator.generate_metadata(Company)

for field in meta['fields']:
    if 'acc_bank' in field['name']:
        print(f"Field: {field['name']}, Target Resource: {field['target_resource']}")
