# gemini-flash
import logging
from sqlalchemy.orm import Session
from ..registry.audit_log import AuditLog

logger = logging.getLogger(__name__)

# claude-sonnet-4-6
PII_FIELDS = frozenset({
    'password', 'password_hash', 'token', 'refresh_token', 'secret',
    'email', 'phone', 'address', 'card', 'pan', 'cvv',
    'bank_account', 'tax_id', 'national_id', 'passport',
    'saas_license_token', 'api_key'
})

# gemini-flash
def redact_pii(diff: dict, model_cls=None) -> dict:
    """
    Recursively redacts PII from a dictionary or list.
    If model_cls is provided, it also checks for pii=True tags on columns.
    """
    if not isinstance(diff, (dict, list)):
        return diff

    if isinstance(diff, list):
        return [redact_pii(item, model_cls) for item in diff]

    redacted = {}
    for k, v in diff.items():
        is_pii_field = k.lower() in PII_FIELDS
        
        # Check model metadata if available
        if not is_pii_field and model_cls and hasattr(model_cls, "__table__"):
            col = model_cls.__table__.columns.get(k)
            if col is not None and col.info.get("pii"):
                is_pii_field = True

        if is_pii_field:
            if isinstance(v, list) and len(v) == 2:
                # Handle [old, new] diff format
                redacted[k] = ["[redacted]", "[redacted]"]
            else:
                redacted[k] = "[redacted]"
        else:
            redacted[k] = redact_pii(v, model_cls)
    return redacted

class AuditService:
    @staticmethod
    def record(db: Session, table: str, row_id: str, action: str, diff: dict, user_id: int = None):
        """
        Records an audit entry in the audit_log table.
        """
        try:
            # gemini-3-flash-preview: Enforce PII redaction
            safe_diff = redact_pii(diff)

            # Resolve tenant_id from DB
            from .config import config
            tenant_id = config._get_tenant_id(db)
            
            log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                table_name=table,
                row_id=str(row_id),
                action=action,
                diff_json=safe_diff
            )
            db.add(log)
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

audit = AuditService
