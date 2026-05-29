# gemini-2-5-flash
from apscheduler.schedulers.background import BackgroundScheduler
from .services.billing import BillingService
from core import Aras
import logging

def billing_job():
    logging.info("Running billing job...")
    db = next(Aras.get_db())
    try:
        BillingService.generate_due_invoices(db)
        BillingService.enforce_overdue(db)
        BillingService.send_dunning_emails(db)
    except Exception as e:
        logging.error(f"Billing job failed: {e}")
    finally:
        db.close()

def setup_cron():
    import os
    if os.getenv("ARAS_CRON_ENABLED") != "1":
        return
        
    scheduler = BackgroundScheduler()
    scheduler.add_job(billing_job, 'cron', hour=2)
    scheduler.start()
    logging.info("SaaS Cron started (daily at 02:00 UTC)")
