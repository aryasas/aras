from celery import Celery
import os
from dotenv import load_dotenv

# Load .env from project root (three levels up from core/lib/)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

# Default to Redis broker URL
REDIS_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "aras_tasks",
    broker=REDIS_BROKER_URL,
    backend=REDIS_BROKER_URL, # Using Redis for result backend as well
    include=['api.core.manager.task_manager'] # Will be created later
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True
)

# Optional: Configuration for development
if os.getenv("APP_ENV") == "development":
    celery_app.conf.update(
        broker_connection_max_retries=10,
        task_always_eager=False, # Set to True for testing tasks synchronously
        worker_redirect_stdouts_level='INFO'
    )
