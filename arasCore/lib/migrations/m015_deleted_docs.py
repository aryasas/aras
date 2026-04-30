"""
arasCore/lib/migrations/m015_deleted_docs.py
Create aras_deleted_doc table for deletion backup/restore.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import inspect

        insp = inspect(db.engine)
        if "aras_deleted_doc" not in insp.get_table_names():
            from arasCore.lib.models.deletion_models import DeletedDoc
            DeletedDoc.__table__.create(db.engine, checkfirst=True)
            logger.info("[m015] aras_deleted_doc table created")
        else:
            logger.info("[m015] aras_deleted_doc already exists, skip")
