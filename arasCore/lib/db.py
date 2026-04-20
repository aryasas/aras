import os
import sys
import sqlalchemy
import mariadb
from datetime import datetime, timezone
from flask import jsonify, json, url_for
from flask_login import current_user
from sqlalchemy import orm, cast, String, inspect
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy_utils import database_exists

from flask import current_app
from arasCore.lib.extensions import db, ma
from arasCore.lib.db_helper import Serializer, DbHelper, meta


def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {field: getattr(model, field) for field in model.__searchable__}
    current_app.elasticsearch.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index,
        body={"query": {"multi_match": {"query": query, "fields": ["*"]}},
              "from": (page - 1) * per_page, "size": per_page},
    )
    ids = [int(hit["_id"]) for hit in search["hits"]["hits"]]
    return ids, search["hits"]["total"]["value"]


db_uri = os.getenv("DB_URI")
engine = sqlalchemy.create_engine(db_uri)
Session = orm.scoped_session(orm.sessionmaker())
Session.configure(bind="engine")
session = Session()


ArasBase = declarative_base(metadata=meta)


class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return (
            cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)),
            total,
        )

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            "add": list(session.new),
            "update": list(session.dirty),
            "delete": list(session.deleted),
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes["add"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["update"]:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes["delete"]:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


# db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
# db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            "items": [item.to_dict() for item in resources.items],
            "_meta": {
                "page": page,
                "per_page": per_page,
                "total_pages": resources.pages,
                "total_items": resources.total,
            },
            "_links": {
                "self": url_for(endpoint, page=page, per_page=per_page, **kwargs),
                "next": url_for(endpoint, page=page + 1, per_page=per_page, **kwargs)
                if resources.has_next
                else None,
                "prev": url_for(endpoint, page=page - 1, per_page=per_page, **kwargs)
                if resources.has_prev
                else None,
            },
        }
        return data


class BaseAPISchema(ma.SQLAlchemySchema):

    # created_at = fields.DateTime(dump_only=True)
    # updated_at = fields.DateTime(dump_only=True)

    class Meta:
        sqla_session = Session
        load_instance = True


