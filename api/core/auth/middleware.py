import os
import logging
from fastapi import Depends, HTTPException, status
from typing import Dict

from .license import verify_license_token, days_until_expiry

logger = logging.getLogger(__name__)

# Default path for the license file, can be overridden by environment variable
DEFAULT_LICENSE_PATH = os.path.join("data", "license.jwt")
LICENSE_PATH = os.getenv("ARAS_LICENSE_PATH", DEFAULT_LICENSE_PATH)

# Cache the license in memory to avoid reading the file on every request
_license_cache: Dict[str, any] = {"token": None, "payload": None, "verified": False}


def get_license_payload() -> Dict:
    """
    A dependency that reads, verifies, and caches the instance license.

    It reads the license token from the path specified by ARAS_LICENSE_PATH.
    If the license is valid, it returns the decoded payload.
    If invalid or expired, it raises an HTTP 403 Forbidden error.

    Raises:
        HTTPException: 403 Forbidden if the license is missing, invalid, or expired.

    Returns:
        The decoded JWT payload as a dictionary.
    """
    # Use cached result if available and verified
    if _license_cache.get("verified"):
        return _license_cache["payload"]

    try:
        with open(LICENSE_PATH, "r") as f:
            token = f.read().strip()
    except FileNotFoundError:
        logger.critical(f"License file not found at '{LICENSE_PATH}'.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Instance license is missing. Please contact support.",
        )

    payload = verify_license_token(token)

    if not payload:
        days_left = days_until_expiry(token)
        if days_left is not None and days_left < 0:
            logger.error("Instance license has expired.")
            detail = "Instance license has expired. Please renew your license."
        else:
            logger.error("Instance license is invalid.")
            detail = "Instance license is invalid or corrupted. Please contact support."
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    # Cache the valid license payload
    _license_cache["token"] = token
    _license_cache["payload"] = payload
    _license_cache["verified"] = True

    # Attempt renewal if approaching expiry (after caching — runs async-ish, next request picks up new token)
    renew_license_if_needed(token)

    logger.info(
        f"Instance license verified for tenant '{payload.get('sub')}'. "
        f"Expires in {days_until_expiry(token)} days."
    )

    return payload


def renew_license_if_needed(token: str):
    import httpx
    
    days = days_until_expiry(token)
    if days is not None and 0 <= days <= 7:
        control_plane_url = os.getenv("ARAS_CONTROL_PLANE_URL", "http://localhost:8000")
        try:
            payload = verify_license_token(token)
            tenant_id = payload.get("sub") if payload else "unknown"
            
            with httpx.Client() as client:
                res = client.post(
                    f"{control_plane_url}/api/v1/saas/license/renew",
                    json={"tenant_id": tenant_id, "current_token": token},
                    timeout=5.0
                )
                if res.status_code == 200:
                    new_token = res.json().get("token")
                    if new_token:
                        with open(LICENSE_PATH, "w") as f:
                            f.write(new_token)
                        _license_cache["verified"] = False
                        _license_cache["token"] = None
                        _license_cache["payload"] = None
                        logger.info("License automatically renewed successfully.")
                else:
                    logger.warning(f"Failed to auto-renew license: {res.text}")
        except Exception as e:
            logger.warning(f"Failed to auto-renew license (network/error): {e}")


# Alias for clarity in router dependencies
verify_instance_license = Depends(get_license_payload)
