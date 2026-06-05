# gemini-2-5-flash
import logging

# gpt-5
def billing_job():
    from .services.billing import BillingService
    from core import Aras

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

# gpt-5
def setup_cron():
    from core.registry.job_runner import start_jobs

    start_jobs()
