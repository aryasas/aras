# Aras Admin — UI Kit

A pixel-faithful recreation of the Aras admin dashboard, lifted directly from `templates/admin/*`.

Screens wired up in `index.html`:
- **Login** (`/auth/login.html`) — brand lockup centered, Themify icon inputs
- **Dashboard** (`/admin/dashboard.html`) — stat widgets + notes list + posts
- **Users** (`/admin/users.html`) — table with avatars, badges, row actions
- **App Builder** (`/admin/settings.html#panel-apps`) — apps CRUD table
- **Settings** (`/admin/settings.html`) — tab + left-nav layout

Components (`*.jsx`):
- `Chrome.jsx` — Sidebar, TopBar, MenuBar, PageTitleStrip
- `Primitives.jsx` — Card, Button, Badge, Input, Avatar
- `DataTable.jsx` — the canonical admin table
- `DashboardWidgets.jsx` — stat cards with colored left-border
- `LoginCard.jsx` — auth form
