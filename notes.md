arasCore/arasAdmin/models.py line 375, 486, 507, 529, 557, 600             
arasCore/arasAdmin/services.py line 282, 308, 351                          
arasCore/auth.py line 17                                                   
arasCore/lib/installer.py line 446                                         
arasCore/lib/label_utils.py line 45                                        
arasCore/permissions.py line 12, 26, 64                                    
still use db.model. inherit all model from ArasModel                                             
                                                                                                  
then:                                                                                           
                                                                                                  
(this is made before continuing work after terminated) recheck the line number:
  
Refactor arasCore/arasAdmin/services.py — split into focused modules. Do not change any logic, signatures, or behavior.
Read only these sections of services.py, nothing else:

Lines 1–70 (imports, _SYSTEM_COLS, _slug_from_url, _make_sa_column)
Lines 71–147 (_make_wtf_field)
Lines 149–293 (_table_registry, apply_search_and_filters, _invoke_hooks, sync_table_columns, clear_cache)
Lines 295–414 (make_table_model, make_table_form, get_view_columns)
Lines 416–543 (_build_raw_menu, build_sidebar_menu, _filter_menu_for_user)
Lines 548–703 (_register_built_app)
Lines 706–1197 (_register_table_routes and all inner make_adm_*, make_web_* factories)
Lines 1200–1496 (_detect_parent_fk, _get_child_tables_for_model, _get_inline_columns, _load_activity_log, _populate_relation_choices, load_all_built_apps, get_dashboard_widgets)

Create these files in the same directory, writing only the moved symbols:

column_factory.py — _make_sa_column, _make_wtf_field
crud_factory.py — all make_adm_*, make_web_*, _populate_relation_choices, _invoke_hooks, _load_activity_log
table_registry.py — _table_registry, make_table_model, make_table_form, get_view_columns, sync_table_columns, clear_cache
menu_service.py — _build_raw_menu, build_sidebar_menu, _filter_menu_for_user

Then update services.py: replace moved code with imports from the new files. Do not re-read services.py for this step — use what is already in context.
Finally, search only for these two import patterns across the codebase — do not read any full files:

from arasCore.arasAdmin.services import
from .services import

Fix any broken imports found. Stop after that.
  
  