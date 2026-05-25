import os
from jose import jwt
from jose.exceptions import JWTError
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Reading configuration from environment variables as specified
SECRET_KEY = os.getenv("ARAS_LICENSE_SECRET", "default-secret-key-for-dev")
DEFAULT_EXPIRY_DAYS = int(os.getenv("ARAS_LICENSE_EXPIRY_DAYS", "30"))
ISSUER = "aras-control-panel"


def issue_license_token(
    tenant_id: str,
    expiry_days: Optional[int] = None,
    secret_key: Optional[str] = None,
) -> str:
    """
    Generates a signed JWT license token for a tenant.

    Args:
        tenant_id: The subject of the token, identifying the tenant.
        expiry_days: The number of days until the token expires. Defaults to
                     the value of ARAS_LICENSE_EXPIRY_DAYS env var or 30.
        secret_key: The secret key for signing. Defaults to ARAS_LICENSE_SECRET.

    Returns:
        A signed JWT as a string.
    """
    if expiry_days is None:
        expiry_days = DEFAULT_EXPIRY_DAYS
    if secret_key is None:
        secret_key = SECRET_KEY

    issue_time = datetime.now(timezone.utc)
    expiry_time = issue_time + timedelta(days=expiry_days)

    payload = {
        "sub": tenant_id,
        "exp": expiry_time,
        "iat": issue_time,
        "iss": ISSUER,
        "aud": "aras-instance",  # Audience claim
    }

    logger.info(
        f"Issuing license for tenant '{tenant_id}' valid until {expiry_time.isoformat()}"
    )

    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_license_token(
    token: str, secret_key: Optional[str] = None
) -> Optional[Dict]:
    """
    Verifies a license token's signature and expiry.

    Args:
        token: The JWT to verify.
        secret_key: The secret key for verification. Defaults to ARAS_LICENSE_SECRET.

    Returns:
        The decoded payload as a dictionary if verification is successful,
        otherwise None.
    """
    if secret_key is None:
        secret_key = SECRET_KEY

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"],
            issuer=ISSUER,
            audience="aras-instance",
        )
        return payload
    except JWTError as e:
        logger.error(f"Failed to decode license token: {e}")

    return None


def days_until_expiry(token: str) -> Optional[int]:
    """
    Calculates the number of days until a license token expires.

    This function checks the 'exp' claim without verifying the signature,
    making it useful for quick checks or reminder notifications.

    Args:
        token: The JWT license token.

    Returns:
        The number of days remaining until expiry as an integer. Returns a
        negative number if the token has already expired. Returns None if
        the token is invalid or does not contain an 'exp' claim.
    """
    try:
        # Decode without verification to inspect claims
        payload = jwt.get_unverified_claims(token)
        exp_timestamp = payload.get("exp")

        if not exp_timestamp:
            return None

        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        remaining = exp_datetime - datetime.now(timezone.utc)

        return remaining.days
    except JWTError as e:
        logger.error(f"Could not decode token to check expiry: {e}")
        return None
