# gemini-flash
import os
import base64
import hashlib
from cryptography.fernet import Fernet

def _get_fernet(tenant_id: str) -> Fernet:
    master_secret = os.environ.get("ARAS_SECRET_MASTER", "default-secret-change-me")
    # Derive a per-tenant key
    salt = tenant_id or "global"
    key_material = hashlib.pbkdf2_hmac(
        'sha256', 
        master_secret.encode(), 
        salt.encode(), 
        100000
    )
    key = base64.urlsafe_b64encode(key_material)
    return Fernet(key)

def encrypt(value: str, tenant_id: str) -> str:
    if not value:
        return ""
    f = _get_fernet(tenant_id)
    return f.encrypt(value.encode()).decode()

def decrypt(value: str, tenant_id: str) -> str:
    if not value:
        return ""
    try:
        f = _get_fernet(tenant_id)
        return f.decrypt(value.encode()).decode()
    except Exception:
        return "ERROR_DECRYPTING"

def mask(value: str) -> str:
    if not value:
        return ""
    return "••••"
