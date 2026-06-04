# claude-opus-4-8
"""
Guards for the generic declarative seed framework (core/seeds/base.py).

The framework runs each app's `seeds` list generically with zero core->app
coupling. These tests pin the contract: path resolution beside the owning app,
the three built-in seed kinds, and graceful handling of plain callables.
"""
import json

from core.seeds import SeriesSeed, RowSeed, Seed, run_app_seeds


# claude-opus-4-8
def test_seed_path_resolves_against_owner_dir(tmp_path):
    s = SeriesSeed("seeds/series.yaml")
    assert s.owner_dir is None
    s.bind(tmp_path)
    assert s.resolve() == tmp_path / "seeds" / "series.yaml"


# claude-opus-4-8
def test_seriesseed_writes_numbering_config(db, tmp_path):
    data_dir = tmp_path / "seeds"
    data_dir.mkdir()
    (data_dir / "series.yaml").write_text(
        "series:\n"
        "  - key: test_doc\n"
        "    format: \"X-{next_value:04d}\"\n"
    )
    SeriesSeed("seeds/series.yaml").bind(tmp_path).run(db)
    db.flush()

    from core.lib.config import config
    val = config.get(db, "core_config.numbering.test_doc")
    assert val == "X-{seq:4}"  # token transformed by the generic loader


# claude-opus-4-8
def test_run_app_seeds_handles_callables_and_seed_instances(db):
    calls = []

    class _Probe(Seed):
        def run(self, db):
            calls.append("seed_instance")

    def _callable(db):
        calls.append("callable")

    class _FakeApp:
        app_name = "fake"
        seeds = [_Probe(), _callable]

    run_app_seeds(_FakeApp, db)
    assert calls == ["seed_instance", "callable"]


# claude-opus-4-8
def test_run_app_seeds_isolates_failures(db):
    ran = []

    def _boom(db):
        raise RuntimeError("intentional")

    def _after(db):
        ran.append("after")

    class _FakeApp:
        app_name = "fake"
        seeds = [_boom, _after]

    # _boom raises but must not prevent _after from running.
    run_app_seeds(_FakeApp, db)
    assert ran == ["after"]


# claude-opus-4-8
def test_rowseed_is_idempotent(db, tmp_path):
    from core.registry.role import Role

    (tmp_path / "data.json").write_text(json.dumps({
        "model": "core.registry.role.Role",
        "match": ["name"],
        "rows": [{"name": "__seed_probe_role__", "description": "x"}],
    }))
    seed = RowSeed("data.json")
    seed.bind(tmp_path).run(db)
    db.flush()
    seed.bind(tmp_path).run(db)  # second run must not duplicate
    db.flush()

    n = db.query(Role).filter(Role.name == "__seed_probe_role__").count()
    assert n == 1
