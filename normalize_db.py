
import os
from sqlalchemy import create_engine, text, inspect
from config import config

uri = os.getenv('SQLALCHEMY_DATABASE_URI') or config['default'].SQLALCHEMY_DATABASE_URI
engine = create_engine(uri)

def fix_table(table_name, column_specs):
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing_cols = {c['name']: c for c in inspector.get_columns(table_name)}
    
    with engine.connect() as conn:
        for col_name, new_type in column_specs.items():
            if col_name in existing_cols:
                curr_type = str(existing_cols[col_name]['type']).upper()
                # Simplified check for integer types
                is_int_match = (curr_type.startswith('INT') or curr_type == 'INTEGER') and (new_type.upper() == 'INTEGER' or new_type.upper() == 'INT')
                if curr_type != new_type.upper() and not is_int_match:
                    print(f"Altering {table_name}.{col_name}: {curr_type} -> {new_type}")
                    try:
                        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                        conn.execute(text(f"ALTER TABLE `{table_name}` MODIFY COLUMN `{col_name}` {new_type}"))
                        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                    except Exception as e:
                        print(f"  Error: {e}")
        conn.commit()

# Fix PKs first without the PRIMARY KEY keyword (since they are already PKs)
fix_table('company', {'id': 'INTEGER AUTO_INCREMENT'})
fix_table('acc_account', {'id': 'BIGINT AUTO_INCREMENT'})
fix_table('acc_journal_entry', {'id': 'BIGINT AUTO_INCREMENT'})

# Fix other columns
fix_table('company', {
    'base_currency_id': 'INTEGER',
    'default_charge_id': 'INTEGER',
    'parent_id': 'INTEGER',
    'acc_bank_default_id': 'BIGINT',
    'acc_cash_default_id': 'BIGINT',
    'acc_receivable_default_id': 'BIGINT',
    'acc_payable_default_id': 'BIGINT',
    'acc_income_default_id': 'BIGINT',
    'acc_cogs_default_id': 'BIGINT',
    'acc_payroll_payable_id': 'BIGINT',
    'acc_payment_discount_id': 'BIGINT',
    'acc_write_off_id': 'BIGINT',
    'acc_unrealized_gain_loss_id': 'BIGINT',
    'acc_round_off_id': 'BIGINT',
    'acc_inventory_default_id': 'BIGINT',
    'acc_stock_received_not_billed_id': 'BIGINT',
    'acc_stock_provisional_id': 'BIGINT',
    'acc_stock_adjustment_id': 'BIGINT',
    'acc_expenses_in_valuation_id': 'BIGINT',
    'acc_tax_output_ppn_id': 'BIGINT',
    'acc_tax_input_ppn_id': 'BIGINT',
    'acc_stock_default_id': 'BIGINT',
})

fix_table('acc_account', {
    'company_id': 'INTEGER',
    'parent_id': 'BIGINT',
    'currency_id': 'INTEGER',
    'charge_id_default': 'INTEGER',
    'account_type': "ENUM('asset_current', 'asset_fixed', 'asset_other', 'liability_current', 'liability_long', 'equity', 'income_operating', 'income_other', 'expense_operating', 'expense_cogs', 'expense_other', 'view')"
})

fix_table('acc_journal_entry', {
    'company_id': 'INTEGER',
    'fiscal_period_id': 'INTEGER',
    'posted_by': 'INTEGER',
    'origin_id': 'BIGINT',
    'state': "ENUM('draft', 'posted', 'cancelled')"
})

print("Normalization phase 2 complete.")
