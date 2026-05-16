Plan: Production-Readiness untuk Aras ERP                                                                

 Context

 Audit menyeluruh proyek /Users/aras/Dev/aras (Flask ERP framework) menemukan banyak isu yang harus
 diselesaikan sebelum deploy production. Plan ini mengelompokkan perbaikan ke dalam fase prioritas —
 CRITICAL dulu (blocker keamanan & data), lalu HIGH (deployment & integritas), terakhir MEDIUM (operasional
  & dokumentasi).

 Tujuan: aplikasi bisa di-deploy ke server production dengan aman, tanpa kebocoran kredensial, tanpa risiko
  kehilangan data, dengan observability dan recovery yang layak.

 ---
 FASE 1 — CRITICAL (Blocker, harus selesai dulu)

 1.1 Hapus & rotasi kredensial yang bocor di repo

 - File ke-purge dari working tree dan git history (pakai git filter-repo):
   - .env (DB password root:999999, mail password Aa999999)
   - cookie.txt (session cookie)
   - claudefraud.txt, hist.txt, raw_prompt.txt, routes.txt, notes.md
   - check_users.py, create_test_user.py, run_test_add*.py (7 file)
   - child_row.png, resize_columns.py
 - Tambahkan ke .gitignore: .env, *.txt, cookie.*, instance/, run_test_*.py
 - Rotasi semua kredensial yang sudah bocor (DB password, mail password, SECRET_KEY)
 - File dipengaruhi: .gitignore, hapus file-file di atas

 1.2 Fix config.py — secrets, CSRF, environment split

 - config.py:17 — hapus fallback SECRET_KEY="hard to guess string". Wajib dari env, raise error jika
 kosong.
 - config.py:26 — set CSRF_ENABLED = True (saat ini False, padahal WTF_CSRF_ENABLED=True — konflik).
 - config.py:30 — hapus SQLALCHEMY_COMMIT_ON_TEARDOWN = True (deprecated, risiko transaksi).
 - config.py:104-105 — RBAC_ENABLED = False di Dev — biarkan, tapi pastikan ProductionConfig.RBAC_ENABLED =
  True.
 - config.py:125 — ProductionConfig saat ini menunjuk ke ARAS_DATABASE_URI_DEV — ganti ke
 ARAS_DATABASE_URI_PROD.
 - Tambah validasi startup: jika FLASK_ENV=production dan SECRET_KEY masih default → raise.
 - File dipengaruhi: config.py, arasCore/__init__.py (startup check)

 1.3 Fix run.py & Dockerfile — bukan dev server di production

 - run.py:22-24 — hapus debug=True, use_debugger=True hardcoded. Pakai os.getenv("FLASK_DEBUG").
 - Dockerfile:33-34 — duplikat CMD; ganti ke gunicorn:
 CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
 - Commit gunicorn.conf.py (sudah ada generator di arasCore/lib/core/server_config.py — render hasilnya).
 - Tambah non-root user di Dockerfile, healthcheck, MAX_CONTENT_LENGTH.
 - File dipengaruhi: run.py, Dockerfile, gunicorn.conf.py (baru)

 1.4 Fix docker-compose.yml — secrets via env

 - Hapus hardcoded DB_PASSWORD: "999999", SECRET_KEY: your_secret_key_here.
 - Pakai ${VAR} saja, dokumentasi .env.example (tanpa nilai asli).
 - File dipengaruhi: docker-compose.yml, .env.example (baru)

 1.5 SQL injection — table_registry & home_service

 - arasCore/admin/table_registry.py:144,153 — table name di-f-string ke DESCRIBE / ALTER TABLE. Tambah
 whitelist (regex ^[a-zA-Z0-9_]+$) sebelum interpolasi.
 - arasCore/admin/home_service.py:103,142 — column/table name di f-string SELECT. Validasi terhadap
 AppManagerColumn/AppManagerTable sebelum eksekusi.
 - File dipengaruhi: arasCore/admin/table_registry.py, arasCore/admin/home_service.py

 1.6 File upload limit & validasi

 - Set MAX_CONTENT_LENGTH = 16 * 1024 * 1024 di config.py (16MB cap default).
 - arasCore/admin/routes/apps.py:641 (apps_install) — tambah MIME check (application/zip) selain ekstensi.
 - File dipengaruhi: config.py, arasCore/admin/routes/apps.py

 1.7 Pin dependencies

 - requirements.txt — pin semua versi (Flask==3.0.3, dst). Hapus Flask-DebugToolbar dari requirement utama,
  pindah ke requirements-dev.txt.
 - File dipengaruhi: requirements.txt, requirements-dev.txt (baru)

 ---
 FASE 2 — HIGH (Integritas data & deployment)

 2.1 DB constraint & transaksi atomik untuk operasi stock

 - aras/erp/erp_stock/posting.py — bungkus posting stock + journal dalam satu transaksi (with
 db.session.begin()), rollback di except.
 - Tambah with_for_update() saat baca stock balance sebelum movement (cegah race condition).
 - Tambahkan FK ON DELETE RESTRICT di migration baru untuk relasi business-critical (movement→item,
 journal→account).
 - File dipengaruhi: aras/erp/erp_stock/posting.py, aras/erp/erp_pos/order_service.py,
 aras/erp/erp_acc/*_service.py, migration baru

 2.2 Audit log untuk business records

 - Pakai AuditLog (sudah ada di aras/erp/erp_core/models/audit.py) di hook before_save / after_save
 ArasModel untuk model finansial: AccSalesInvoice, AccJournalEntry, StockMovementLine, PosOrder.
 - File dipengaruhi: aras/erp/erp_acc/models.py, aras/erp/erp_stock/models.py, aras/erp/erp_pos/models.py

 2.3 Soft delete enforcement

 - Ganti business model di aras/erp/ dari ArasModel → ArasSoftModel untuk: invoice, journal, stock
 movement, order. Sudah ada framework-nya di arasCore/lib/core/base_model.py.
 - File dipengaruhi: aras/erp/erp_acc/models.py, aras/erp/erp_stock/models.py, aras/erp/erp_pos/models.py

 2.4 Health check publik untuk K8s/Docker probe

 - Pindah /admin/_health/ ke /_health tanpa @require_auth. Cek DB ping ringan.
 - File dipengaruhi: arasCore/__init__.py atau arasCore/admin/routes/

 2.5 Rate limiting

 - Tambah Flask-Limiter di arasCore/lib/core/extensions.py. Default 200/minute, login endpoint 5/minute.
 - File dipengaruhi: requirements.txt, arasCore/lib/core/extensions.py, arasCore/auth.py

 2.6 Connection pooling

 - config.py — set SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 10, "pool_recycle": 1800, "pool_pre_ping":
 True}.
 - File dipengaruhi: config.py

 2.7 Restore script — refactor

 - restore.sh (27KB heredoc) — pecah jadi script Python di scripts/restore.py yang baca dari backup file
 (mysqldump output), bukan embed code.
 - File dipengaruhi: restore.sh (hapus), scripts/restore.py (baru)

 2.8 Sentry / error tracking

 - Aktifkan Sentry SDK (sudah ada placeholder di config.py:67-69). Ambil DSN dari env.
 - File dipengaruhi: config.py, arasCore/__init__.py, requirements.txt

 2.9 Graceful shutdown

 - Tambahkan handler SIGTERM di run.py untuk drain request + close DB pool.
 - File dipengaruhi: run.py

 ---
 FASE 3 — MEDIUM (Operasional & dokumentasi)

 3.1 Background job queue

 - Tambah Celery + Redis untuk: cleanup StockValuation kosong, email async, generate report PDF.
 - File dipengaruhi: requirements.txt, arasCore/lib/jobs.py (baru), docker-compose.yml

 3.2 PDF report

 - Pakai WeasyPrint untuk invoice PDF. Tambah view /admin/erp/acc/sales-invoice/<id>/print.
 - File dipengaruhi: requirements.txt, aras/erp/erp_acc/views.py atau setara

 3.3 Alembic untuk schema versioning

 - Setup Flask-Migrate paralel dengan custom mgr_schema_migration (custom tetap untuk dynamic apps; Alembic
  untuk core).
 - File dipengaruhi: migrations/ (baru), arasCore/__init__.py

 3.4 File storage abstraction

 - Abstraksi upload (arasCore/lib/storage.py) dengan backend local & s3. Default local, prod pakai S3 via
 env.
 - File dipengaruhi: arasCore/lib/storage.py (baru), arasCore/admin/routes/settings_modules/server.py

 3.5 README & deployment doc

 - Tulis README.md — overview, setup dev, env var list, deploy steps.
 - Tulis docs/DEPLOYMENT.md — Docker production, gunicorn tuning, nginx config, backup cron.
 - File dipengaruhi: README.md (baru), docs/DEPLOYMENT.md (baru)

 3.6 Hapus dev artifacts dari production image

 - .dockerignore — exclude tests/, docs/, notes/, erpnext-develop/, *.md, instance/.
 - File dipengaruhi: .dockerignore (baru)

 3.7 Logging level produksi

 - config.py:74 — turunkan default ke INFO, structured JSON logging via python-json-logger.
 - File dipengaruhi: config.py, arasCore/__init__.py

 3.8 Test coverage

 - Migrasi custom test runner ke pytest. Tambah CI (.github/workflows/test.yml) yang jalankan pytest --cov.
 - File dipengaruhi: pyproject.toml, .github/workflows/test.yml (baru)

 3.9 Static asset minify

 - Optional — tambah flask-assets atau npm build step untuk minify CSS/JS di static/.
 - File dipengaruhi: package.json (baru) atau arasCore/lib/core/extensions.py

 ---
 Verifikasi (Test Plan)

 Setelah Fase 1:
 1. git log --all -- .env cookie.txt → kosong (sudah purge).
 2. docker compose up dengan .env baru → app start, /_health 200.
 3. python -c "import config; assert config.ProductionConfig.SECRET_KEY != 'hard to guess string'".
 4. Test SQL injection: kirim ?table=users;DROP TABLE ke endpoint terkait → ditolak validasi.
 5. Upload file >16MB → 413 Request Entity Too Large.

 Setelah Fase 2:
 1. Concurrent stock posting test (2 request bersamaan kurangi stock yang sama) → tidak overcommit.
 2. Delete invoice → row tetap ada dengan deleted_at set, audit log entry tertulis.
 3. /_health accessible tanpa login, return 200 + {"db": "ok"}.
 4. Login 6× cepat → request ke-6 ditolak rate limit.
 5. Sentry test event muncul di dashboard.

 Setelah Fase 3:
 1. Trigger cleanup task → masuk Celery queue, eksekusi async.
 2. Print invoice → PDF terdownload, layout sesuai aras_design.css.
 3. flask db upgrade jalan untuk migration core.
 4. Upload ke S3 (env STORAGE_BACKEND=s3) → file di bucket, bukan local disk.

 ---
 File Critical yang akan Disentuh

 - config.py — env split, secrets, CSRF, pool, MAX_CONTENT_LENGTH
 - run.py — hapus debug
 - Dockerfile + docker-compose.yml + .env.example + .dockerignore
 - gunicorn.conf.py (baru)
 - arasCore/__init__.py — startup validation, Sentry, health
 - arasCore/admin/table_registry.py + arasCore/admin/home_service.py — SQLi fix
 - arasCore/admin/routes/apps.py — upload validation
 - arasCore/lib/core/extensions.py — Flask-Limiter
 - arasCore/lib/core/base_model.py — sudah ada ArasSoftModel, hanya perlu adopsi
 - aras/erp/erp_*/ — soft delete + audit log + transaksi atomik
 - requirements.txt + requirements-dev.txt — pin & split

 ---
 Estimasi Effort (rough)

 - Fase 1: 2-3 hari (paling banyak file kecil tapi sensitif)
 - Fase 2: 3-5 hari (touching domain logic)
 - Fase 3: 5-7 hari (infrastruktur baru)

 Total ~2 minggu untuk production-ready penuh.
