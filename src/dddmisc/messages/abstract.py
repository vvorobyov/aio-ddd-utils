import typing as t
import abc
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType

from . import fields


class _Nothing:
    pass


class AbstractField(abc.ABC):
    value_type: t.Type

    def __init__(self, *, default: t.Any = _Nothing, nullable: bool = False):
        self.default = default
        self.nullable = nullable

    @abc.abstractmethod
    def validate_value_type(self, value):
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
            value = kwargs.get(name, _Nothing)
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
