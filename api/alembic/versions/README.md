Alembic migration revisions live in this directory.

Create a new revision from `api/` with:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply migrations with:

```bash
python manage.py migrate
```
