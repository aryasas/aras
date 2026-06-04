# claude-opus-4-8
"""
Generic declarative seed framework.

An app declares what to seed via a class-level `seeds` list; the framework runs
them generically during bootstrap with zero core->app coupling:

    class AccountingApp(App):
        seeds = [
            RbacSeed("seeds/rbac.yaml"),
            SeriesSeed("seeds/series.yaml"),
            seed_default_accounts,        # a plain callable(db) works too
        ]

Each entry is either:
  * a `Seed` instance (RbacSeed / SeriesSeed / RowSeed / a subclass), or
  * any callable taking (db) — run as-is.

Data files are resolved RELATIVE TO THE DECLARING APP's package directory, so
seed data lives beside the app that owns it (apps/<app>/seeds/...), never in a
loose top-level folder. Framework-tier seeds live under core/ the same way.

To add a new seed *kind*, subclass `Seed` and implement `run(db)`. Anything that
inherits `Seed` is picked up by the generic runner automatically.
"""
from __future__ import annotations

import inspect
import json
import logging
import importlib
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def parse_data_file(path: Union[str, Path]) -> dict:
    """Parse a YAML or JSON seed data file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    if suffix == ".json":
        with open(path) as f:
            return json.load(f)
    raise ValueError(f"Unsupported seed format: {suffix} (use .yaml or .json)")


class Seed:
    """Base class for a declarative seed.

    Subclasses set a relative `path` (resolved against the owning app's dir) and
    implement `run(db)`. The framework injects `owner_dir` before running so the
    path resolves beside whichever app/module declared the seed.
    """

    optional = True
    default_label: Optional[str] = None

    def __init__(
        self,
        path: Optional[str] = None,
        *,
        key: Optional[str] = None,
        label: Optional[str] = None,
        optional: Optional[bool] = None,
    ):
        self.path = path
        self.owner_dir: Optional[Path] = None
        self._key = key
        self._label = label
        if optional is not None:
            self.optional = optional

    def bind(self, owner_dir: Path) -> "Seed":
        """Attach the declaring app's directory so relative paths resolve."""
        self.owner_dir = owner_dir
        return self

    def resolve(self) -> Path:
        if self.path is None:
            raise ValueError(f"{type(self).__name__} has no data path")
        if self.owner_dir is None:
            # Unbound: treat path as already absolute / cwd-relative.
            return Path(self.path)
        return self.owner_dir / self.path

    def run(self, db: Session) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    @property
    def name(self) -> str:
        return f"{type(self).__name__}({self.path})"

    @property
    def key(self) -> str:
        if self._key:
            return self._key
        if self.path:
            return f"{type(self).__name__}:{self.path}"
        return f"{type(self).__module__}.{type(self).__qualname__}"

    @property
    def label(self) -> str:
        if self._label:
            return self._label
        if self.default_label:
            return self.default_label
        if self.path:
            return Path(self.path).stem.replace("_", " ").replace("-", " ").title()
        return type(self).__name__.replace("Seed", "").replace("_", " ").strip() or type(self).__name__


class RbacSeed(Seed):
    """Seed roles + permissions from a YAML/JSON file (idempotent)."""
    optional = False
    default_label = "RBAC"

    # claude-opus-4-8
    def run(self, db: Session) -> None:
        from core.seeds.loader import load_rbac
        load_rbac(self.resolve(), db)


class SeriesSeed(Seed):
    """Seed document numbering series into the core_config.numbering config.

    Data shape:
        series:
          - key: accounting_inflow_invoices   # == model __tablename__
            format: "{prefix}{year}-{next_value:04d}"
    """
    optional = False
    default_label = "Numbering Series"

    # claude-opus-4-8
    def run(self, db: Session) -> None:
        from core.lib.config import config
        data = parse_data_file(self.resolve())
        for s in data.get("series", []):
            key = s["key"]
            fmt = (
                s["format"]
                .replace("{next_value:04d}", "{seq:4}")
                .replace("{next_value:05d}", "{seq:5}")
                .replace("{next_value}", "{seq}")
            )
            config.set(db, f"core_config.numbering.{key}", fmt)
        db.flush()


class RowSeed(Seed):
    """Generic idempotent table-row seeder.

    Data shape:
        model: <import path, e.g. apps.crm.models.LeadStage>   # or pass model=
        match: [field, ...]    # fields that identify an existing row
        rows:
          - {field: value, ...}

    A row is inserted only if no existing row matches on `match` fields.
    """

    def __init__(self, path: Optional[str] = None, model: Any = None,
                 match: Optional[list] = None):
        super().__init__(path)
        self._model = model
        self._match = match

    # claude-opus-4-8
    def run(self, db: Session) -> None:
        data = parse_data_file(self.resolve()) if self.path else {}
        model = self._model or _import_attr(data["model"])
        match_fields = self._match or data.get("match", [])
        rows = data.get("rows", []) if self.path else []
        for row in rows:
            q = db.query(model)
            for f in match_fields:
                q = q.filter(getattr(model, f) == row.get(f))
            if match_fields and q.first():
                continue
            db.add(model(**row))
        db.flush()


def _import_attr(dotted: str):
    module_path, attr = dotted.rsplit(".", 1)
    return getattr(importlib.import_module(module_path), attr)


def _entry_owner_dir(app_cls) -> Optional[Path]:
    try:
        return Path(inspect.getfile(app_cls)).resolve().parent
    except (TypeError, OSError):
        return None


def _callable_key(entry: Any) -> str:
    return getattr(entry, "key", None) or f"{entry.__module__}.{getattr(entry, '__qualname__', entry.__name__)}"


def _callable_label(entry: Any) -> str:
    label = getattr(entry, "label", None)
    if label:
        return str(label)
    return getattr(entry, "__name__", "Seed").replace("_", " ").replace("-", " ").title()


def _catalog_key(app_cls, entry: Any) -> str:
    local_key = entry.key if isinstance(entry, Seed) else _callable_key(entry)
    return f"{app_cls.app_name}:{local_key}"


# claude-opus-4-8
def _rbac_entry_for_app(app_cls) -> Optional[dict[str, Any]]:
    owner_dir = _entry_owner_dir(app_cls)
    rbac_rel_path = getattr(app_cls, "rbac_file", None)
    if owner_dir is None or not rbac_rel_path:
        return None
    rbac_path = owner_dir / rbac_rel_path
    if not rbac_path.exists():
        return None
    return {
        "app_cls": app_cls,
        "app_name": getattr(app_cls, "app_name", app_cls.__name__),
        "app_label": getattr(app_cls, "app_label", getattr(app_cls, "app_name", app_cls.__name__)),
        "entry": RbacSeed(rbac_rel_path, key="rbac", label="RBAC", optional=False),
        "owner_dir": owner_dir,
        "key": f"{app_cls.app_name}:rbac",
        "label": "RBAC",
        "optional": False,
    }


# claude-opus-4-8
def _demo_seed_entry() -> dict[str, Any]:
    demo_seed = _import_attr("seeds.demo.run_seed")
    return {
        "app_cls": None,
        "app_name": "(sample data)",
        "app_label": "(sample data)",
        "entry": demo_seed,
        "owner_dir": None,
        "key": "demo:all",
        "label": "Demo / Sample Data",
        "optional": True,
    }


def iter_seed_entries(app_cls) -> list[dict[str, Any]]:
    entries = getattr(app_cls, "seeds", None) or []
    owner_dir = _entry_owner_dir(app_cls)
    catalog: list[dict[str, Any]] = []

    for entry in entries:
        if not isinstance(entry, Seed) and not callable(entry):
            logger.warning("Unknown seed entry %r on %s", entry, app_cls.__name__)
            continue
        catalog.append(
            {
                "app_cls": app_cls,
                "app_name": getattr(app_cls, "app_name", app_cls.__name__),
                "app_label": getattr(app_cls, "app_label", getattr(app_cls, "app_name", app_cls.__name__)),
                "entry": entry,
                "owner_dir": owner_dir,
                "key": _catalog_key(app_cls, entry),
                "label": entry.label if isinstance(entry, Seed) else _callable_label(entry),
                "optional": bool(getattr(entry, "optional", True)),
            }
        )
    rbac_entry = _rbac_entry_for_app(app_cls)
    if rbac_entry:
        catalog.append(rbac_entry)
    return catalog


def seed_catalog() -> list[dict[str, Any]]:
    from core.manager.install_order import resolve_install_order

    grouped: list[dict[str, Any]] = []
    for app_cls in resolve_install_order():
        seeds = [
            {
                "key": item["key"],
                "label": item["label"],
                "optional": item["optional"],
                "app_name": item["app_name"],
            }
            for item in iter_seed_entries(app_cls)
        ]
        if not seeds:
            continue
        grouped.append(
            {
                "app_name": app_cls.app_name,
                "app_label": getattr(app_cls, "app_label", app_cls.app_name),
                "seeds": seeds,
            }
        )
    demo_entry = _demo_seed_entry()
    grouped.append(
        {
            "app_name": demo_entry["app_name"],
            "app_label": demo_entry["app_label"],
            "seeds": [
                {
                    "key": demo_entry["key"],
                    "label": demo_entry["label"],
                    "optional": demo_entry["optional"],
                    "app_name": demo_entry["app_name"],
                }
            ],
        }
    )
    return grouped


def execute_seed_entry(entry_info: dict[str, Any], db: Session, org_id: Optional[int] = None) -> None:
    entry = entry_info["entry"]
    owner_dir = entry_info["owner_dir"]
    if isinstance(entry, Seed):
        if owner_dir is not None:
            entry.bind(owner_dir)
        entry.run(db)
        return
    params = inspect.signature(entry).parameters
    if len(params) >= 2:
        if org_id is None:
            raise ValueError(f"Seed '{entry_info['key']}' requires org_id.")
        entry(db, org_id)
        return
    entry(db)


# claude-opus-4-8
def run_app_seeds(app_cls, db: Session) -> None:
    """Run every declarative seed entry defined on an app."""
    entries = iter_seed_entries(app_cls)
    if not entries:
        return

    for entry_info in entries:
        label = entry_info["label"]
        try:
            execute_seed_entry(entry_info, db)
            db.flush()
        except Exception as exc:
            db.rollback()
            logger.error("Seed %s failed for %s: %s", label,
                         getattr(app_cls, "app_name", app_cls.__name__), exc)
