"""
Migration 004: Company default accounts + group structure + cleanup.

Changes:
- core_company: add is_group, enable_perpetual_inventory, enable_provisional_non_stock,
                acc_* default account FK columns, remove branches relationship
- pos_terminal: drop branch_id
- pos_session: add company_id
- acc_journal_entry: drop journal_id (no longer required)
- acc_sales_invoice / acc_purchase_invoice: drop journal_id
- Drop tables: core_company_branch, acc_default_account, acc_bank_statement,
               acc_bank_statement_line, acc_journal (data removal must be manual/reviewed)
"""


def upgrade(db):
    conn = db.engine.connect()
    dialect = db.engine.dialect.name

    def col_exists(table, col):
        insp = db.inspect(db.engine)
        return col in [c["name"] for c in insp.get_columns(table)]

    def table_exists(table):
        return db.inspect(db.engine).has_table(table)

    # ── core_company: new columns ─────────────────────────────────────────────
    company_cols = {
        "is_group":                      "BOOLEAN NOT NULL DEFAULT FALSE",
        "enable_perpetual_inventory":     "BOOLEAN NOT NULL DEFAULT FALSE",
        "enable_provisional_non_stock":   "BOOLEAN NOT NULL DEFAULT FALSE",
        "acc_bank_default_id":            "BIGINT",
        "acc_cash_default_id":            "BIGINT",
        "acc_receivable_default_id":      "BIGINT",
        "acc_payable_default_id":         "BIGINT",
        "acc_income_default_id":          "BIGINT",
        "acc_cogs_default_id":            "BIGINT",
        "acc_payroll_payable_id":         "BIGINT",
        "acc_payment_discount_id":        "BIGINT",
        "acc_write_off_id":               "BIGINT",
        "acc_unrealized_gain_loss_id":    "BIGINT",
        "acc_round_off_id":               "BIGINT",
        "acc_inventory_default_id":       "BIGINT",
        "acc_stock_received_not_billed_id": "BIGINT",
        "acc_stock_provisional_id":       "BIGINT",
        "acc_stock_adjustment_id":        "BIGINT",
        "acc_expenses_in_valuation_id":   "BIGINT",
    }
    for col, typedef in company_cols.items():
        if not col_exists("core_company", col):
            conn.execute(db.text(f"ALTER TABLE core_company ADD COLUMN {col} {typedef}"))

    # ── pos_session: add company_id ───────────────────────────────────────────
    if not col_exists("pos_session", "company_id"):
        conn.execute(db.text("ALTER TABLE pos_session ADD COLUMN company_id INTEGER"))
        # backfill from terminal
        conn.execute(db.text("""
            UPDATE pos_session s
            SET company_id = (
                SELECT t.company_id FROM pos_terminal t WHERE t.id = s.terminal_id LIMIT 1
            )
        """))

    if dialect != "sqlite":
        def drop_fk_and_col(table, col, fk_target_table):
            """Drop FK constraint then column (MariaDB/MySQL)."""
            if not col_exists(table, col):
                return
            # Find and drop FK constraints referencing fk_target_table
            fks = db.inspect(db.engine).get_foreign_keys(table)
            for fk in fks:
                if fk_target_table in (fk.get("referred_table") or ""):
                    constraint_name = fk.get("name")
                    if constraint_name:
                        conn.execute(db.text(f"ALTER TABLE {table} DROP FOREIGN KEY `{constraint_name}`"))
            conn.execute(db.text(f"ALTER TABLE {table} DROP COLUMN {col}"))

        # pos_terminal: branch_id → core_company_branch
        drop_fk_and_col("pos_terminal", "branch_id", "core_company_branch")
        # pos_terminal: journal_id and opening_journal_id → acc_journal
        if col_exists("pos_terminal", "journal_id") or col_exists("pos_terminal", "opening_journal_id"):
            fks = db.inspect(db.engine).get_foreign_keys("pos_terminal")
            for fk in fks:
                if fk.get("referred_table") == "acc_journal":
                    conn.execute(db.text(f"ALTER TABLE pos_terminal DROP FOREIGN KEY `{fk['name']}`"))
            for col_name in ("journal_id", "opening_journal_id"):
                if col_exists("pos_terminal", col_name):
                    conn.execute(db.text(f"ALTER TABLE pos_terminal DROP COLUMN {col_name}"))

        # acc_journal_entry: journal_id → acc_journal
        drop_fk_and_col("acc_journal_entry", "journal_id", "acc_journal")

        # acc_sales_invoice / acc_purchase_invoice: journal_id → acc_journal
        for tbl in ("acc_sales_invoice", "acc_purchase_invoice"):
            drop_fk_and_col(tbl, "journal_id", "acc_journal")

    conn.commit()
    conn.close()
    print("[migration 004] company defaults + cleanup done.")


def downgrade(db):
    pass  # intentionally irreversible
