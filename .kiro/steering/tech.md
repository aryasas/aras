# Tech Stack

## Language & Runtime
- Python 3.x

## Core Frameworks & Libraries
- **Flask** — Web framework, Blueprints for routing
- **SQLAlchemy** — ORM (via Flask-SQLAlchemy)
- **WTForms + WTForms-Alchemy** — Form generation and validation
- **Marshmallow** — Serialization/deserialization
- **Flask-Login** — Authentication sessions
- **Jinja2** — Server-side HTML templating
- **Huey / RQ** — Background task queues
- **Flask-Caching** — Response and data caching
- **pytest** — Test framework

## Frontend
- Bootstrap CSS (via Jinja2 templates)
- jQuery
- All custom styles go in `static/css/aras_design.css` — never inline
- All custom JS goes in `static/js/` — never inline in templates

## Database
- MariaDB (primary)
- Connection configured via `SQLALCHEMY_DATABASE_URI` in `.env`

## Configuration
- Environment set via `ARAS_CONFIG` (`development` / `testing` / `production`)
- Config classes defined in `config.py`
- Dev server runs on port 8080

## Common Commands

### Development
```bash
python run.py          # Start dev server (port 8080)
flask run              # Alternative start
```

### Database
```bash
flask aras dbca        # Create all tables
flask aras remigrate   # Full reset: drop + recreate + run migrations + seed
flask aras erp-init    # Seed ERP reference data
```

### Testing
```bash
pytest                 # Run full test suite
flask aras test api    # Test all auto-generated API endpoints
flask aras test url    # Smoke test all GET routes
```

### App Management
```bash
flask aras install <app>   # Install an app from YAML/JSON definition
flask aras uninstall <app> # Uninstall an app
```
