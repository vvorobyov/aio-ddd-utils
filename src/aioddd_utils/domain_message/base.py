import abc
import typing as t

from marshmallow import Schema


class AbstractDomainMessage(abc.ABC):
    __schema__: t.Type[Schema]

    def __init__(self, **kwargs):
        pass

    @classmethod
    def load(cls, data: dict):
        schema = cls.__schema__()
        return schema.load(data)

    def dump(self):
        schema = self.__schema__()
        return schema.dump(self)