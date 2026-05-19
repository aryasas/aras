"""
Purpose: Logic for generating sequential document numbers.
Context: Level 2 Manager.
Impact: Provides atomic incrementing and formatting for naming series.
"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from ..registry.series import Series
from .manager import Manager

logger = logging.getLogger(__name__)

class SeriesManager(Manager):
    """Orchestrates sequential numbering generation."""

    @classmethod
    def get_next(cls, db: Session, key: str, default_prefix: str = "") -> str:
        """
        Atomically increments the series and returns the formatted string.
        Format: {prefix}{year}{next_value:04d}
        """
        # Use SELECT ... FOR UPDATE to ensure atomicity in concurrent environments
        stmt = select(Series).where(Series.key == key).with_for_update()
        series = db.scalar(stmt)

        now = datetime.now()
        year = now.year

        if not series:
            series = Series(
                key=key,
                prefix=default_prefix or key.split('_')[-1][:3].upper() + "-",
                next_value=1,
                last_reset_year=year
            )
            db.add(series)
            db.flush()
        else:
            # Handle yearly reset if configured
            if series.config.get("reset_yearly") and series.last_reset_year != year:
                series.next_value = 1
                series.last_reset_year = year
            
        current_val = series.next_value
        prefix = series.prefix or ""
        
        # Simple formatting logic
        try:
            formatted = series.format.format(
                prefix=prefix,
                year=year,
                next_value=current_val
            )
        except Exception as e:
            logger.error(f"Failed to format naming series {key}: {e}")
            formatted = f"{prefix}{year}{current_val:04d}"

        # Increment for next time
        series.next_value += 1
        db.flush()

        return formatted

    @classmethod
    def peek_next(cls, db: Session, key: str) -> Optional[str]:
        """Return the next formatted number without incrementing the counter."""
        from sqlalchemy import select as sa_select
        series = db.scalar(sa_select(Series).where(Series.key == key))
        if not series:
            return None
        now = datetime.now()
        year = now.year
        current_val = series.next_value
        if series.config.get("reset_yearly") and series.last_reset_year != year:
            current_val = 1
        prefix = series.prefix or ""
        try:
            return series.format.format(prefix=prefix, year=year, next_value=current_val)
        except Exception:
            return f"{prefix}{year}{current_val:04d}"
