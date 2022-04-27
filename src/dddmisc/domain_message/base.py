import abc
import typing as t

from marshmallow import Schema


T = t.TypeVar('T')


class AbstractDomainMessage(abc.ABC):
    __schema__: Schema = Schema()
    __domain_name__: str
    __registered__: bool

    def __init__(self, **kwargs):
        pass

    @classmethod
    @abc.abstractmethod
    def load(cls: t.Type[T], data: dict) -> T:
        ...

    @classmethod
    @abc.abstractmethod
    def loads(cls: t.Type[T], data: bytes) -> T:
        ...

    @abc.abstractmethod
    def dump(self) -> dict:
        ...

    @abc.abstractmethod
    def dumps(self) -> bytes:
        ...


