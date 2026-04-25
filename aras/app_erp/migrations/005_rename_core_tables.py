"""
Migration 005: Remove 'core_' prefix from table names + rename tax→charge.

Renames:
  core_company            → company
  core_currency           → currency
  core_fx_rate            → fx_rate
  core_fiscal_year        → fiscal_year
  core_fiscal_period      → fiscal_period
  core_sequence           → sequence
  core_setting            → setting
  core_role               → erp_role
  core_permission         → erp_permission
  core_role_permission    → erp_role_permission
  core_user_company       → erp_user_company
  core_attachment         → attachment
  core_print_template     → print_template
  core_print_template_version → print_template_version
  core_audit_log          → audit_log
  core_notification       → notification
  core_email_template     → email_template
  core_tax                → core_charge  (keep core_ prefix — it's a domain object)
  core_tax_group          → core_charge_category (new table, created fresh)
  Drop: core_tax_group, core_tax_group_line

New columns on existing tables:
  acc_sales_invoice:    rename tax_amt → charge_amt
  acc_purchase_invoice: rename tax_amt → charge_amt
  acc_sales_invoice_line:    drop tax_id, tax_amt
  acc_purchase_invoice_line: drop tax_id, tax_amt

New tables:
  core_charge_category
  acc_sales_invoice_charge
  acc_purchase_invoice_charge
"""


def upgrade(db):
    conn = db.engine.connect()
    dialect = db.engine.dialect.name

    def table_exists(t):
        return db.inspect(db.engine).has_table(t)

    def col_exists(t, c):
        if not table_exists(t):
            return False
        return c in [x["name"] for x in db.inspect(db.engine).get_columns(t)]

    # ── Table renames ─────────────────────────────────────────────────────────
    renames = [
        ("core_company",                "company"),
        ("core_currency",               "currency"),
        ("core_fx_rate",                "fx_rate"),
        ("core_fiscal_year",            "fiscal_year"),
        ("core_fiscal_period",          "fiscal_period"),
        ("core_sequence",               "sequence"),
        ("core_setting",                "setting"),
        ("core_role",                   "erp_role"),
        ("core_permission",             "erp_permission"),
        ("core_role_permission",        "erp_role_permission"),
        ("core_user_company",           "erp_user_company"),
        ("core_attachment",             "attachment"),
        ("core_print_template",         "print_template"),
        ("core_print_template_version", "print_template_version"),
        ("core_audit_log",              "audit_log"),
        ("core_notification",           "notification"),
        ("core_email_template",         "email_template"),
        ("core_tax",                    "core_charge"),
    ]

    for old, new in renames:
        if table_exists(old) and not table_exists(new):
            conn.execute(db.text(f"RENAME TABLE `{old}` TO `{new}`"))
            print(f"  renamed {old} → {new}")

    # ── Create core_charge_category ───────────────────────────────────────────
    if not table_exists("core_charge_category"):
        conn.execute(db.text("""
            CREATE TABLE core_charge_category (
                id         INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                code       VARCHAR(20) NOT NULL,
                name       VARCHAR(100) NOT NULL,
                is_active  TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (company_id) REFERENCES company(id)
            )
        """))
        print("  created core_charge_category")

    # ── Add category_id to core_charge ────────────────────────────────────────
    if not col_exists("core_charge", "category_id"):
        conn.execute(db.text(
            "ALTER TABLE core_charge ADD COLUMN category_id INT NULL REFERENCES core_charge_category(id)"
        ))

    # ── Invoice: rename tax_amt → charge_amt ──────────────────────────────────
    for tbl in ("acc_sales_invoice", "acc_purchase_invoice"):
        if col_exists(tbl, "tax_amt") and not col_exists(tbl, "charge_amt"):
            conn.execute(db.text(f"ALTER TABLE {tbl} CHANGE tax_amt charge_amt DECIMAL(18,4) NOT NULL DEFAULT 0"))

    # ── Invoice lines: drop tax_id & tax_amt ──────────────────────────────────
    for tbl in ("acc_sales_invoice_line", "acc_purchase_invoice_line"):
        if dialect != "sqlite":
            fks = db.inspect(db.engine).get_foreign_keys(tbl) if table_exists(tbl) else []
            for fk in fks:
                if fk.get("referred_table") in ("core_tax", "core_charge"):
                    if fk.get("name"):
                        conn.execute(db.text(f"ALTER TABLE {tbl} DROP FOREIGN KEY `{fk['name']}`"))
        for col in ("tax_id", "tax_amt"):
            if col_exists(tbl, col):
                conn.execute(db.text(f"ALTER TABLE {tbl} DROP COLUMN {col}"))

    # ── Journal line: rename tax_id → charge_id ──────────────────────────────
    if col_exists("acc_journal_line", "tax_id") and not col_exists("acc_journal_line", "charge_id"):
        if dialect != "sqlite":
            fks = db.inspect(db.engine).get_foreign_keys("acc_journal_line")
            for fk in fks:
                if fk.get("referred_table") in ("core_tax", "core_charge") and fk.get("name"):
                    conn.execute(db.text(f"ALTER TABLE acc_journal_line DROP FOREIGN KEY `{fk['name']}`"))
        conn.execute(db.text("ALTER TABLE acc_journal_line CHANGE tax_id charge_id INT NULL"))

    # ── Create acc_sales_invoice_charge ───────────────────────────────────────
    if not table_exists("acc_sales_invoice_charge"):
        conn.execute(db.text("""
            CREATE TABLE acc_sales_invoice_charge (
                id         BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                invoice_id BIGINT NOT NULL,
                charge_id  INT NOT NULL,
                sequence   INT NOT NULL DEFAULT 10,
                base_amt   DECIMAL(18,4) NOT NULL DEFAULT 0,
                amount     DECIMAL(18,4) NOT NULL DEFAULT 0,
                account_id BIGINT NULL,
                is_active  TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (invoice_id) REFERENCES acc_sales_invoice(id),
                FOREIGN KEY (charge_id)  REFERENCES core_charge(id)
            )
        """))
        print("  created acc_sales_invoice_charge")

    # ── Create acc_purchase_invoice_charge ────────────────────────────────────
    if not table_exists("acc_purchase_invoice_charge"):
        conn.execute(db.text("""
            CREATE TABLE acc_purchase_invoice_charge (
                id         BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                invoice_id BIGINT NOT NULL,
                charge_id  INT NOT NULL,
                sequence   INT NOT NULL DEFAULT 10,
                base_amt   DECIMAL(18,4) NOT NULL DEFAULT 0,
                amount     DECIMAL(18,4) NOT NULL DEFAULT 0,
                account_id BIGINT NULL,
                is_active  TINYINT(1) NOT NULL DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (invoice_id) REFERENCES acc_purchase_invoice(id),
                FOREIGN KEY (charge_id)  REFERENCES core_charge(id)
            )
        """))
        print("  created acc_purchase_invoice_charge")

    # ── Drop old tax_group tables ─────────────────────────────────────────────
    for tbl in ("core_tax_group_line", "core_tax_group"):
        if table_exists(tbl):
            conn.execute(db.text(f"DROP TABLE `{tbl}`"))
            print(f"  dropped {tbl}")

    conn.commit()
    conn.close()
    print("[migration 005] rename core tables + charge refactor done.")


def downgrade(db):
    pass  # intentionally irreversible
