import decimal
from typing import overload
from datetime import datetime, time, date
from uuid import UUID

from yarl import URL


class String:
    @overload
    def __get__(self, instance, owner) -> str:
        ...

class Uuid:
    @overload
    def __get__(self, instance, owner) -> UUID:
        ...

class Integer:
    @overload
    def __get__(self, instance, owner) -> int:
        ...

class Float:
    @overload
    def __get__(self, instance, owner) -> float:
        ...

class Decimal:
    @overload
    def __get__(self, instance, owner) -> decimal.Decimal:
        ...

class Boolean:
    @overload
    def __get__(self, instance, owner) -> bool:
        ...

class Datetime:
    @overload
    def __get__(self, instance, owner) -> datetime:
        ...

class Time:
    @overload
    def __get__(self, instance, owner) -> time:
        ...

class Date:
    @overload
    def __get__(self, instance, owner) -> date:
        ...

class Url:
    @overload
    def __get__(self, instance, owner) -> URL:
        ...

class Email:
    @overload
    def __get__(self, instance, owner) -> str:
        ...
