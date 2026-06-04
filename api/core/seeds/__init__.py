# claude-opus-4-8
"""Generic seed framework — declarative seeds any app/module can inherit."""
from core.seeds.base import (
    Seed,
    RbacSeed,
    SeriesSeed,
    RowSeed,
    run_app_seeds,
    seed_catalog,
    iter_seed_entries,
    execute_seed_entry,
    parse_data_file,
)

__all__ = [
    "Seed",
    "RbacSeed",
    "SeriesSeed",
    "RowSeed",
    "run_app_seeds",
    "seed_catalog",
    "iter_seed_entries",
    "execute_seed_entry",
    "parse_data_file",
]
