# Aras Database Specs

## Engine
- MariaDB / MySQL via SQLAlchemy.
- Config classes live in `config.py`.

## Environments
- Dev: `arasdev`
- Test: `arastest`
- Prod: `aras`

## Core Utilities (`aras/lib/db.py`)
- Standard SQLAlchemy `db.session` management.
- Base model class definitions.
- `SearchableMixin`: Used for adding full-text search capabilities to models.

## Dynamic Tables
When `aras/app_manager/factory.py` generates a model at runtime using `type()`, it dynamically binds it to SQLAlchemy's metadata. 
- Ensure `dbca` is run or metadata is refreshed when creating new dynamic tables so SQLAlchemy recognizes them before queries are executed.
