- YOU ARE STRONGLY NOT ALLOW TO USE GIT COMMAND THAT WILL BRING CHANGE. ONLY ALLOW GIT TO READ (git diff atau git log)

- # Aras Framework — Context & Guidelines

Aras is a modular, metadata-driven ERP and Application Framework built with Flask, SQLAlchemy, and MariaDB. It consists of a core engine (`arasCore`) and various application modules (`aras/app_*`).

## 🏗️ Architecture Overview

- **arasCore**: The engine of the framework.
  - **App Manager**: Handles dynamic app installation via YAML/JSON definitions or Python manifests.
  - **Workflow Engine**: Declarative state-machine (DSL) with RBAC-gated transitions and automated actions.
  - **Server Scripting**: Sandboxed Python hooks (before/after CRUD) for deep behavioral customization.
  - **Universal API**: Automatically generates RESTful endpoints with built-in validation and event triggers.
  - **Global Search**: Command-palette style search across all searchable resources.
  - **RBAC & Audit**: Role-Based Access Control and field-level audit logging (tracking old/new values).
  - **Webhooks**: Event-driven outbound notifications with HMAC signatures.
  - **CLI**: Powerful command-line interface under `flask aras`.
- **Apps (`aras/`)**:
  - **app_erp**: A comprehensive ERP suite covering Accounting, CRM, POS, and Stock/Inventory.
  - **app_todo / app_soc**: Example dynamic/social apps.
- **Data Layer**: Uses a custom `ArasModel` (base for all models) and an idempotent migration system.

## 🚀 Key Commands

### Development & Setup
- `pip install -e .`: Install the project in editable mode.
- `flask aras dbca`: Create all tables for core and installed apps.
- `flask aras remigrate`: Full reset (Drop & Recreate + Migrations + Seed).
- `flask aras erp-init`: Seed ERP core data and run ERP-specific migrations.
- `flask aras fix-db`: Attempt to fix model-to-database mismatches (adding missing columns).

### Running & Testing
- `python run.py` or `flask run`: Start the development server (default port 8080).
- `pytest`: Run the standard test suite.
- `flask aras test api`: Test all registered API endpoints.
- `flask aras test url`: Smoke test all non-parameterized GET routes.

## 🛠️ Development Conventions

- **Models**: Inherit from `arasCore.lib.base_model.ArasModel`.
- **Manifests**: Code-based apps are registered via a `manifest.py` file using `AppHelper` to define menu groups, resources, and custom routes.
- **Templates**: 
  - Standardized admin views use `admin/adm_list.html` and `admin/adm_form.html`.
  - Reusable list logic is encapsulated in `admin/_list_partial.html`.
  - **MANDATE**: Never write CSS or JavaScript directly in HTML templates. Always move styles to `static/css/aras_design.css` (or relevant stylesheets) and logic to external `.js` files in `static/js/`.
- **API**: Resources defined in manifests are automatically exposed at `/api/<app_slug>/<resource_name>/`.
- **Migrations**: 
  - Core migrations live in `arasCore/lib/migrations/`.
  - App-specific migrations are often found in `aras/app_*/migrations/` or task scripts like `migrate_task*.py`.

## ⚠️ Known Fixes & Quirks
- **Database Mismatches**: If you encounter "Unknown column" errors, check the model definition vs the physical table. Use `flask aras fix-db` or manual `ALTER TABLE` via the `mysql` client.
- **Template Errors**: Ensure you use `admin/adm_list.html` for generic lists. Avoid non-existent legacy paths like `admin/aras_list.html`.

## 📁 Project Structure (Post-Refactor)

The project has undergone a significant refactor. This is the updated high-level overview of the Aras project structure.

- **`arasCore/`**: The core framework engine. It contains the essential logic for the application, including the application factory, authentication, database management, and administrative interface.
  - **`lib/`**: The core library of the framework. It has been expanded with more specialized modules.
    - `workflow.py` & `workflow_models.py`: Workflow state machine and transition logic.
    - `script_runner.py` & `script_models.py`: Sandboxed execution engine for server-side hooks.
    - `webhook.py` & `webhook_models.py`: Outbound event notification system.
    - `formula.py`: Safe-eval sandbox for computed/formula fields.
    - `validator.py`: Centralized resource validation (regex, uniqueness, constraints).
    - `audit_models.py`: Extended audit trail for field-level change logging.
    - `widget_registry.py`: Registry for dashboard KPI and chart widgets.
    - `app_helper.py`: Defines `AppHelper` for registering code-based applications.
    - `api_handler.py`: Manages the registration of API endpoints.
    - `installer.py`: Handles app installation from definitions.
    - `blueprints.py`: Manages the registration of Flask Blueprints for apps.
    - `base_model.py`: Contains the `ArasModel`, the base for all database models.
    - `schema_migrator.py`: Manages database schema migrations for dynamic apps.
    - `events.py`: A pub/sub event system for decoupled communication.
    - `search.py`: Powers the global search functionality.
    - `utils.py`: General utility functions.
  - **`arasAdmin/`**: The built-in administration application. This has been heavily refactored.
    - `crud_factory.py`: A factory for creating CRUD (Create, Read, Update, Delete) views.
    - `column_factory.py`: A factory for generating table columns.
    - `table_registry.py`: A registry for dynamic tables.
    - `routes/`: The new location for admin routes, split into multiple files.
    - `services.py`: Contains business logic for the admin interface.
    - `models.py`: Defines the database models for the application manager.
  - `auth.py`: Manages user authentication and authorization.
  - `__init__.py`: The application factory `create_app()` is in here.
