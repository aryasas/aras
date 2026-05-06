from arasCore.lib.core.extensions import db

def upgrade():
    db.session.execute(db.text(
        "ALTER TABLE company ADD COLUMN default_charge_enable TINYINT(1) NOT NULL DEFAULT 0"
    ))
    db.session.commit()
