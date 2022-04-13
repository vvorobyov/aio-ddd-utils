import decimal
import typing as t
import uuid
from datetime import datetime, time, date
from marshmallow import fields as mf
from .messages import Object

__all__ = ['String', 'UUID', 'Integer', 'Float',
           'Boolean', 'DateTime', 'Time', 'Date',
           'URL', 'Email',
           'Nested', 'List']

_V = t.TypeVar('_V')

class Field(t.Generic[_V]):
    ...

class String(Field):
    @t.overload
    def __get__(self, instance, owner) -> str: ...


class UUID(Field):
    @t.overload
    def __get__(self, instance, owner) -> uuid.UUID: ...


class Integer(Field):
    @t.overload
    def __get__(self, instance, owner) -> int: ...


class Float(Field):
    @t.overload
    def __get__(self, instance, owner) -> float: ...


class Decimal(Field):
    @t.overload
    def __get__(self, instance, owner) -> decimal.Decimal: ...


class Boolean(Field):
    @t.overload
    def __get__(self, instance, owner) -> bool: ...


class DateTime(Field):
    @t.overload
    def __get__(self, instance, owner) -> datetime: ...


class Time(Field):
    @t.overload
    def __get__(self, instance, owner) -> time: ...


class Date(Field):
    @t.overload
    def __get__(self, instance, owner) -> date: ...


class URL(Field):
    @t.overload
    def __get__(self, instance, owner) -> str: ...


class Email(Field):
    @t.overload
    def __get__(self, instance, owner) -> str: ...


_T = t.TypeVar('_T', bound=Object)

class Nested(Field):
    @t.overload
    def __new__(cls, nested: t.Type[_T], *, many: bool = False, **kwargs)-> t.Union[tuple[_T], _T]: ...


class List(Field):
    @t.overload
    def __new__(cls, cls_or_instance: Field[_T], *, many: bool = False, **kwargs)-> tuple[_T]: ...

