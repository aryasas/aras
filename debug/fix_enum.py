from run import app
from arasCore.lib.core.extensions import db

with app.app_context():
    db.session.execute(db.text("ALTER TABLE acc_sales_invoice MODIFY COLUMN state ENUM('draft', 'submitted', 'posted', 'partial', 'paid', 'cancelled') NOT NULL DEFAULT 'draft'"))
    db.session.execute(db.text("ALTER TABLE acc_purchase_invoice MODIFY COLUMN state ENUM('draft', 'submitted', 'posted', 'partial', 'paid', 'cancelled') NOT NULL DEFAULT 'draft'"))
    db.session.commit()
    print("ENUMs updated successfully.")
