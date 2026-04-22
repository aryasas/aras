from sqlalchemy import inspect, MetaData
from sqlalchemy.orm import RelationshipProperty, class_mapper, ColumnProperty


meta = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class DbHelper(object):
    def get_all_columns(self):
        col = []
        for c in self.__table__.columns:
            col.append(str(c.name))
        for c in inspect(self).attrs:
            if isinstance(c, RelationshipProperty) and str(c.key)[0] != "_":
                col.append(c.key)
        return col

    def get_columns_relations(self):
        return [
            prop.key
            for prop in class_mapper(self).iterate_properties
            if isinstance(prop, RelationshipProperty) and str(prop.key)[0] != "_"
        ]

    def get_column(self):
        return [
            prop.key
            for prop in class_mapper(self).iterate_properties
            if isinstance(prop, ColumnProperty)
        ]


class Serializer(object):
    def serialize(self):
        return {c: str(getattr(self, c)) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(list):
        return [m.serialize() for m in list]

    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
