# gemini-2-5-flash
from core import Aras
from ..models import RequestLog
from sqlalchemy import func
from datetime import datetime, timedelta

class MetricsService(Aras):
    @classmethod
    def tenant_usage(cls, db, tenant_id):
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        request_count = db.query(func.count(RequestLog.id)).filter(
            RequestLog.tenant_id == tenant_id,
            RequestLog.ts >= thirty_days_ago
        ).scalar()
        
        return {
            "storage_bytes": 0,
            "request_count_30d": request_count or 0,
            "active_users_30d": 0,
            "last_login_at": None,
            "db_size_bytes": 0
        }
