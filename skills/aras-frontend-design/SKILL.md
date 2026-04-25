---
name: aras-frontend-design
description: Design system and UI/UX patterns for the Aras Framework. Use when building or refining admin forms, lists, dashboards, and custom Jinja2 templates to ensure a modern, responsive, and "stunning" user experience.
---

# Aras Frontend Design Skill

This skill provides guidelines and patterns for building high-quality, "stunning" UI components within the Aras Framework (Flask + Jinja2 + AdminLTE/Bootstrap).

## Core Design Principles

1.  **"Stunning" UI**: Prioritize visual impact. Use depth (shadows), space (generous padding), and interactive feedback (hover states, loading indicators).
2.  **Contextual Persistence**: Use sticky headers for primary actions in long forms.
3.  **Information Hierarchy**: Use cards to group related data. Place metadata and activity logs in sidebars where appropriate.
4.  **Alive & Interactive**: Every action should feel responsive. Use "dirty checks" for forms and spinners for async operations.

## Key Components & Patterns

### 1. Form Layout (Stunning Redesign)
Use a two-column layout for complex resources:
- **Left (Col-8)**: Main data entry fields grouped by `render_form_fields`.
- **Right (Col-4)**: Metadata, Status badges, and the **Activity Timeline**.

### 2. Sticky Action Header
Always provide a sticky header in `adm_form.html` that contains:
- **Back Link**: `fa-arrow-left` to return to the list.
- **Title**: Clear, bold resource name.
- **Primary Actions**: "Save" and "Cancel" buttons consistently positioned.

### 3. Activity Timeline
Transform flat activity logs into a vertical timeline:
- **Dots**: Color-coded by action (green for `create`, blue for `update`, red for `delete`).
- **Timeago**: Use `data-ts` attributes with relative time formatting.
- **Change Tracking**: Display field-level diffs (Old → New) in a compact `<code>` block.

### 4. Inline Child Tables
For one-to-many relationships (e.g., Invoice Lines):
- Use the `_child_table_content.html` partial.
- Support **Inline Adding/Editing** without full page reloads.
- Ensure buttons have hover states (Blue for Edit, Red for Delete).

## Reusable Macros
Always check `templates/_macros.html` before writing custom HTML.
- `render_card(title, actions=[])`: Standard container.
- `render_form_fields(form)`: Automatic WTForms rendering.
- `render_button(label, url, icon, style)`: Consistent button styling.

## Workflows

### Refactoring a Legacy Form
1.  **Analyze**: Identify the model fields and child relationships.
2.  **Layout**: Set up the two-column Bootstrap grid.
3.  **Header**: Implement the sticky `aras-form-header-sticky`.
4.  **Sidebar**: Add the `aras-sidebar-sticky` with the activity timeline.
5.  **Validation**: Ensure "dirty checks" and JS helpers for child tables are included.

### Creating a New Dashboard Widget
1.  Use `render_stat_box` for KPIs.
2.  Use clean SVG icons or FontAwesome icons.
3.  Ensure 1:1 aspect ratios or clear grid alignment.
