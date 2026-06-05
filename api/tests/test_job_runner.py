from pathlib import Path

from fastapi.testclient import TestClient


# gpt-5
def _reset_runner_state():
    import core.registry.job_runner as job_runner

    if job_runner._scheduler is not None and job_runner._scheduler.running:
        job_runner._scheduler.shutdown(wait=False)
    job_runner._scheduler = None
    job_runner._started = False


# gpt-5
def test_job_runner_registers_manifest_jobs_and_skips_bad_handlers(monkeypatch, caplog):
    from core.registry.job_registry import JobSpec, job_registry
    from core.registry.job_runner import start_jobs
    from main import app

    monkeypatch.setenv("ARAS_CRON_ENABLED", "1")
    _reset_runner_state()

    with TestClient(app):
        assert job_registry.get("stock", "low-stock-digest") is not None
        assert job_registry.get("accounting", "overdue-ar-digest") is not None
        assert job_registry.get("saas", "billing-daily") is not None

    _reset_runner_state()
    job_registry.register("test", "bogus", JobSpec(
        key="bogus",
        schedule_cron="0 1 * * *",
        handler_path="apps.missing.jobs.nope",
        app="test",
        enabled_default=True,
    ))

    scheduler = start_jobs()
    scheduler_again = start_jobs()

    assert scheduler is scheduler_again
    assert scheduler.running
    assert "failed to import handler" in caplog.text

    runner_source = (Path(__file__).resolve().parents[1] / "core" / "registry" / "job_runner.py").read_text(encoding="utf-8")
    assert "from apps" not in runner_source
    _reset_runner_state()
