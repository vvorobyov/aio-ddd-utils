
from typing import overload, final, TypeVar, Type, Callable, Union, Tuple
from uuid import UUID


_T = TypeVar('_T')


class DomainCommand:
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

class DomainEvent:
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


get_message_class = Callable[[Union[Tuple[str, str], str]], Union[Type[DomainCommand], Type[DomainEvent]]]



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

    @overload
    def __init__(self, aggregator_ref: UUID, command_ref: UUID):
        ...

    @property
    @overload
    def __reference__(self) -> UUID:
        ...

    @property
    @overload
    def reference(self) -> UUID:
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

