from typing import overload, final, TypeVar, Type
from uuid import UUID

__all__ = ['DomainMessage', 'DomainCommand', 'DomainEvent', 'fields']

_T = TypeVar('_T')

class DomainMessage:

    @final
    @overload
    def __init__(self, **kwargs):
        ...

    @property
    @overload
    def __reference__(self) -> UUID:
        ...

    @property
    @overload
    def __timestamp__(self) -> float:
        ...

    @classmethod
    @final
    @overload
    def loads(cls: Type[_T], data: str) -> _T:
        ...

    @classmethod
    @final
    @overload
    def load(cls: Type[_T], data: dict) -> _T:
        ...

    @final
    @overload
    def dumps(self) -> str:
        ...

    @final
    @overload
    def dump(self) -> dict:
        ...


class DomainCommand(DomainMessage):
    ...

class DomainEvent(DomainMessage):
    ...

class DomainStructure:

    @final
    @overload
    def __init__(self, **kwargs):
        ...

    @classmethod
    @final
    @overload
    def loads(cls: Type[_T], data: str) -> _T:
        ...

    @classmethod
    @final
    @overload
    def load(cls: Type[_T], data: dict) -> _T:
        ...

    @final
    @overload
    def dumps(self) -> str:
        ...

    @final
    @overload
    def dump(self) -> dict:
        ...


class DomainCommandResponse:

    @property
    @overload
    def __reference__(self) -> UUID:
        ...

    @property
    @overload
    def __timestamp__(self) -> float:
        ...

    @classmethod
    @final
    @overload
    def loads(cls: Type[_T], data: str) -> _T:
        ...

    @classmethod
    @final
    @overload
    def load(cls: Type[_T], data: dict) -> _T:
        ...

    @final
    @overload
    def dumps(self) -> str:
        ...

    @final
    @overload
    def dump(self) -> dict:
        ...

