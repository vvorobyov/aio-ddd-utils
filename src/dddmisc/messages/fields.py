import decimal
import typing as t
from datetime import datetime, timezone, time, date
from urllib.parse import urlparse, ParseResult
from uuid import UUID


class Field:

    serialize_type: t.Type = None
    serialize_converter: t.Callable[[t.Any], t.Any] = None

    def parse(self, value):
        return self.serialize(value)

    def serialize(self, value):
        if self.serialize_converter is not None:
            return self.serialize_converter(value)
        else:
            return self.serialize_type(value)


class String(Field):
    serialize_type = str


class Uuid(Field):
    serialize_type = UUID


class Integer(Field):
    serialize_type = int


class Float(Field):
    serialize_type = float


class Decimal(Field):
    serialize_type = decimal.Decimal

    def __init__(self, places: t.Union[int, None] = None,
                 rounding: t.Union[int, None] = None):
        self.rounding = rounding
        self.places = (
            decimal.Decimal((0, (1,), -places)) if places is not None else None
        )

    def serialize_converter(self, value):
        return decimal.Decimal(value).quantize(self.places, self.rounding)


class Boolean(Field):
    serialize_type = bool


class Datetime(Field):
    serialize_type = datetime

    @staticmethod
    def serialize_converter(value):
        return datetime.fromisoformat(value).astimezone(timezone.utc)


class Time(Field):
    serialize_type = time

    @staticmethod
    def serialize_converter(value):
        return time.fromisoformat(value)


class Date(Field):
    serialize_type = date

    @staticmethod
    def serialize_converter(value):
        return date.fromisoformat(value)


class Url(Field):
    serialize_type = ParseResult

    @staticmethod
    def serialize_converter(value):
        return urlparse(value)


class Email(Field):
    serialize_type = str

