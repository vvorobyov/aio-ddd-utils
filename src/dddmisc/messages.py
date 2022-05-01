import abc
import datetime as dt
import json
import typing as t
from dataclasses import dataclass, FrozenInstanceError
from types import MappingProxyType
from uuid import uuid4, UUID


class Nothing:
    pass


T = t.TypeVar('T')


class Field(t.Generic[T]):
    value_type: t.Type

    def __init__(self, *, default: T = Nothing, nullable: bool = False):
        self.default = default
        self.nullable = nullable
        self._field_name: t.Optional[str] = None

    def __set_name__(self, owner, name):
        self._field_name = name
        if not issubclass(owner, BaseDomainMessage):
            raise TypeError('{field!r} can used only with subclasses of{type!r} (got {actual!r}).'.format(
                field=self.__class__,
                type=BaseDomainMessage,
                actual=owner.__class__,
            ))

    def __get__(self, instance: 'BaseDomainMessage', owner):
        if instance is None:
            return self
        if isinstance(instance, BaseDomainMessage):
            return instance.get_attr(self._field_name)
        raise

    def __set__(self, instance, value):
        if instance is not None:
            raise FrozenInstanceError("cannot assign to field '{name}'".format(
                name=self._field_name
            ))

    def deserialize(self, value) -> T:
        if value is Nothing and self.default:
            value = self.default
        if value is Nothing and self.nullable:
            return None
        if value is Nothing:
            raise AttributeError('Not set required attribute "{name}"'.format(name=self._field_name))
        return self._deserialize(value)

    def _deserialize(self, value):
        return value

    def serialize(self, value: T):
        return self._serialize(value)

    def _serialize(self, value: T):
        return value

    def raise_type_error(self, value):
        raise TypeError("'{name}' must be {type!r} (got {value!r} that is a {actual!r}).".format(
            name=self._field_name,
            type=self.value_type,
            actual=value.__class__,
            value=value,
        ))


@dataclass(frozen=True)
class Metadata:
    fields: MappingProxyType[str, Field]
    domain: str
    is_baseclass: bool


_T = t.TypeVar('_T')


class BaseDomainMessage(abc.ABC):
    __metadata__: Metadata

    def __init__(self, **kwargs):
        if self.__metadata__.is_baseclass:
            if not isinstance(self, DomainStructure):
                raise TypeError(f"cannot create instance of '{type(self).__name__}' class, because this is BaseClass")
        self._data = self._deserialize(kwargs)

    def _deserialize(self, obj: dict):
        result = {}
        errors = {}
        for key, field in self.__metadata__.fields.items():
            try:
                result[key] = field.deserialize(obj.get(key, Nothing))
            except BaseException as err:
                errors[key] = err
        if not errors:
            return result

        raise list(errors.values())[0]  # TODO реализовать массовую обработку ошибок

    def _serialize(self):
        result = {}
        for key, field in self.__metadata__.fields.items():
            result[key] = field.serialize(self._data.get(key))
        return result

    def get_attr(self, item: str):
        return self._data[item]

    def __eq__(self, other):
        return isinstance(other, BaseDomainMessage) and self._data == other._data

    def __hash__(self):
        return hash(repr(self._data))

    def __repr__(self):
        fields = ', '.join(f'{name}={getattr(self, name)!r}' for name in self.__metadata__.fields.keys())
        return f'{self.__class__.__module__}.{self.__class__.__name__}({fields})  # domain="{self.__metadata__.domain}"'

    @classmethod
    def load(cls: t.Type[_T], data: dict) -> _T:
        """
        Method restore instance from data dict

        :param data:
        :return:
        """
        return cls(**data)

    @classmethod
    def loads(cls: t.Type[_T], data: str) -> _T:
        dict_data = json.loads(data)
        return cls.load(dict_data)

    def dump(self) -> dict:
        """
        Method for dump instance to json dict

        :return:
        """
        return self._serialize()

    def dumps(self) -> str:
        data = self.dump()
        return json.dumps(data)


def __make_register_functions():
    MESSAGE_REGISTER: t.Dict[t.Tuple[str, str], t.Type[BaseDomainMessage]] = {}

    def register(klass: t.Type[BaseDomainMessage]):
        if klass.__metadata__.is_baseclass:
            return
        domain = klass.__metadata__.domain
        name = klass.__name__
        if (domain, name) in MESSAGE_REGISTER:
            raise RuntimeError(f'Multiple message class in domain "{klass.__metadata__.domain}" with name "{name}"')
        MESSAGE_REGISTER[(domain, name)] = klass

    def get(key: t.Union[t.Tuple[str, str], str]) -> t.Type[BaseDomainMessage]:
        if isinstance(key, str):
            domain, name = key.split('.')
            key_ = (domain, name)
        else:
            key_ = key
        if key_ in MESSAGE_REGISTER:
            return MESSAGE_REGISTER[key_]
        raise ValueError(f"Message class by '{key}' not found")

    return register, get


