# Aras Progress

## Session: 2026-04-22

### Template Cleanup

**Deleted unused admin templates (14 files):**
- `adm_form_upload.html`, `adm_home.html`, `adm_list.html`, `adm_list_detail.html`, `adm_list_dict.html`, `adm_list_dt.html`, `adm_list_search.html`
- `activities.html`, `edit_profile.html`, `test.html`, `user_popup.html`
- `_menu_app.html`, `_notif_messages.html`, `aras_admin_fields.html`

**Error pages consolidated (5 → 1):**
- Deleted `_page_error.html`, `page_401.html`, `page_403.html`, `page_404.html`, `page_500.html`
- Created single `templates/page_error.html` with `{% if error_code %}` blocks
- Updated `arasCore/lib/error_handler.py` to pass `error_code` variable

**Template generics:**
- Created `templates/admin/_admin_submenu.html` — shared App Manager breadcrumb nav partial
  - Used by `aras_admin_tables.html` (no leaf) and `aras_admin_table_form.html` (with `submenu_title=title`)
  - `aras_admin_columns.html` keeps its own block (has table-switcher slot)
- Merged `adm_group_home.html` into `adm_app_home.html` — discriminated by `back_url` variable
  - `home_service.py` both home views now render `admin/adm_app_home.html`

**CSS cleanup:**
- Moved inline `<style>` block from `aras_admin_columns.html` into `static/admin/assets/css/custom-css.css`
  - Rules: `#relation-options`, `#length-option`, `#select-options` display:none; `.col-settings-section`
