# -*- coding: utf-8 -*-
import os
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
from arasCore.lib.extensions import db

meta = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

ArasBase = declarative_base(metadata=meta)


def configure_database(app):
    with app.app_context():
        db.create_all()


def db_init():
    import sys
    import sqlalchemy
    from sqlalchemy_utils import database_exists
    db_uri = os.getenv("DB_URI")
    engine = sqlalchemy.create_engine(db_uri)
    print("Checking database..")
    if database_exists(engine.url):
        print("Database already exist")
        sys.exit()


def db_createall():
    import sys
    import mariadb
    import sqlalchemy
    db_uri = os.getenv("DB_URI")
    engine = sqlalchemy.create_engine(db_uri)
    try:
        ArasBase.metadata.create_all(engine)
    except mariadb.Error as e:
        print(f"Error for MariaDB Platform: {e}")
        print("Database initialize failed")
        sys.exit(1)
    else:
        print("Database initialized")
