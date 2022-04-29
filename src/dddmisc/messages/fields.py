import decimal
import re
import typing
import typing as t
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone, time, date
from urllib.parse import urlparse, ParseResult
from uuid import UUID

import yarl

from dddmisc.messages.core import AbstractField, AbstractDomainMessage, Nothing


class Field(AbstractField):
    converter: t.Callable[[t.Any], t.Any] = None
    serialize_converter: t.Callable[[t.Any], t.Any] = None

    def __init__(self, **kwargs):
        self._field_name: t.Optional[str] = None
        super().__init__(**kwargs)

    def __set_name__(self, owner, name):
        self._field_name = name

    def __get__(self, instance: AbstractDomainMessage, owner):
        if instance is None:
            return self
        if self._field_name.startswith('__') and self._field_name.endswith('__'):
            value = instance.__data__[self._field_name]
        else:
            value = instance.__data__['data'][self._field_name]
        return value

    def __set__(self, instance, value):
        if instance is not None:
            raise FrozenInstanceError(f"cannot assign to field '{self._field_name}'")

    def parse(self, value):
        return self.serialize(value)

    def serialize(self, value):
        if self.serialize_converter is not None:
            return self.serialize_converter(value)
        else:
            return self.value_type(value)

    def validate_value_type(self, value):

        if self.default is not Nothing and value is Nothing:
            value = self.default
        elif self.nullable and value in [None, Nothing]:
            return None
        elif value is Nothing:
            raise AttributeError(f'Not set required attributes {self._field_name}')
        return self.converter(value)

    def raise_type_error(self, value):
        raise TypeError("'{name}' must be {type!r} (got {value!r} that is a {actual!r}).".format(
            name=self._field_name,
            type=self.value_type,
            actual=value.__class__,
            value=value,
        ))


class String(Field):
    value_type = str

    def converter(self, value):
        if isinstance(value, str):
            return value
        self.raise_type_error(value)


class Uuid(Field):
    value_type = UUID

    def converter(self, value):
        try:
            if isinstance(value, UUID):
                return value
            elif isinstance(value, str):
                return UUID(value)
        except ValueError:
            pass
        self.raise_type_error(value)


class Integer(Field):
    value_type = int

    def converter(self, value):
        try:
            if isinstance(value, int):
                return value
            elif isinstance(value, str):
                return int(value)
        except ValueError:
            pass
        self.raise_type_error(value)


class Float(Field):
    value_type = float

    def converter(self, value):
        try:
            if isinstance(value, (float, int, decimal.Decimal, str)):
                return float(value)
            elif isinstance(value, str):
                return int(value)
        except ValueError:
            pass
        self.raise_type_error(value)


class Decimal(Field):
    value_type = decimal.Decimal

    def __init__(self, places: t.Union[int, None] = None,
                 rounding: t.Union[str, None] = None, **kwargs):
        self.rounding = rounding
        self.places = (
            decimal.Decimal((0, (1,), -places)) if places is not None else None
        )
        super().__init__(**kwargs)

    def converter(self, value):
        try:
            value = decimal.Decimal(value)
            if self.places is not None:
                value = value.quantize(self.places, self.rounding)
            return value
        except (decimal.InvalidOperation, TypeError):
            pass
        self.raise_type_error(value)


class Boolean(Field):
    value_type = bool

    def converter(self, value):
        if isinstance(value, str):
            value = value.lower()
        truthy = {True, "true", "t", "yes", "y", "on", "1", 1}
        falsy = {False, "false", "f", "no", "n", "off", "0", 0}
        try:
            if value in truthy:
                return True
            if value in falsy:
                return False
        except TypeError:
            # Raised when "val" is not hashable (e.g., lists)
            pass
        self.raise_type_error(value)


class Datetime(Field):
    value_type = datetime

    def converter(self, value):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        self.raise_type_error(value)


class Time(Field):
    value_type = time

    def converter(self, value):
        if isinstance(value, str):
            return time.fromisoformat(value)
        elif isinstance(value, time):
            return value
        self.raise_type_error(value)


class Date(Field):
    value_type = date

    def converter(self, value):
        if isinstance(value, str):
            return date.fromisoformat(value)
        elif isinstance(value, date):
            return value
        self.raise_type_error(value)


class Url(Field):
    value_type = yarl.URL



    def converter(self, value):
        try:
            return yarl.URL(value)
        except TypeError:
            pass
        self.raise_type_error(value)


class Email(Field):
    value_type = str

    USER_REGEX = re.compile(
        r"(^[-!#$%&'*+/=?^`{}|~\w]+(\.[-!#$%&'*+/=?^`{}|~\w]+)*\Z"  # dot-atom
        # quoted-string
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]'
        r'|\\[\001-\011\013\014\016-\177])*"\Z)',
        re.IGNORECASE | re.UNICODE,
    )

    DOMAIN_REGEX = re.compile(
        # domain
        r"(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+" r"(?:[A-Z]{2,6}|[A-Z0-9-]{2,})\Z"
        # literal form, ipv4 address (SMTP 4.1.3)
        r"|^\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)"
        r"(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]\Z",
        re.IGNORECASE | re.UNICODE,
    )

    DOMAIN_WHITELIST = ("localhost",)

    def converter(self, value):
        if isinstance(value, str):
            if not value or "@" not in value:
                raise self.raise_type_error(value)
            user_part, domain_part = value.rsplit("@", 1)
            if not self.USER_REGEX.match(user_part):
                raise self.raise_type_error(value)
            if domain_part not in self.DOMAIN_WHITELIST:
                if not self.DOMAIN_REGEX.match(domain_part):
                    try:
                        domain_part = domain_part.encode("idna").decode("ascii")
                    except UnicodeError:
                        pass
                    else:
                        if self.DOMAIN_REGEX.match(domain_part):
                            return value
                    self.raise_type_error(value)
            return str(value)
        self.raise_type_error(value)