# A base model for other database tables to inherit
class Base(ArasBase, db.Model, Serializer, DbHelper):

    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # sqlalchemy.exc.InvalidRequestError:
    # Columns with foreign keys to other columns must be declared as @declared_attr
    # callables on declarative mixin classes. For dataclass field() objects, use a lambda:.

    @declared_attr
    def __table_args__(cls):
        return {"extend_existing": True}

    # get this from https://gist.github.com/techniq/5174410
    def _current_user_id_or_none():
        try:
            return current_user.id
        except:
            return None

    @declared_attr
    def created_by_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey(
                "auth_users.id",
                name="fk_%s_created_by_id" % cls.__name__,
                use_alter=True,
            ),
            # nullable=False,
            default=cls._current_user_id_or_none,
        )

    @declared_attr
    def created_by(cls):
        return db.relationship(
            "User",
            primaryjoin="User.id == %s.created_by_id" % cls.__name__,
            remote_side="User.id",
            # overlaps="user, created_by",
        )

    @declared_attr
    def updated_by_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey(
                "auth_users.id",
                name="fk_%s_updated_by_id" % cls.__name__,
                use_alter=True,
            ),
            # nullable=False,
            default=cls._current_user_id_or_none,
            onupdate=cls._current_user_id_or_none,
        )

    @declared_attr
    def updated_by(cls):
        return db.relationship(
            "User",
            primaryjoin="User.id == %s.updated_by_id" % cls.__name__,
            remote_side="User.id",
        )

    def on_add(self):
        self.created_by = current_user.id if current_user else ...

    def on_update(self):
        self.updated_by = current_user.id if current_user else exit()

    def get_all(self):
        return self.query.all()

    def get_by_id(self, id):
        return self.query.filter_by(id=id).first()

    def get_child_list(self, main_model, main_id, column, order_column=None):
        if order_column is None:
            order_column = "id"

        data_main = main_model.get_by_id(main_model, main_id)

        data_array = []
        for data in data_main.__getattribute__(column):
            data_array.append(data)

        return data_array

    def update_dict(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    # belum difungsikan
    def set_view_column():
        return []

    # must implemented by all derived model for search function in listview, or just return []
    def set_searchable_columns(self):
        # raise NotImplementedError("Search column must be filled or just return [] if no column to search")
        return []

    def list_dict(self, data):
        l = []

        for row in data:
            l.append(self.row_dict(self, row))

        dt = self.serialize_list(data)
        # print(l)
        return dt

    def row_dict(self, row):
        d = {}

        for column in inspect(self).attrs.keys():
            d[column] = str(getattr(row, column))

        return d

    def test_(self):
        data = self.query.all()
        l = []
        for row in data:
            l.append(self.row_dict(self, row))

        # dt = self.serialize_list(data)
        # print(l)
        return json.dumps(l)

    def get_filter(self, column, value, order_column=None):
        if order_column is None:
            order_column = "id"

        data = self.query.filter(
            cast(self.__getattribute__(self, column), String).ilike("%" + value + "%")
        ).order_by(self.__getattribute__(self, order_column))
        return data

    def get_filter_with_relation(self, model_ref, column_ref, value, order_column=None):
        if order_column is None:
            order_column = "id"

        data = (
            self.query.join(model_ref)
            .filter(
                cast(model_ref.__getattribute__(model_ref, column_ref), String).ilike(
                    "%" + value + "%"
                )
            )
            .order_by(self.__getattribute__(self, order_column))
        )
        return data

    def get_filter_with_relation_dict(
        self, model_ref, column_ref, value, order_column=None
    ):
        datas = self.get_filter_with_relation(
            self,
            model_ref=model_ref,
            column_ref=column_ref,
            value=value,
            order_column=order_column,
        )
        data_array = []
        for data in datas:
            data_array.append(data.to_dict())
        return jsonify(data_array)

    def get_filter_with_many_to_many(
        self, model_ref, column_ref, value, self_column_relation=None, order_column=None
    ):
        if order_column is None:
            order_column = "id"

        # FIXME: belum berfungsi sebagaimana mestinya
        for col in self_column_relation:
            data = (
                self.query.options(
                    joinedload(self.__getattribute__(self, self_column_relation[0])),
                    joinedload(self.__getattribute__(self, self_column_relation[0])),
                )
                .filter(
                    cast(
                        model_ref.__getattribute__(model_ref, column_ref), String
                    ).ilike("%" + value + "%")
                )
                .order_by(self.__getattribute__(self, order_column))
            )
            return data

    def paginate(function, page, per_page):
        paginate = function.paginate(page=page, per_page=per_page, error_out=False)
        return paginate

    def insert_table_args(
        self,
        param_key=None,
        param_value=None,
        include_properties=None,
        exclude_properties=None,
        order_by=None,
        *args,
        **kwargs,
    ):

        """
        Untuk fungsi render pada form (data yg di load dan nama table), rencana menggunakan fungsi ini,
        jadi data yang di load benar-benar data yang dibutuhkan untuk di load
        """

        if param_key and param_value:
            self.__table_args__[param_key] = (param_value,)
        if include_properties:
            self.__table_args__["include_properties"] = (include_properties,)
        if exclude_properties:
            self.__table_args__["exclude_properties"] = (exclude_properties,)
        if order_by:
            self.__table_args__["order_by"] = (order_by,)

        return self.__table_args__


class MediaType(db.Model):
    __tablename__ = "media_type"

    id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column("name", db.Unicode(length=10))

    def __repr__(self):
        return self.name

    @property
    def media_key(self):
        return (self.name)

    def set_searchable_columns(self):
        col = [
            (self.name.key, None, None),
        ]

        return col

    @staticmethod
    def fill_data():
        type = {"Picture", "Audio"}
        for name in type:
            media_type = MediaType.query.filter_by(name=name).first()

            if media_type is None:
                media_type = MediaType(name=name)
                db.session.add(media_type)
        db.session.commit()


# ArasBase.metadata.create_all(engine)


def db_init():
    # Base.metadata.create_all(engine)
    print("Checking database..")
    if database_exists(engine.url):
        print("Database already exist")
        exit()
    else:
        pass


def db_createall():
    try:
        ArasBase.metadata.create_all(engine)
    except mariadb.Error as e:
        print(f"Error for MariaDB Platform: {e}")
        print("Database initialize failed")
        sys.exit(1)
    else:
        print("Database initialized")


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        db.session.remove()
