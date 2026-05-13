from ..base.aras import Aras
from ..manager.manager import Manager
from ..lib.task_queue import celery_app
from typing import Dict, Any

class TaskManager(Manager):
    """
    Manages background tasks using Celery.
    Provides methods to enqueue tasks and retrieve their status.
    """

    @classmethod
    def enqueue_task(cls, task_name: str, *args, **kwargs) -> str:
        """
        Enqueues a background task.
        :param task_name: The name of the task function (e.g., 'task_manager.example_task').
        :param args: Positional arguments for the task.
        :param kwargs: Keyword arguments for the task.
        :return: The ID of the enqueued task.
        """
        # Ensure the task name is fully qualified if it's not local to this module
        if '.' not in task_name and not task_name.startswith('api.core.manager.task_manager.'):
            task_name = f'api.core.manager.task_manager.{task_name}'
            
        task = celery_app.send_task(task_name, args=args, kwargs=kwargs)
        return task.id

    @classmethod
    def get_task_status(cls, task_id: str) -> Dict[str, Any]:
        """
        Retrieves the status of a background task.
        """
        task = celery_app.AsyncResult(task_id)
        return {
            "task_id": task.id,
            "status": task.status,
            "result": task.result if task.ready() else None,
            "successful": task.successful(),
            "failed": task.failed()
        }

    @celery_app.task(name='task_manager.example_task')
    def example_task(x: int, y: int) -> int:
        """An example background task that adds two numbers."""
        import time
        time.sleep(5) # Simulate long-running task
        return x + y

    @celery_app.task(name='task_manager.import_csv_task')
    def import_csv_task(model_class_name: str, data: list, user_id: int) -> Dict[str, Any]:
        """
        Background task to import CSV data.
        This is a placeholder and would interact with the Model.create method.
        """
        from ..base.model import Model
        from ..lib.database import SessionLocal # Need a new DB session for the worker
        
        imported_count = 0
        errors = []
        
        # Re-initialize DB session for the worker process
        db = SessionLocal()
        try:
            # Dynamically get model class (assuming it's in Model._registry)
            model_class = Model._registry.get(model_class_name)
            if not model_class:
                raise ValueError(f"Model '{model_class_name}' not found.")

            for i, row in enumerate(data):
                try:
                    # Basic cleaning: convert empty strings to None for nullable columns
                    for key, val in row.items():
                        if val == "": row[key] = None
                    
                    model_class.create(db, row, user_id=user_id)
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Row {i+1}: {str(e)}")
            
            db.commit() # Commit all changes
            return {"status": "success", "imported_count": imported_count, "errors": errors}
        except Exception as e:
            db.rollback()
            return {"status": "failed", "error": str(e), "imported_count": imported_count, "errors": errors}
        finally:
            db.close()
