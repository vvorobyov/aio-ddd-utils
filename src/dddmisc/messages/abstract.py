import typing as t
import abc
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class _Nothing:
    pass


class AbstractField(abc.ABC):
    nullable: bool
    default: t.Any = _Nothing


@dataclass(frozen=True)
class Metadata:
    domain: str
    fields: dict[str, AbstractField]
    is_baseclass: bool = False

    def validate_fields(self, income_data: dict):
        self_keys = set(self.fields.keys())
        income_keys = set(income_data.keys())
        if unknown_keys := (income_keys - self_keys):
            raise AttributeError(f'Unknown attributes {", ".join(unknown_keys)}')
        required_keys = set(key for key, field in self.fields.items()
                            if not field.nullable)
        if not_set_keys := (required_keys - income_keys):
            raise AttributeError(f'Not set required attributes {", ".join(not_set_keys)}')

        result = {'data': {}}
        for name, field in self.fields.items():
            value = income_data[name]
            if name.startswith('__') and name.endswith('__'):
                result[name] = value
            else:
                result['data'][name] = value
        return result


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

