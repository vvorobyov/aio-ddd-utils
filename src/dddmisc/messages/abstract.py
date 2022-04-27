import typing as t
import abc
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class _Nothing:
    pass


class AbstractField(abc.ABC):
    nullable: bool = False
    default: t.Any = _Nothing
    factory: t.Callable = _Nothing
    value_type: t.Type


@dataclass(frozen=True)
class Metadata:
    domain: str
    fields: dict[str, AbstractField]
    is_baseclass: bool = False

    def validate_fields(self, **kwargs):
        self._check_parameters(**kwargs)
        self._validate_values_type(**kwargs)
        result = {}
        for name, field in self.fields.items():
            value = kwargs.get(name, _Nothing)
            if value is _Nothing:
                if field.nullable:
                    value = None
                if field.default is not _Nothing:
                    value = field.default
                if field.factory is not _Nothing:
                    value = field.factory()
            result[name] = value
        return result

    def _check_parameters(self, **kwargs):
        self_keys = set(self.fields.keys())
        income_keys = set(kwargs.keys())
        if unknown_keys := (income_keys - self_keys):
            raise AttributeError(f'Unknown attributes {", ".join(unknown_keys)}')
        required_keys = set(key for key, field in self.fields.items()
                            if (not field.nullable
                                and field.default is not _Nothing
                                and field.factory is not _Nothing))
        if not_set_keys := (required_keys - income_keys):
            raise AttributeError(f'Not set required attributes {", ".join(not_set_keys)}')

    def _validate_values_type(self, **kwargs):
        for name, field in self.fields.items():
            value = kwargs.get(name, _Nothing)
            if value is not _Nothing:
                if field.nullable:
                    continue
                elif field.default is not _Nothing:
                    continue
                elif field.factory is not _Nothing:
                    continue
                elif isinstance(value, field.value_type):
                    continue
                raise TypeError(f'"{name}" got is instance of {field.value_type}')


class AbstractDomainMessage(abc.ABC):
    from . import fields
    __reference__ = fields.Uuid()
    __timestamp__ = fields.Integer()

    def __init__(self, **kwargs):
        self.__data__ = {
            '__reference__': uuid.uuid4(),
            '__timestamp__': datetime.now(tz=timezone.utc).timestamp(),
            'data': kwargs
        }

    @classmethod
    @t.final
    def load(cls, data: dict):
        """
        Method restore instance from data dict

        :param data:
        :return:
        """

    @classmethod
    @t.final
    def loads(cls, data: t.Union[bytes, str]):
        """
        Method restore instance from json string

        :param bytes data: json data string
        :return: instance of domain command
        """

    @t.final
    def dump(self) -> dict:
        """
        Method for dump instance to json dict

        :return:
        """

    @t.final
    def dumps(self) -> bytes:
        """
        Method for dump command to json string

        :return:
        """

