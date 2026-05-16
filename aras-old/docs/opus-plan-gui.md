 Plan: GUI Improvement & Framework Dev Tooling                                                           
                                                                                                            
  Context                                                                                                 
                                                                                                            
  Fokus ke GUI — design polish, fitur UX yang masih kurang, plus GUI tooling untuk dev framework-level agar 
  bikin/edit app, table, kolom, layout lebih cepat tanpa edit kode mentah.
                                                                                                            
  Audit GUI menemukan: design system di static/css/aras_design.css sudah solid (palette, typography, utility
   class lengkap). Layout dasar (sidebar, top bar, list, form, child table) sudah jalan. Yang kurang: polish
   UX di form/list, beberapa komponen reusable (datepicker, typeahead, toast, rich editor), dan GUI dev     
  tooling masih basic — bikin app/table sudah ada, tapi visual layout designer, schema viewer, route map, 
  log viewer, masih minim/belum ada.

  ---
  FASE A — GUI Polish (User-Facing)
                                                                                                            
  A.1 Form UX — required indicator, validation feedback, submit state
                                                                                                            
  - templates/admin/base/base_partial_form_fields.html & templates/admin/macro/macro_forms.html:            
    - Tambah asterisk * merah di label saat field required.                                                 
    - Tambah inline validation (HTML5 + CSS :invalid) — border merah saat blur dengan value invalid.        
    - Submit button: tambah class .is-loading + spinner saat form submit (JS handler di                     
  static/js/aras-design.js).                                                                                
  - Help text sudah ada via field.description — pastikan macro reusable konsisten dipakai di semua form.    
                                                                                                            
  A.2 List UX — sortable column, saved view, CSV export                                                     
                                                                                                            
  - templates/admin/macro/macro_tables.html — header <th> jadi link ?sort=col&dir=asc. Tambah icon arrow    
  (▲/▼).                                                                                                  
  - Saved view (AppManagerPageView model sudah ada) — UI dropdown di toolbar untuk pick view + tombol "Save 
  current as view".                                                                                         
  - Tombol export CSV di toolbar — render via endpoint /api/<app>/<resource>/?format=csv.
  - File: templates/admin/gen/gen_view_list_toolbar.html, arasCore/lib/api_handler.py,                      
  arasCore/admin/services.py                                                                                
                                                                                                            
  A.3 Toast notification — ganti flash alert                                                                
                                                                                                          
  - Ganti .alert.alert-{category} di templates/admin/base_index.html:46-56 jadi toast pojok kanan bawah.    
  - Tambah class .aras-toast + .aras-toast-success/error/warning di static/css/aras_design.css.
  - JS auto-dismiss 4s, slide-in animation. Add helper Aras.toast(msg, type) di static/js/aras-design.js.   
                                                                                                            
  A.4 Component library — datepicker, typeahead, rich editor                                                
                                                                                                            
  - Datepicker: Flatpickr (lightweight, no jQuery). Auto-attach ke input[type=date] + custom WTForms field  
  type "date" dari AppManagerColumn.
  - Typeahead/Select2: untuk SelectField FK dengan banyak option — pakai Tom Select (vanilla, modern).      
  Auto-attach ke select.aras-form-select[data-typeahead].                                                   
  - Rich text editor: untuk TextAreaField dengan field_type='richtext' — pakai Quill atau EasyMDE. Optional,
   opt-in via column config.                                                                                
  - File: static/js/aras-design.js, static/css/aras_design.css,                                           
  templates/admin/base/base_partial_form_fields.html                                                        
                                                                                                          
  A.5 Loading skeleton + empty state                                                                        
                                                                                                          
  - Skeleton loader untuk list page (saat AJAX/server delay) — class .aras-skeleton + animation shimmer.    
  - Empty state sudah ada di macro_tables.html — pastikan dipakai konsisten di app home (/admin/<app>/) saat
   belum ada child page.                                                                                    
                                                                                                          
  A.6 Breadcrumb                                                                                            
                                                                                                          
  - CSS .aras-breadcrumb sudah ada tapi konten kosong. Render breadcrumb di templates/admin/base_index.html 
  block dari breadcrumb Jinja variable.
  - Auto-generate dari URL pattern: App > Resource > {Detail}.                                              
                                                                                                            
  A.7 Activity timeline di detail page
                                                                                                            
  - CSS .aras-timeline sudah ada — render timeline dari UserActivity model atau AuditLog (jika sudah        
  diaktifkan).
  - Tampilkan di sidebar kanan form detail (gen_view_form.html).                                            
                                                                                                            
  A.8 Print view                                                                                            
                                                                                                            
  - Tambah print stylesheet static/css/aras_print.css — sembunyikan sidebar/topbar/buttons, fokus konten.   
  - Tombol "Print" di toolbar detail page — JS window.print().                                            
                                                                                                            
  A.9 Dark mode (opsional)                                                                                
                                                                                                            
  - Tambah CSS variable di :root + [data-theme="dark"]. Toggle button di top bar, simpan ke localStorage.   
  - Refactor warna hardcoded di CSS jadi var.
                                                                                                            
  A.10 Accessibility pass                                                                                 
                                                                                                            
  - Tambah :focus-visible outline di semua interactive element (button, link, input).                       
  - ARIA: aria-label di icon-only button, role="dialog" + aria-modal="true" di modal, aria-live="polite" di
  toast region.                                                                                             
  - Skip-to-content link di base_index.html untuk keyboard user.                                          
                                                                                                            
  ---                                                                                                     
  FASE B — Framework Dev GUI (Developer-Facing)                                                             
                                                                                                            
  Tujuan: developer (kita) bisa bikin/edit app, table, kolom, layout tanpa edit kode atau YAML manual. Semua
   via GUI di /admin/.                                                                                      
                                                                                                          
  B.1 Visual Layout Designer (drag & drop tab/section/field)                                                
                                                                                                          
  - Sudah ada placeholder di templates/admin/setting/setting_form_dnd.html. Lengkapi:                       
    - Drag tabs, sections, fields ke posisi baru.                                                         
    - Edit layout_json (lihat arasCore/lib/layout.py) live.                                                 
    - Preview di sebelah kanan — render form pakai layout yang lagi diedit.                                 
  - Save → update AppManagerTable.layout_json.                                                              
  - File: templates/admin/setting/setting_form_dnd.html, static/js/layout-designer.js (baru),               
  arasCore/admin/routes/apps.py (endpoint save)                                                             
                                                                                                            
  B.2 Schema Viewer / ER Diagram                                                                            
                                                                                                          
  - Halaman baru /admin/dev/schema — render ER diagram dari AppManagerTable + AppManagerColumn + FK.        
  - Pakai library: mermaid.js (text-based, simple) atau dagre-d3.
  - Tampilkan: nama tabel, kolom, tipe, FK arrow.                                                           
  - File: templates/admin/setting/setting_schema.html (baru), arasCore/admin/routes/dev.py                  
                                                                                                            
  B.3 Route Map dengan filter & docs                                                                        
                                                                                                            
  - Upgrade /admin/dev (saat ini tabel polos):                                                              
    - Filter by method (GET/POST), prefix (/api/, /admin/), app                                           
    - Group by app/blueprint                                                                                
    - Klik route → modal dengan handler doc, view function source link                                      
  - File: templates/admin/setting/setting_dev.html, arasCore/admin/routes/dev.py                            
                                                                                                            
  B.4 Log Viewer GUI                                                                                        
                                                                                                            
  - Halaman /admin/dev/logs — tail file log (atau in-memory ring buffer) terakhir N baris.                  
  - Filter by level (INFO/WARNING/ERROR), search keyword, auto-refresh tiap 5s.
  - File: templates/admin/setting/setting_logs.html (baru), arasCore/admin/routes/dev.py, ring buffer       
  handler di logging setup                                                                                  
                                                                                                            
  B.5 Migration GUI (improve existing)                                                                      
                                                                                                          
  - /admin/apps/<id>/migrations sudah ada. Tambah:                                                          
    - Diff visual: kolom baru ditandai hijau, hapus merah, type-change kuning.
    - Tombol "Apply Safe" (sudah ada) + "Apply All" (dengan konfirmasi).                                    
    - History migration yang sudah dijalankan.                                                              
  - File: templates/admin/setting/setting_migrations.html                                                   
                                                                                                            
  B.6 App Scaffolder Wizard                                                                                 
                                                                                                            
  - /admin/apps/new saat ini single-form. Ubah jadi wizard 3-step:                                          
    a. App info (name, label, icon, color)
    b. Tables — bisa quick-add multiple table dengan nama & label                                           
    c. Per-table columns — quick add multiple column dengan tipe + required                                 
  - Hasil: langsung jadi app aktif, bisa langsung pakai.                                                    
  - File: templates/admin/setting/setting_app_wizard.html (baru), arasCore/admin/routes/apps.py             
                                                                                                            
  B.7 Field Type Inspector / Component Catalog                                                              
                                                                                                            
  - Halaman /admin/dev/components — galeri semua field type, button variant, card, badge, table, modal,     
  toast.                                                                                                  
  - Berfungsi sebagai live styleguide buat dev — preview + copy-paste markup.                               
  - File: templates/admin/setting/setting_components.html (baru), arasCore/admin/routes/dev.py              
                                                                                                            
  B.8 SQL Console (dev-only, gated)                                                                         
                                                                                                            
  - Halaman /admin/dev/sql — read-only SQL query runner. Hanya SELECT, validasi regex.                      
  - Output: hasil dalam table dengan pagination.                                                          
  - Hanya aktif saat app.debug atau role super-admin.                                                       
  - File: templates/admin/setting/setting_sql_console.html (baru), arasCore/admin/routes/dev.py             
                                                                                                            
  B.9 Manifest ↔ DB Sync GUI                                                                                
                                                                                                            
  - Sudah ada apps_sync per app. Tambah halaman ringkas /admin/dev/sync:                                    
    - List semua app, status sync (DB == manifest? atau drift?)
    - Tombol sync per app + "Sync All".                                                                     
  - File: templates/admin/setting/setting_sync.html (baru), arasCore/admin/routes/dev.py                  
                                                                                                            
  B.10 Theme/Design Token Editor                                                                            
                                                                                                            
  - Halaman /admin/settings/theme — edit CSS variable (color palette, font, radius) via color picker, simpan
   ke DB (AppManagerSetting), inject sebagai CSS variable di base_index.html.                             
  - Live preview di kanan.                                                                                  
  - File: templates/admin/setting/setting_theme.html (baru), arasCore/admin/routes/settings.py              
   
  ---                                                                                                       
  Verifikasi                                                                                              
                                                                                                            
  Fase A
                                                                                                            
  1. Buka form create — field required tampil asterisk merah; submit kosong → error inline.                 
  2. Submit form valid — button jadi spinner, redirect ke list, toast hijau "Saved".
  3. List page — klik header column → reload dengan sort, ada arrow icon.                                   
  4. Dropdown SelectField FK >50 option → pakai Tom Select, bisa search.                                    
  5. prefers-color-scheme: dark atau toggle → tema gelap aktif, palette tetap konsisten.                    
  6. Tab/keyboard navigate — fokus ring kelihatan jelas.                                                    
                                                                                                            
  Fase B                                                                                                    
                                                                                                          
  1. Buka /admin/apps/<id>/tables/<id>/layout → drag field ke section lain → save → reload form, field di   
  posisi baru.
  2. /admin/dev/schema → ER diagram render, FK arrow visible.                                               
  3. /admin/dev/logs → trigger error → log baru muncul tanpa reload manual (auto-refresh).                  
  4. /admin/apps/new wizard → bikin app + 2 table + 5 kolom dalam <2 menit, langsung aktif.                 
  5. /admin/dev/components → semua varian button/badge/card/table tampil dengan markup-nya.                 
  6. Edit theme color → simpan → seluruh admin pakai warna baru tanpa reload deploy.                        
                                                                                                            
  ---                                                                                                     
  File Utama yang Disentuh                                                                                  
                                                                                                          
  CSS / JS
  - static/css/aras_design.css — toast, skeleton, focus-visible, dark mode var
  - static/css/aras_print.css (baru)                                                                        
  - static/js/aras-design.js — toast helper, form spinner, sort handler
  - static/js/layout-designer.js (baru) — drag&drop layout                                                  
  - Vendor libs: flatpickr, tom-select, quill/easymde, mermaid                                              
   
  Template                                                                                                  
  - templates/admin/base_index.html — toast region, breadcrumb block, theme toggle                        
  - templates/admin/base/base_partial_form_fields.html — required, validation, datepicker hook              
  - templates/admin/macro/macro_forms.html, macro_tables.html — sortable header, asterisk                 
  - templates/admin/gen/gen_view_list_toolbar.html — saved view dropdown, export CSV                        
  - templates/admin/gen/gen_view_form.html — activity timeline, print button                                
  - templates/admin/setting/ — file baru: setting_schema.html, setting_logs.html, setting_components.html,  
  setting_sql_console.html, setting_sync.html, setting_theme.html, setting_app_wizard.html                  
                                                                                                            
  Backend                                                                                                 
  - arasCore/admin/routes/dev.py — endpoint baru: schema, logs, components, sql, sync                       
  - arasCore/admin/routes/apps.py — wizard endpoint, layout designer save                                 
  - arasCore/admin/routes/settings.py — theme save/load                  
  - arasCore/lib/api_handler.py — CSV export, sort param                                                    
  - arasCore/lib/layout.py — utility untuk validasi layout_json saat designer save
  - Logging setup — ring buffer handler untuk log viewer                                                    
                                                                                                          
  ---                                                                                                       
  Urutan Implementasi yang Disarankan                                                                     
                                                                                                            
  Quick wins (1-2 hari):                                                                                  
  1. A.1 Form required + validation                                                                         
  2. A.3 Toast (ganti flash alert) 
  3. A.6 Breadcrumb                                                                                         
  4. A.10 Accessibility focus-visible + ARIA                                                              
  5. B.3 Route Map upgrade                                                                                  
   
  Medium (3-5 hari):                                                                                        
  6. A.2 List sort + CSV export                                                                           
  7. A.4 Component library (datepicker + typeahead dulu)                                                    
  8. A.5 Loading skeleton & empty state
  9. B.4 Log Viewer                                                                                         
  10. B.7 Component Catalog                                                                                 
  11. B.5 Migration GUI improve
                                                                                                            
  Heavier (5-7 hari):                                                                                     
  12. A.9 Dark mode
  13. B.1 Visual Layout Designer (paling rumit, tapi paling impactful buat dev)                             
  14. B.2 Schema Viewer ER diagram
  15. B.6 App Scaffolder Wizard                                                                             
  16. B.10 Theme Editor                                                                                     
  17. B.8 SQL Console
  18. A.7 Activity Timeline (perlu Audit Log dulu — depend ke production plan FASE 2.2)                     
                                                                                                            
  Total: 2-3 minggu untuk full coverage. Bisa dipotong ke "quick wins + dev tooling" subset (~1 minggu)     
  untuk impact tercepat.                                                                                    
                                                                                                            
  ---                                                                                                     
  Catatan
         
  - Plan production tersimpan di docs/opus-plan-production.md. A.7 Activity Timeline depend pada Audit Log
  dari plan production fase 2.2.                                                                            
  - Hindari dependency JS berat (jangan React/Vue full framework). Pertahankan stack vanilla + library
  kecil.                                                                                                    
  - Setiap halaman dev tooling harus pakai ResourceDef atau CustomRoute — jangan @app.route langsung.     
  (Aturan framework di CLAUDE.md.)                                                                          
                                                                                                          
  ---                                                                                 


  AUDIT:
  ✦ Berdasarkan audit kode mendalam terhadap file-file inti Aras Framework, berikut adalah hasil verifikasi fitur untuk Fase A dan Fase B:
  
    ✅ Fase A: Verifikasi UI/UX Core
     1. Form Validation: 
         * Asterisk: Terverifikasi di macro_forms.html (logika is-required) dan aras_design.css yang menambahkan content: " *" berwarna oxblood pada label.
         * Error Inline: Terverifikasi di macro_forms.html yang merender span.aras-form-error tepat di bawah field jika terdapat error validasi dari WTForms.
     2. Submission Feedback: 
         * Spinner: Terverifikasi secara global di aras-design.js (initFormLoading) yang menambahkan class .is-loading saat submit, dan aras_design.css yang mengubah button menjadi spinner via pseudo-element ::after.
         * Toast: Terverifikasi fungsi window.Aras.toast() di aras-design.js yang menangani notifikasi sukses/error dengan animasi slide-in.
     3. List Sorting:
         * Logic: Backend di crud_factory.py sudah menangani argumen ?sort= dan ?dir=. 
         * UI: Macro sorting di macro_tables.html menyediakan link interaktif dan icon arrow (fa-sort-asc/desc).
     4. SelectField FK (Tom Select):
         * Implementation: Terverifikasi di aras-design.js menggunakan library TomSelect untuk elemen berkelas .data-typeahead, lengkap dengan fitur search dan dropdown_input.
     5. Dark Mode:
         * Consistency: Terverifikasi di aras_design.css menggunakan variabel :root yang di-override oleh selector [data-theme="dark"]. Palette warna tetap harmonis antara mode terang dan gelap.
     6. Keyboard Navigation:
         * Focus Ring: Terverifikasi di aras_design.css menggunakan :focus-visible dengan outline 2px solid var(--studio-ochre) dan outline-offset: 2px untuk visibilitas tinggi.
  
    ✅ Fase B: Verifikasi Developer Tools & Studio
     1. Layout Builder (Drag & Drop): 
         * Tool: Terverifikasi file static/js/layout-designer.js menggunakan React 18 untuk builder interaktif. Mendukung drag field antar section, pengaturan lebar kolom (1/2 atau Full), dan tab manajemen.
         * Persistence: Tersimpan di kolom layout_json pada tabel mgr_table.
     2. Schema Viewer (ER Diagram):
         * Visual: Terverifikasi di templates/admin/setting/setting_schema.html menggunakan Mermaid.js untuk merender diagram ER dinamis dari metadata aplikasi.
     3. Auto-refresh Logs:
         * Real-time: Terverifikasi di setting_logs.html dengan fitur "Auto Refresh (5s)" yang melakukan polling ke endpoint /admin/api/dev/logs tanpa reload halaman.
     4. App Wizard:
         * Speed: Terverifikasi rute apps_wizard di arasCore/admin/routes/apps.py yang menerima payload JSON untuk membuat App, tabel-tabel, dan kolom-kolom dalam satu transaksi database tunggal.
     5. Component Library:
         * Catalog: Terverifikasi di /admin/dev/components (setting_components.html) yang mendokumentasikan semua elemen UI Aras (badges, buttons, cards, forms, tables) lengkap dengan contoh markup HTML untuk developer.
     6. Live Theme Edit:
         * Dynamic Theme: Terverifikasi rute /settings/theme yang menyimpan desain token ke ArasSystemSetting. Perubahan langsung aktif karena base_partial_head.html menyuntikkan variabel CSS tersebut ke dalam :root di
           setiap request.
  
    Kesimpulan: Infrastruktur Aras Framework telah memenuhi standar yang diminta. Sistem siap digunakan untuk produktivitas tinggi dengan estetika "Studio/Midnight Editorial" yang konsisten.