- **`aras/`**: This directory contains all the pluggable application modules.
  - **`app_*/`**: Each subdirectory represents an application (e.g., `app_erp`, `app_todo`).
    - `manifest.py`: The entry point for a code-based application, where it registers itself with the framework.
    - `migrations/`: App-specific database migrations.
    - `views/`: App-specific view functions.
    - `templates/`: App-specific Jinja2 templates.
- **`templates/`**: Contains global Jinja2 templates for the application.
  - **`admin/`**: Global templates for the administration interface.
- **`static/`**: Contains static assets like CSS, JavaScript, and images.
- **`tests/`**: Contains the test suite for the project.
- **`run.py`**: The main entry point to run the Flask development server.
- **`config.py`**: Contains the application configuration.
- **`requirements.txt`**: Lists the Python dependencies for the project.
- **`GEMINI.md`**: This file, providing context and guidelines for the Aras framework.
- **`docs/`**: Contains additional documentation.

## 🌟 Future Vision & Roadmap (The "Stunning Framework" Epic)

To evolve Aras from a functional ERP framework into a powerful, stunning, and next-generation platform for both users and developers, the following capabilities are prioritized for future implementation:

### 🤖 Native AI Capabilities & Knowledge Base
- **Contextual Knowledge Base:** A built-in, vectorized knowledge base that understands the framework's internal architecture and the user's specific app configurations.
  - *For Users:* Chatbot interface to ask questions like "How do I create a new Sales Invoice workflow?" or "Show me my top 5 customers."
  - *For Devs:* Embedded assistant for "Write a Server Script that sends an email after an invoice is paid," trained directly on Aras `AppHelper` and `SubHandler` patterns.
- **Smart Token Optimization CLI:** Commands like `flask aras ai-context --optimize` that pack the exact relevant codebase files into a compressed string or minimal token footprint for LLMs, effectively reducing context size and saving costs.
- **Auto-Generative Apps:** CLI or UI capability to prompt "Build a simple CRM with Deals and Pipelines" and have the AI instantly generate the `app_install.yaml` or `manifest.py`.

### 🎨 Stunning User Experience (UX) & Extensibility
- **Visual Designers:** 
  - *Visual Workflow Builder:* A drag-and-drop node editor (e.g., using ReactFlow or Mermaid) to define states and transitions for the `Workflow Engine`.
  - *No-Code Form Builder:* Interactive UI to place fields, set up tabs, and configure column breakpoints without writing JSON layouts.
  - *Advanced Dashboard Studio:* Enhanced widget placement, custom charting tools, and dynamic filtering.
- **Modern Design System:** Move toward a highly polished, responsive, and accessible UI theme (e.g., Tailwind CSS / Radix primitives or Bootstrap 5 advanced theming) with dark mode toggle and customizable branding per tenant.
- **Unified Command Palette:** Enhance the existing Global Search (Cmd+K) with actionable commands (e.g., "Create New User", "Clear Cache", "Go to Settings").

### 🛠️ Elite Developer Experience (DX)
- **Advanced CLI Helpers:** 
  - `flask aras scaffold`: Interactive prompts to generate new apps, models, handlers, and migrations.
  - `flask aras verify-db`: Advanced schema inspector to detect drift and automatically generate safe `Alembic`-style `ALTER TABLE` scripts.
- **Embedded IDE for Scripts:** A Monaco or Ace code editor embedded in the Admin UI for Server Scripts and Formulas, providing real-time syntax highlighting, autocomplete, and linting.
- **Automated API Documentation:** Auto-generate interactive Swagger/OpenAPI documentation directly from the Universal API and `validator.py` schemas.

### 🔗 Deep Integrations & Connectivity
- **Authentication & Identity:** Built-in support for SSO (Google, Microsoft, GitHub) and LDAP/Active Directory.
- **Unified Cloud Storage:** Abstraction layer for file attachments to seamlessly switch between local storage, AWS S3, and Google Cloud Storage.
- **Payment & Commerce:** Pre-built, pluggable gateways (Stripe, PayPal) to support subscriptions, invoicing, and POS checkouts natively.
- **Multi-Tenancy:** Native support to run multiple isolated organizations/companies from a single database using global tenant scoping in SQLAlchemy.
