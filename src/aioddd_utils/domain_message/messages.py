import typing as t
from datetime import datetime, time, date, timedelta
from decimal import Decimal
from inspect import isclass
from ipaddress import IPv6Address, IPv4Address, IPv4Interface, IPv6Interface
from uuid import UUID

import attr
from marshmallow import Schema, EXCLUDE, fields as mf, post_load, missing

_FIELDS_TYPE = {
    mf.String: str,
    mf.UUID: UUID,
    mf.Number: float,
    mf.Integer: int,
    mf.Float: float,
    mf.Decimal: Decimal,
    mf.Boolean: bool,
    mf.DateTime: datetime,
    mf.NaiveDateTime: datetime,
    mf.AwareDateTime: datetime,
    mf.Time: time,
    mf.Date: date,
    mf.TimeDelta: timedelta,
    mf.URL: str,
    mf.Email: str,
    mf.IP: IPv4Address | IPv6Address,
    mf.IPv4: IPv4Address,
    mf.IPv6: IPv6Address,
    mf.IPInterface: IPv4Interface | IPv6Interface,
    mf.IPv4Interface: IPv4Interface,
    mf.IPv6Interface: IPv6Interface,
}


class UnknownMessageType(Exception):
    def __init__(self, domain: str, message_type: str):
        super(UnknownMessageType, self).__init__(f'Unknown message type {domain=} {message_type=}')


class DomainMessageMeta(type):

    def __new__(mcs, name: str, bases: tuple, attrs: dict):
        module = attrs['__module__']
        if module == __name__ and 'Base' in name:
            return super().__new__(mcs, name, bases, attrs)

        attrs_fields = mcs._get_attrs_fields(attrs)
        klass = super().__new__(mcs, name, bases, attrs_fields)

        base_class = next((base for base in bases if issubclass(base, BaseMessage)), Schema)
        schema_fields = mcs._get_fields_from_attrs(attrs)
        schema = mcs._create_schema_class(klass, schema_fields, base_class.__schema__)
        klass.__schema__ = schema

        domain: str = getattr(klass, '__domain_name__', None)
        if domain is None:
            raise ValueError(f'Required set value to "__domain_name__" class attr for {klass}')
        MESSAGES_REGISTRY[(domain.upper(), name.upper())] = klass

        return attr.s(frozen=True)(klass)

    @classmethod
    def _get_attrs_fields(mcs, attrs: dict[str, t.Any]) -> dict[str, t.Any]:
        fields = {}
        for key, value in attrs.items():
            if ('Meta' in key and isclass(value)) or key in ['dump', 'load']:
                continue
            elif isinstance(value, mf.Field):
                fields[key] = mcs._convert_field_to_attrib(value)
            else:
                fields[key] = value
        return fields

    @staticmethod
    def _convert_field_to_attrib(field: mf.Field):
        params = {}
        if type(field) in _FIELDS_TYPE:
            params['type'] = _FIELDS_TYPE[type(field)]

        if field.required is False:
            params['default'] = None

        if field.load_default is not missing:
            params['default'] = field.default

        return attr.ib(**params)

    @classmethod
    def _create_schema_class(mcs, message_class: object, fields: dict[str, t.Any], base_schema=Schema) -> t.Type[Schema]:
        attrs = fields.copy()

        def load_data(self, data, many, **kwargs):
            if many:
                return tuple(message_class(**item) for item in data)
            else:
                return message_class(**data)

        attrs['__load_message_class__'] = post_load(load_data)
        klass = type(message_class.__name__+'Schema', (base_schema,), attrs)
        return klass  # noqa

    @staticmethod
    def _get_fields_from_attrs(attrs: dict[str, t.Any]) -> dict[str, t.Any]:
        """
         Filter attributes if is instance marshmallow.fields.Field and added marshmallow Meta class
        :param attrs: class attributes
        :return:
        """
        fields = {}
        for key, value in attrs.items():
            if key == 'SchemaMeta' and isclass(value):
                fields['Meta'] = value
            if isinstance(value, mf.Field):
                if key.startswith('_'):
                    fields[value.attribute] = value

                else:
                    fields[key] = value
        if 'Meta' not in fields:
            class Meta:
                pass
            fields['Meta'] = Meta

        fields['Meta'].unknown = EXCLUDE

        return fields


T = t.TypeVar('T')


class BaseMessage(metaclass=DomainMessageMeta):
    __schema__: t.Type[Schema] = Schema
    __domain_name__: str

    @classmethod
    @t.final
    def load(cls: t.Type[T], data: dict) -> T:
        if cls in [BaseMessage, BaseEvent, BaseCommand]:
            TypeError('Can not use with Base domain message classes')
        schema = cls.__schema__()
        return schema.load(data)

    @t.final
    def dump(self) -> dict:
        if isinstance(self, (BaseMessage, BaseEvent, BaseCommand)):
            TypeError('Can not use with Base domain message classes')
        schema = self.__schema__()
        return schema.dump(self)


class BaseEvent(BaseMessage):
    pass


class BaseCommand(BaseMessage):
    pass


MESSAGES_REGISTRY: dict[tuple[str, str], BaseMessage] = {}


def get_message_class(domain_name: str, name: str) -> BaseMessage:
    klass = MESSAGES_REGISTRY.get((domain_name.upper(), name.upper()), None)
    if klass is None:
        raise UnknownMessageType(domain_name, name)
    return klass


