import abc
import typing as t
from ._fields import Field
import attr
from marshmallow import Schema, EXCLUDE, post_load

from .base import AbstractDomainMessage
from .exceptions import UnknownMessageType


class DomainMessageMeta(abc.ABCMeta):

    def __new__(mcs, name: str, bases: tuple, attrs: dict):
        module = attrs['__module__']
        if module == __name__:
            klass = super().__new__(mcs, name, bases, attrs)
        else:
            attrs_fields = mcs._get_attrs_fields(attrs)
            klass = super().__new__(mcs, name, bases, attrs_fields)

            base_class = next((base for base in bases if issubclass(base, AbstractDomainMessage)), Schema)
            schema_fields = mcs._get_fields_from_attrs(attrs)
            schema = mcs._create_schema_class(klass, schema_fields, type(base_class.__schema__))
            klass.__schema__ = schema()

            if not issubclass(base_class, Object):
                domain: str = getattr(klass, '__domain_name__', None)
                if domain is None:
                    raise ValueError(f'Required set value to "__domain_name__" class attr for {klass}')
                register_flag = getattr(klass, '__registered__', True)
                setattr(klass, '__registered__', register_flag)
                if not issubclass(base_class, Object) and register_flag:
                    MESSAGES_REGISTRY[(domain.upper(), name.upper())] = klass
        return attr.s(frozen=True)(klass)

    @classmethod
    def _get_attrs_fields(mcs, attrs: dict[str, t.Any]) -> dict[str, t.Any]:
        fields = {}
        for key, value in attrs.items():
            if key in ['dump', 'load']:
                continue
            elif isinstance(value, Field):
                fields[key] = value.get_attrib()
            else:
                fields[key] = value
        return fields

    @classmethod
    def _create_schema_class(mcs, message_class: t.Type[AbstractDomainMessage],
                             fields: dict[str, t.Any], base_schema=Schema) -> t.Type[Schema]:
        attrs = fields.copy()

        def load_data(self, data: t.Union[dict, list[dict]], many, **kwargs):
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
            if isinstance(value, Field):
                if key.startswith('_'):
                    raise ValueError("Can't use private field with domain message class")
                else:
                    fields[key] = value.get_marshmallow_field()

        class Meta:
            unknown = EXCLUDE

        fields['Meta'] = Meta

        return fields


T = t.TypeVar('T')


class BaseMessage(AbstractDomainMessage, metaclass=DomainMessageMeta):
    @classmethod
    @t.final
    def load(cls: t.Type[T], data: dict) -> T:
        return cls.__schema__.load(data)

    @t.final
    def dump(self) -> dict:
        return self.__schema__.dump(self)


class Event(BaseMessage):
    pass


class Command(BaseMessage):
    pass


class Object(AbstractDomainMessage, metaclass=DomainMessageMeta):
    pass


MESSAGES_REGISTRY: dict[tuple[str, str], t.Type[AbstractDomainMessage]] = {}


def get_message_class(domain_name: str, name: str) -> t.Type[AbstractDomainMessage]:
    klass = MESSAGES_REGISTRY.get((domain_name.upper(), name.upper()), None)
    if klass is None:
        raise UnknownMessageType(domain_name, name)
    return klass
