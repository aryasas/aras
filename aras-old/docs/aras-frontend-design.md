Design system and UI/UX patterns for the Aras Framework. Use when building or refining admin forms, lists, dashboards, and custom Jinja2 templates to ensure a modern, responsive, and "stunning" user experience.Aras Frontend Design Skill
This skill provides guidelines and patterns for building high-quality, "stunning" UI components within the Aras Framework (Flask + Jinja2 + AdminLTE/Bootstrap).
Core Design Principles

"Stunning" UI: Prioritize visual impact. Use depth (shadows), space (generous padding), and interactive feedback (hover states, loading indicators).
Contextual Persistence: Use sticky headers for primary actions in long forms.
Information Hierarchy: Use cards to group related data. Place metadata and activity logs in sidebars where appropriate.
Alive & Interactive: Every action should feel responsive. Use "dirty checks" for forms and spinners for async operations.

Key Components & Patterns
1. Form Layout (Out of the box artisan design)
Use a two-column layout for complex resources:

2. Sticky Action Header
Always provide a sticky header in adm_form.html that contains:

Back Link: fa-arrow-left to return to the list.
Title: Clear, bold resource name.
Primary Actions: "Save" and "Cancel" buttons consistently positioned.

3. Activity Timeline
Transform flat activity logs into a vertical timeline:

Dots: Color-coded by action (green for create, blue for update, red for delete).
Timeago: Use data-ts attributes with relative time formatting.
Change Tracking: Display field-level diffs (Old → New) in a compact <code> block.

4. Inline Child Tables
For one-to-many relationships (e.g., Invoice Lines):

Use the _child_table_content.html partial.
Support Inline Adding/Editing without full page reloads.
Ensure buttons have hover states (Blue for Edit, Red for Delete).

Reusable Macros
Always check templates/_macros.html before writing custom HTML.

render_card(title, actions=[]): Standard container.
render_form_fields(form): Automatic WTForms rendering.
render_button(label, url, icon, style): Consistent button styling.

Workflows
Refactoring a Legacy Form

Analyze: Identify the model fields and child relationships.
Layout: Set up the two-column Bootstrap grid.
Header: Implement the sticky aras-form-header-sticky.
Sidebar: Add the aras-sidebar-sticky with the activity timeline.
Validation: Ensure "dirty checks" and JS helpers for child tables are included.

Creating a New Dashboard Widget

Use render_stat_box for KPIs.
Use clean SVG icons or FontAwesome icons.
Ensure 1:1 aspect ratios or clear grid alignment.
