# -*- coding: utf-8 -*-
"""DB backup service — gz-compressed mysqldump to instance/backups/.

Used both as a CLI command (`flask aras db-backup`) and as a pre-migration
safety hook (auto_migrate calls `backup_before_destructive` before any drop).
"""
import os
import gzip
import shutil
import subprocess
from datetime import datetime
from urllib.parse import urlparse, unquote

from flask import current_app


def _parse_db_url(uri: str) -> dict:
    """Extract host/port/user/password/db from a SQLAlchemy URL."""
    p = urlparse(uri)
    return {
        "host": p.hostname or "localhost",
        "port": str(p.port or 3306),
        "user": unquote(p.username or ""),
        "password": unquote(p.password or ""),
        "db": (p.path or "/").lstrip("/"),
    }


def _backup_dir(flask_app=None) -> str:
    app = flask_app or current_app
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    path = os.path.join(root, "instance", "backups")
    os.makedirs(path, exist_ok=True)
    return path


def _find_dump_binary() -> str:
    """Prefer mariadb-dump, fall back to mysqldump."""
    for name in ("mariadb-dump", "mysqldump"):
        p = shutil.which(name)
        if p:
            return p
    raise RuntimeError("Neither mariadb-dump nor mysqldump found on PATH")


def run_backup(flask_app=None, *, label: str = "manual") -> str:
    """Dump the configured DB to instance/backups/<db>_<label>_<ts>.sql.gz.

    Returns the absolute path of the created file.
    Raises RuntimeError on failure — callers (esp. auto_migrate) should catch
    and abort the destructive op when this fails.
    """
    app = flask_app or current_app
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not uri:
        raise RuntimeError("SQLALCHEMY_DATABASE_URI not configured")

    cfg = _parse_db_url(uri)
    if not cfg["db"]:
        raise RuntimeError(f"Cannot parse database name from URI: {uri}")

    binary = _find_dump_binary()
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(_backup_dir(app), f"{cfg['db']}_{label}_{ts}.sql.gz")

    cmd = [
        binary,
        f"--host={cfg['host']}",
        f"--port={cfg['port']}",
        f"--user={cfg['user']}",
        "--single-transaction",
        "--quick",
        "--routines",
        "--triggers",
        "--events",
        "--default-character-set=utf8mb4",
        cfg["db"],
    ]
    env = os.environ.copy()
    if cfg["password"]:
        env["MYSQL_PWD"] = cfg["password"]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        with gzip.open(out, "wb") as gz:
            shutil.copyfileobj(proc.stdout, gz)
        _, err = proc.communicate()
        if proc.returncode != 0:
            try:
                os.remove(out)
            except OSError:
                pass
            raise RuntimeError(f"{os.path.basename(binary)} exit {proc.returncode}: "
                               f"{err.decode('utf-8', 'replace').strip()}")
    except FileNotFoundError as e:
        raise RuntimeError(f"backup tool missing: {e}")

    size = os.path.getsize(out)
    app.logger.info(f"[backup] wrote {out} ({size:,} bytes)")
    return out


def backup_before_destructive(flask_app=None, *, label: str = "auto_migrate") -> str | None:
    """Best-effort pre-destructive backup. Logs and returns None on failure
    so the caller can decide to abort vs proceed."""
    try:
        return run_backup(flask_app, label=label)
    except Exception as e:
        (flask_app or current_app).logger.error(f"[backup] FAILED: {e}")
        return None


def list_backups(flask_app=None) -> list[dict]:
    out = []
    d = _backup_dir(flask_app)
    for name in sorted(os.listdir(d), reverse=True):
        if not name.endswith(".sql.gz"):
            continue
        p = os.path.join(d, name)
        st = os.stat(p)
        out.append({
            "name": name,
            "path": p,
            "size": st.st_size,
            "mtime": datetime.utcfromtimestamp(st.st_mtime),
        })
    return out


def restore_backup(path: str, flask_app=None) -> None:
    """Restore from a .sql.gz dump. DESTRUCTIVE — overwrites current DB."""
    app = flask_app or current_app
    if not os.path.isfile(path):
        raise RuntimeError(f"backup not found: {path}")

    cfg = _parse_db_url(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
    client = shutil.which("mariadb") or shutil.which("mysql")
    if not client:
        raise RuntimeError("Neither mariadb nor mysql client found on PATH")

    cmd = [
        client,
        f"--host={cfg['host']}",
        f"--port={cfg['port']}",
        f"--user={cfg['user']}",
        "--default-character-set=utf8mb4",
        cfg["db"],
    ]
    env = os.environ.copy()
    if cfg["password"]:
        env["MYSQL_PWD"] = cfg["password"]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    with gzip.open(path, "rb") as gz:
        shutil.copyfileobj(gz, proc.stdin)
    proc.stdin.close()
    _, err = proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"{os.path.basename(client)} exit {proc.returncode}: "
                           f"{err.decode('utf-8', 'replace').strip()}")
    app.logger.info(f"[backup] restored from {path}")
