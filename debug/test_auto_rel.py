from app.erp.erp_config.models.currency import FxRate
from arasCore.lib.core.base_model import db

print(f"Checking FxRate relationships...")
# Access the automatically generated relations
try:
    print(f"Has 'from_currency': {hasattr(FxRate, 'from_currency')}")
    print(f"Has 'to_currency': {hasattr(FxRate, 'to_currency')}")
    print(f"Has 'company': {hasattr(FxRate, 'company')}")
except Exception as e:
    print(f"Error: {e}")
