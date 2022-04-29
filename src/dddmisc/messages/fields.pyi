import decimal
from typing import overload, Any, Union
from datetime import datetime, time, date
from uuid import UUID

from yarl import URL

from dddmisc.messages.core import Nothing


class Field:
    @overload
    def __init__(self, *, default: Any = Nothing, nullable: bool = False):
        ...


class String(Field):
    @overload
    def __get__(self, instance, owner) -> str:
        ...

class Uuid(Field):
    @overload
    def __get__(self, instance, owner) -> UUID:
        ...

class Integer(Field):
    @overload
    def __get__(self, instance, owner) -> int:
        ...

class Float(Field):
    @overload
    def __get__(self, instance, owner) -> float:
        ...

class Decimal(Field):
    @overload
    def __init__(self, places: Union[int, None] = None,
                 rounding: Union[str, None] = None,
                 *, default: Any = Nothing, nullable: bool = False):
        ...
    @overload
    def __get__(self, instance, owner) -> decimal.Decimal:
        ...

class Boolean(Field):
    @overload
    def __get__(self, instance, owner) -> bool:
        ...

class Datetime(Field):
    @overload
    def __get__(self, instance, owner) -> datetime:
        ...

class Time(Field):
    @overload
    def __get__(self, instance, owner) -> time:
        ...

class Date(Field):
    @overload
    def __get__(self, instance, owner) -> date:
        ...

class Url(Field):
    @overload
    def __get__(self, instance, owner) -> URL:
        ...

class Email(Field):
    @overload
    def __get__(self, instance, owner) -> str:
        ...
