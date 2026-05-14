# Aras Framework Features

This document outlines the key features and architectural components of the Aras framework, including the recent **Aras Pro** enhancements.

## Core Architecture

-   **Metadata-driven Design:** Built on FastAPI and SQLAlchemy, enabling dynamic behavior and low-code extensibility through metadata.
-   **Hierarchical Structure:** A strict 3-level hierarchy ensures modularity and clear separation of concerns.
-   **Tiered Core Logic:** Prevents circular dependencies by organizing the core into Tiers (0: Utilities, 1: Logic, 2: API).

## Application Lifecycle Management

-   **`manage.py` CLI:** A central command-line interface for managing applications.
    -   `sync`: Synchronizes code-defined metadata to the DB registry and migrates the schema.
    -   `install <file>`, `uninstall <name>`, `activate`, `deactivate`, `discover`, `check`.

## Key Features & Capabilities

### Data & API Layer

-   **Generic CRUD Operations:** Automated generation of FastAPI endpoints via `RouterFactory`.
-   **Enhanced Querying:** Pagination, advanced filtering, and global search.
-   **Global Search & Command Center (Aras Pro):**
    -   **`CommandPalette`:** Integrated `CMD+K` interface for instant access to records, apps, and actions.
    -   **Robust Multi-Resource Search:** The `/search` API uses heuristic type detection and supports `__searchable_fields__` for fine-grained control.
    -   **Intelligent Labeling:** Automatically resolves display labels (username, number, title) for search results.
-   **Computed Properties (Aras Pro):** 
    -   **`@Aras.computed_field` Decorator:** Allows defining dynamic, read-only fields on models that are automatically serialized in API responses.
    -   **Serialization Flexibility:** Computed fields are seamlessly integrated into `to_dict()` and UI metadata.
-   **Advanced Relationship Management (Aras Pro):**
    -   **Many-to-Many (M2M) Support:** Automated M2M handling via `__m2m__` attribute, supporting bridge table synchronization and association management.
    -   **MultiSelect UI:** Dedicated `MultiSelectCombobox` for managing M2M relationships in the UI.
-   **Advanced Import Mapping (Aras Pro):**
    -   **Field Mapping UI:** Users can now map CSV columns to specific resource fields during the import process.
    -   **Background Processing:** Imports are handled via Celery for zero-latency user experience.
-   **Permissions & RBAC:** Integrated Role-Based Access Control.
-   **Auto-Migration:** Automatic database schema updates based on models.

### UI & Presentation Layer (Aras Pro Upgrades)

-   **Dynamic Analytics & Dashboard (Aras Pro):**
    -   **Pluggable Dashboard Widgets:** Support for Stat, List, and Chart widgets.
    -   **Interactive Data Visualization:** Built-in SVG-based charting engine supporting Bar and Pie charts with zero external dependencies.
    -   **Real-time Aggregation:** Widgets automatically fetch and group data from resources.
-   **Pro Layout Engine:**
    -   **Sections & Tabs:** Models can define `__layout__` to group fields into logical sections in the UI.
    -   **Dynamic Rendering:** `DynamicForm` automatically renders these layouts, reducing scroll fatigue.
-   **Advanced Conditional UI Visibility (Aras Pro):**
    -   **Safe `LogicEvaluator`:** A secure, recursive-descent logic engine for evaluating field dependencies (e.g., `total_amount > 5000 && status != 'Draft'`).
    -   **No-Eval Security:** Avoids unsafe JS execution, ensuring system stability.
-   **Pluggable UI Registry:**
    -   **`SchemaRegistry`:** A global registry for field components. Developers can easily register custom widgets (e.g., Color Pickers, Maps) without modifying core components.
-   **Real-time Validation:** Automated mapping of backend Pydantic errors (422) to UI field-level feedback.

### System & Extensibility

-   **Custom Model Actions Framework:**
    -   **`@Aras.model_action` Decorator:** Declarative business logic methods exposed as API endpoints.
    -   **UI Integration:** Actions appear as "Quick Action" (Zap icon) buttons in form headers.
-   **Centralized Background Task Processor:** Celery-powered task queue via `TaskManager`.
-   **Workflow Engine:** State-machine engine for document lifecycles.
-   **Advanced Logging and Monitoring:** Structured JSON logging and global exception handling.