register_message_class, get_message_class = __make_register_functions()


class DomainMessageMeta(abc.ABCMeta):
    def __new__(mcs, name: str, bases: t.Tuple[t.Type], attrs: dict):
        domain_message_bases = [base for base in bases if issubclass(base, BaseDomainMessage)]
        base_dm_count = len(domain_message_bases)
        if base_dm_count > 1:
            raise TypeError('Inherit from more one "BaseDomainMessage" class')
        if base_dm_count == 0:
            bases = (BaseDomainMessage, *bases)
            domain_message_bases = [BaseDomainMessage]
        new_attrs = {**attrs}

        if attrs['__module__'] != __name__:
            for key in ['load', 'loads', 'dump', 'dumps']:
                new_attrs.pop(key, None)

        new_attrs['__metadata__'] = mcs._get_metadata(domain_message_bases[0], **attrs)
        klass = super(DomainMessageMeta, mcs).__new__(mcs, name, bases, new_attrs)
        register_message_class(klass)  # noqa
        return klass

    @staticmethod
    def _get_metadata(base: t.Optional[t.Type[BaseDomainMessage]], **attrs) -> Metadata:
        fields = {key: field for key, field in attrs.items() if isinstance(field, Field)}
        base_metadata: Metadata = getattr(base, '__metadata__', None)

        meta_info = attrs.get('Meta', None)
        is_baseclass = getattr(meta_info, 'is_baseclass', False)
        domain = getattr(base_metadata, 'domain', None) or getattr(meta_info, 'domain', None)
        if domain is None:
            is_baseclass = True
        base_fields = dict(getattr(base_metadata, 'fields', {}))
        return Metadata(fields=MappingProxyType({**base_fields, **fields}),
                        domain=domain, is_baseclass=is_baseclass)


class DomainMessage(BaseDomainMessage, metaclass=DomainMessageMeta):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reference = uuid4()
        self._timestamp = dt.datetime.now().timestamp()

    @property
    def __reference__(self) -> UUID:
        return self._reference

    @property
    def __timestamp__(self) -> float:
        return self._timestamp

    @classmethod
    def load(cls, data):
        obj = super().load(data.get('data', {}))
        if ref_value := data.get('__reference__', None):
            obj._reference = UUID(ref_value)
        if ts_value := data.get('__timestamp__', None):
            obj._timestamp = ts_value
        return obj

    @classmethod
    def loads(cls, data):
        return super().loads(data)

    def dump(self):
        result = {
            '__reference__': str(self.__reference__),
            '__timestamp__': self.__timestamp__,
            'data': super().dump()}
        return result

    def dumps(self):
        return super().dumps()


class DomainStructure(BaseDomainMessage, metaclass=DomainMessageMeta):
    pass


class DomainCommand(DomainMessage):
    pass


class DomainEvent(DomainMessage):
    pass


class DomainCommandResponse:

    def __init__(self, aggregator_ref: UUID, command_ref: UUID):
        self._command_ref = command_ref
        self._timestamp = dt.datetime.now().timestamp()
        self._aggregator_ref = aggregator_ref

    @property
    def __reference__(self) -> UUID:
        """Идентификатор команды для которой предназначен ответ"""
        return self._command_ref

    @property
    def reference(self) -> UUID:
        """Идентификатор """
        return self._aggregator_ref

    @property
    def __timestamp__(self) -> float:
        return self._timestamp

    @classmethod
    def load(cls, data: dict):
        aggr_ref = UUID(data.get('data', {}).get('reference', Nothing))
        command_ref = UUID(data['__reference__'])
        obj = cls(aggr_ref, command_ref)
        if ref_value := data.get('__reference__', None):
            obj._reference = UUID(ref_value)
        if ts_value := data.get('__timestamp__', None):
            obj._timestamp = ts_value
        return obj

    @classmethod
    def loads(cls, data):
        dict_data = json.loads(data)
        return cls.load(dict_data)

    def dump(self):
        result = {
            '__reference__': str(self.__reference__),
            '__timestamp__': self.__timestamp__,
        }
        return result

    def dumps(self):
        data = self.dump()
        return json.dumps(data)

    def __eq__(self, other):
        return (isinstance(other, DomainCommandResponse)
                and self.__reference__ == other.__reference__
                and self.__timestamp__ == other.__timestamp__
                and self.__reference__ == other.__reference__)

    def __hash__(self):
        return hash(f'{self.__class__.__name__}.{self.reference}.'
                    f'{self.__reference__}.{self.__timestamp__}')
