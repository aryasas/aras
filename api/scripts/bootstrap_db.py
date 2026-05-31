# gemini-pro
import sys
import os

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core import Aras
from core.lib.database import engine
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)

def bootstrap():
    logging.info("Discovering apps...")
    Aras.logic.discovery.discover_apps(package_path="apps")
    
    logging.info("Creating all tables via SQLAlchemy metadata...")
    Aras.Base.metadata.create_all(bind=engine)
    
    # Seed plans if control-panel
    if os.getenv("ARAS_ROLE") == "control-panel":
        logging.info("Seeding default plans...")
        with Session(engine) as db:
            from apps.saas.plans import seed_default_plans
            seed_default_plans(db)
            
            # Seed default payment methods
            from apps.saas.models import PaymentMethod
            if not db.query(PaymentMethod).first():
                db.add(PaymentMethod(code="stripe_card", label="Credit/Debit Card", provider_code="stripe", icon="CreditCard", sort_order=1))
                db.commit()
                logging.info("Payment methods seeded.")
                
    logging.info("Bootstrap complete.")

if __name__ == "__main__":
    bootstrap()
