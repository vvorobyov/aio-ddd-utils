import abc
import typing as t
from dataclasses import dataclass
from types import MappingProxyType


class Nothing:
    pass


class AbstractField(abc.ABC):
    value_type: t.Type

    def __init__(self, *, default: t.Any = Nothing, nullable: bool = False):
        self.default = default
        self.nullable = nullable

    @abc.abstractmethod
    def validate_value_type(self, value):
        pass

    @abc.abstractmethod
    def to_json(self, value):
        pass


@dataclass(frozen=True)
class Metadata:
    fields: MappingProxyType[str, AbstractField]
    domain: str
    is_baseclass: bool

    def validate_initial_data(self, **kwargs):
        result = {}
        for name, field in self.fields.items():
            self._check_parameter(name)
            value = kwargs.get(name, Nothing)
            if not (name.startswith('__') and name.endswith('__')):
                result[name] = field.validate_value_type(value)
        return result

    def _check_parameter(self, name: str):
        if name not in self.fields:
            raise AttributeError(f'Unknown attributes {name}')


class AbstractDomainMessage(abc.ABC):
    __metadata__: Metadata

    def __init__(self, **kwargs):
        if self.__metadata__.is_baseclass:
            raise TypeError(f"cannot create instance of '{type(self).__name__}' class, because this is BaseClass")
        self.__data__ = {
            'data': self.__metadata__.validate_initial_data(**kwargs)
        }

    def __eq__(self, other):
        return isinstance(other, AbstractDomainMessage) and self.__data__ == other.__data__

    def __hash__(self):
        return hash(repr(self.__data__))

    def __repr__(self):
        fields = ', '.join(f'{name}={getattr(self, name)!r}' for name in self.__metadata__.fields.keys())
        return f'{self.__class__.__module__}.{self.__class__.__name__}({fields})  # domain="{self.__metadata__.domain}"'

    @classmethod
    def load(cls, data: dict):
        """
        Method restore instance from data dict

        :param data:
        :return:
        """
        result = {}
        for name, field in cls.__metadata__.fields.items():
            if not (name.startswith('__') and name.endswith('__')):
                value = data.get(name, Nothing)
                result[name] = field.validate_value_type(value)
        return cls(**result)

    @t.final
    def dump(self) -> dict:
        """
        Method for dump instance to json dict

        :return:
        """
        result = {}
        for name, fields in self.__metadata__.fields.items():
            if not(name.startswith('__') and name.endswith('__')):
                result[name] = fields.to_json(getattr(self, name))
        return result


def __make_register_functions():

    MESSAGE_REGISTER: t.Dict[t.Tuple[str, str], t.Type[AbstractDomainMessage]] = {}

    def register(klass: t.Type[AbstractDomainMessage]):
        if klass.__metadata__.is_baseclass:
            return
        domain = klass.__metadata__.domain
        name = klass.__name__
        if (domain, name) in MESSAGE_REGISTER:
            raise RuntimeError(f'Multiple message class in domain "{klass.__metadata__.domain}" with name "{name}"')
        MESSAGE_REGISTER[(domain, name)] = klass

    def get(key: t.Union[t.Tuple[str, str], str]) -> t.Type[AbstractDomainMessage]:
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
        domain_message_bases = [base for base in bases if issubclass(base, AbstractDomainMessage)]
        base_dm_count = len(domain_message_bases)
        if base_dm_count > 1:
            raise TypeError('Inherit from more one "AbstractDomainMessage" class')
        if base_dm_count == 0:
            bases = (AbstractDomainMessage, *bases)
            domain_message_bases = [AbstractDomainMessage]
        new_attrs = {**attrs}

        # for key in ['Meta']:  # , 'load', 'loads', 'dump', 'dumps']:
        #     new_attrs.pop(key, None)

        new_attrs['__metadata__'] = mcs._get_metadata(domain_message_bases[0], **attrs)
        klass = super(DomainMessageMeta, mcs).__new__(mcs, name, bases, new_attrs)
        register_message_class(klass)  # noqa
        return klass

    @staticmethod
    def _get_metadata(base: t.Optional[t.Type[AbstractDomainMessage]], **attrs) -> Metadata:
        fields = {key: field for key, field in attrs.items() if isinstance(field, AbstractField)}
        meta_info = attrs.get('Meta', None)
        is_baseclass = getattr(meta_info, 'is_baseclass', False)
        base_metadata: Metadata = getattr(base, '__metadata__', None)
        domain = getattr(base_metadata, 'domain', None) or getattr(meta_info, 'domain', None)
        if domain is None:
            is_baseclass = True
        base_fields = dict(getattr(base_metadata, 'fields', {}))
        return Metadata(fields=MappingProxyType({**base_fields, **fields}),
                        domain=domain, is_baseclass=is_baseclass)

