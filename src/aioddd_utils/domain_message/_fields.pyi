import decimal
import typing as t
import uuid
from datetime import datetime, time, date

from . import fields as f
from .messages import Object
from ..message_bus import AbstractDomainMessage


class String:
    @t.overload
    def __get__(self, instance, owner) -> str: ...


class UUID:
    @t.overload
    def __get__(self, instance, owner) -> uuid.UUID: ...


class Integer:
    @t.overload
    def __get__(self, instance, owner) -> int: ...


class Float:
    @t.overload
    def __get__(self, instance, owner) -> float: ...


class Decimal:
    @t.overload
    def __get__(self, instance, owner) -> decimal.Decimal: ...


class Boolean:
    @t.overload
    def __get__(self, instance, owner) -> bool: ...


class DateTime:
    @t.overload
    def __get__(self, instance, owner) -> datetime: ...


class Time:
    @t.overload
    def __get__(self, instance, owner) -> time: ...


class Date:
    @t.overload
    def __get__(self, instance, owner) -> date: ...


class URL:
    @t.overload
    def __get__(self, instance, owner) -> str: ...


class Email:
    @t.overload
    def __get__(self, instance, owner) -> str: ...


# _T = t.TypeVar('_T')
_T = t.TypeVar('_T', bound=Object)

class Nested:
    @t.overload
    def __new__(cls, nested: t.Type[_T], *, many: bool = True, **kwargs)-> tuple[_T]: ...
    @t.overload
    def __new__(cls, nested: t.Type[_T], *, many: bool = False, **kwargs)-> _T: ...
    # def __get__(self, instance, owner) -> _T:  # type: ignore
    #     ...




