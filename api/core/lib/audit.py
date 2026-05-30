# gemini-flash
import logging
from sqlalchemy.orm import Session
from ..registry.audit_log import AuditLog

logger = logging.getLogger(__name__)

class AuditService:
    @staticmethod
    def record(db: Session, table: str, row_id: str, action: str, diff: dict, user_id: int = None):
        """
        Records an audit entry in the audit_log table.
        """
        try:
            # Resolve tenant_id from DB
            from .config import config
            tenant_id = config._get_tenant_id(db)
            
            log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                table_name=table,
                row_id=str(row_id),
                action=action,
                diff_json=diff
            )
            db.add(log)
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

audit = AuditService
