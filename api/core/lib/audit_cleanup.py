# claude-sonnet-4-6
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# claude-sonnet-4-6
def cleanup_expired_audit_logs(db: Session) -> int:
    result = db.execute(
        text(
            "DELETE FROM core_audit_log "
            "WHERE retention_days IS NOT NULL "
            "AND ts < NOW() - (retention_days * INTERVAL '1 day')"
        )
    )
    count = result.rowcount
    db.commit()
    if count:
        logger.info(f"[audit_cleanup] Deleted {count} expired audit log records")
    return count
