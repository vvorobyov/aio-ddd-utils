import abc
from typing import TypeVar, Type, Protocol, runtime_checkable
from uuid import UUID

T = TypeVar('T')


@runtime_checkable
class CrossDomainObjectProtocol(Protocol):
    """
    Общий интерфейс объекта используемого для междоменного взаимодействия
    Возможные типы объектов:
    - Событие
    - Команда
    - Ответ на команду
    - Исключение
    :param def load(cls, data: dict) - Метод десериализации объекта из словаря
    :param def loads(cls, data: str) - Метод десериализации объекта из json-строки
    :param def dump(self) -> dict - Метод сериализации объекта в словарь
    :param def dumps(self) -> str - Метод сериализации объекта в json-строку
    """

    __reference__: UUID
    __timestamp__: float

    @classmethod
    def load(cls: Type[T], data: dict) -> T:
        ...

    @classmethod
    def loads(cls: Type[T], data: str) -> T:
        ...

    def dump(self) -> dict:
        ...

    def dumps(self) -> str:
        ...