# claude-sonnet-4-6
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..registry.series import Series

logger = logging.getLogger(__name__)

class NumberingService:
    """
    Unified service for generating sequential document numbers.
    Uses the 'core_series' table as the primary registry.
    """

    @classmethod
    def get_next(cls, db: Session, key: str, default_prefix: str = "") -> str:
        """
        Atomically increments the series and returns the formatted string.
        """
        # gemini-3-flash-preview: Use FOR UPDATE for atomicity
        stmt = select(Series).where(Series.key == key).with_for_update()
        series = db.scalar(stmt)

        now = datetime.now(timezone.utc)
        year = now.year

        if not series:
            # Auto-create series if missing
            prefix = default_prefix or (key.split('_')[-1][:3].upper() + "-")
            series = Series(
                key=key,
                prefix=prefix,
                next_value=1,
                last_reset_year=year,
                format="{prefix}{year}{next_value:04d}"
            )
            db.add(series)
            db.flush()
        else:
            # Handle yearly reset
            if series.config and series.config.get("reset_yearly") and series.last_reset_year != year:
                series.next_value = 1
                series.last_reset_year = year
            
        current_val = series.next_value
        prefix = series.prefix or ""
        
        try:
            # Support both python format and custom token replacement
            fmt = series.format or "{prefix}{year}{next_value:04d}"
            if "{" in fmt:
                formatted = fmt.format(
                    prefix=prefix,
                    year=year,
                    YYYY=year,
                    YY=str(year)[2:],
                    MM=f"{now.month:02d}",
                    DD=f"{now.day:02d}",
                    next_value=current_val,
                    seq=current_val
                )
            else:
                formatted = f"{prefix}{year}{current_val:04d}"
        except Exception as e:
            logger.error(f"Failed to format naming series {key}: {e}")
            formatted = f"{prefix}{year}{current_val:04d}"

        series.next_value += 1
        db.flush()
        return formatted

    @classmethod
    def peek_next(cls, db: Session, key: str) -> Optional[str]:
        """Return the next formatted number without incrementing the counter."""
        series = db.scalar(select(Series).where(Series.key == key))
        if not series:
            return None
            
        now = datetime.now(timezone.utc)
        year = now.year
        current_val = series.next_value
        
        if series.config and series.config.get("reset_yearly") and series.last_reset_year != year:
            current_val = 1
            
        prefix = series.prefix or ""
        try:
            fmt = series.format or "{prefix}{year}{next_value:04d}"
            return fmt.format(prefix=prefix, year=year, YYYY=year, next_value=current_val, seq=current_val)
        except Exception:
            return f"{prefix}{year}{current_val:04d}"

# Singleton instance
numbering = NumberingService
SeriesManager = NumberingService # gemini-3-flash-preview: Alias for backward compatibility
