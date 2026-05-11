# -*- coding: utf-8 -*-
"""
arasCore/lib/core/tasks.py
=========================
Background task queue using Huey.
Supports SqliteHuey for zero-config and RedisHuey for production.
"""
import os
import logging
from huey import SqliteHuey, RedisHuey, MemoryHuey

logger = logging.getLogger(__name__)

# Huey initialization
def init_huey(app=None):
    """
    Configure Huey based on environment or app config.
    Returns the Huey instance.
    """
    storage_type = os.getenv("HUEY_STORAGE", "sqlite").lower()
    
    if storage_type == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        huey_instance = RedisHuey('aras-huey', url=redis_url)
        logger.info(f"[tasks] Initialized RedisHuey at {redis_url}")
    elif storage_type == "memory":
        huey_instance = MemoryHuey('aras-huey')
        logger.info("[tasks] Initialized MemoryHuey (non-persistent)")
    else:
        # Default: SQLite in project root
        db_path = os.path.join(os.getcwd(), 'huey_tasks.db')
        huey_instance = SqliteHuey('aras-huey', filename=db_path)
        logger.info(f"[tasks] Initialized SqliteHuey at {db_path}")
        
    return huey_instance

# Global huey instance
huey = init_huey()

def task_wrapper(fn):
    """Decorator to mark a function as a background task."""
    return huey.task()(fn)
