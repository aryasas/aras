# gemini-pro
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.auth.service import create_access_token
from core.auth.license import issue_license_token, verify_license_token, days_until_expiry
from core.lib.settings import settings

def test_activation_token():
    print("=== Testing Activation (Setup) Token ===")
    email = "test@example.com"
    tenant_id = "test-tenant-1"
    
    # 1. Valid Token
    token = create_access_token(
        {"sub": email, "purpose": "portal_setup", "tenant": tenant_id},
        expires_delta=timedelta(hours=1)
    )
    print(f"Generated Token: {token[:20]}...")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"SUCCESS: Decoded payload: {payload}")
    except JWTError as e:
        print(f"FAILED: Could not decode: {e}")

    # 2. Expired Token (simulated by using a past expiry)
    expired_token = jwt.encode(
        {"sub": email, "purpose": "portal_setup", "tenant": tenant_id, "exp": datetime.now(timezone.utc) - timedelta(seconds=10)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    print(f"\nTesting Expired Activation Token...")
    try:
        jwt.decode(expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("FAILED: Expired token was accepted!")
    except JWTError as e:
        print(f"SUCCESS: Expired token rejected. Error: {e}")

def test_license_token():
    print("\n=== Testing License Token ===")
    tenant_id = "tenant-1-1"
    
    # 1. Valid License
    print("Issuing 30-day license...")
    token = issue_license_token(tenant_id, expiry_days=30)
    days = days_until_expiry(token)
    print(f"Days until expiry: {days}")
    
    payload = verify_license_token(token)
    if payload:
        print(f"SUCCESS: License verified. Tenant: {payload.get('sub')}")
    else:
        print("FAILED: License verification failed.")

    # 2. Expired License
    print("\nTesting Expired License Token...")
    # We use -1 days to issue an already expired token
    expired_token = issue_license_token(tenant_id, expiry_days=-1)
    days = days_until_expiry(expired_token)
    print(f"Days until expiry: {days}")
    
    payload = verify_license_token(expired_token)
    if payload:
        print("FAILED: Expired license was accepted!")
    else:
        print("SUCCESS: Expired license rejected by verify_license_token.")

    # 3. Invalid Secret
    print("\nTesting Invalid Secret...")
    payload = verify_license_token(token, secret_key="wrong-secret")
    if payload:
        print("FAILED: License with wrong secret was accepted!")
    else:
        print("SUCCESS: License with wrong secret rejected.")

if __name__ == "__main__":
    # Ensure settings are loaded
    os.environ["ARAS_LICENSE_SECRET"] = "test-license-secret"
    test_activation_token()
    test_license_token()
