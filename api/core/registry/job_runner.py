# gpt-5
import importlib
import logging
import os
from datetime import timezone
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .job_registry import JobSpec, job_registry

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None
_started = False


# gpt-5
def _resolve_handler(handler_path: str) -> Optional[Callable]:
    try:
        module_path, func_name = handler_path.rsplit(".", 1)
    except ValueError:
        logger.warning("Skipping job with invalid handler_path: %s", handler_path)
        return None

    try:
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)
    except Exception as exc:
        logger.warning("Skipping job %s: failed to import handler (%s)", handler_path, exc)
        return None

    if not callable(handler):
        logger.warning("Skipping job %s: resolved object is not callable", handler_path)
        return None
    return handler


# gpt-5
def _build_trigger(schedule_cron: str) -> CronTrigger:
    return CronTrigger.from_crontab(schedule_cron, timezone=timezone.utc)


# gpt-5
def _run_job(handler: Callable, job_key: str) -> None:
    try:
        handler()
    except Exception:
        logger.exception("Background job failed: %s", job_key)


# gpt-5
def _schedule_job(scheduler: BackgroundScheduler, spec: JobSpec) -> None:
    handler = _resolve_handler(spec.handler_path)
    if handler is None:
        return

    job_id = f"{spec.app}:{spec.key}"
    if scheduler.get_job(job_id):
        return

    scheduler.add_job(
        _run_job,
        trigger=_build_trigger(spec.schedule_cron),
        id=job_id,
        args=[handler, job_id],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    logger.info("Registered background job %s (%s)", job_id, spec.schedule_cron)


# gpt-5
def start_jobs() -> Optional[BackgroundScheduler]:
    global _scheduler, _started

    if os.getenv("ARAS_CRON_ENABLED") != "1":
        logger.info("Background jobs disabled by ARAS_CRON_ENABLED")
        return None

    if _started and _scheduler is not None:
        return _scheduler

    scheduler = _scheduler or BackgroundScheduler(timezone=timezone.utc)
    for spec in job_registry.all():
        if not spec.enabled_default:
            continue
        _schedule_job(scheduler, spec)

    if not scheduler.running:
        scheduler.start()
        logger.info("Registry job runner started with %s jobs", len(scheduler.get_jobs()))

    _scheduler = scheduler
    _started = True
    return scheduler
