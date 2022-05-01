import decimal
import re
import typing as t
from datetime import datetime, timezone, time, date
from uuid import UUID

import yarl

from dddmisc.messages.core import DomainStructure, Field, Nothing


class String(Field):
    value_type = str

    def _deserialize(self, value):
        if isinstance(value, str):
            return value
        self.raise_type_error(value)


class Uuid(Field):
    value_type = UUID

    def _deserialize(self, value):
        try:
            if isinstance(value, UUID):
                return value
            elif isinstance(value, str):
                return UUID(value)
        except ValueError:
            pass
        self.raise_type_error(value)

    def _serialize(self, value):
        return str(value)


class Integer(Field):
    value_type = int

    def _deserialize(self, value):
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

    def _deserialize(self, value):
        try:
            if isinstance(value, (float, int, decimal.Decimal, str)):
                return float(value)
            elif isinstance(value, str):
                return float(value)
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

    def _deserialize(self, value):
        try:
            value = decimal.Decimal(value)
            if self.places is not None:
                value = value.quantize(self.places, self.rounding)
            return value
        except (decimal.InvalidOperation, TypeError):
            pass
        self.raise_type_error(value)

    def _serialize(self, value):
        return str(value)


class Boolean(Field):
    value_type = bool
    #: Default truthy values.
    truthy = {
        "t",
        "T",
        "true",
        "True",
        "TRUE",
        "on",
        "On",
        "ON",
        "y",
        "Y",
        "yes",
        "Yes",
        "YES",
        "1",
        1,
        True,
    }
    #: Default falsy values.
    falsy = {
        "f",
        "F",
        "false",
        "False",
        "FALSE",
        "off",
        "Off",
        "OFF",
        "n",
        "N",
        "no",
        "No",
        "NO",
        "0",
        0,
        0.0,
        False,
    }

    def __init__(self, *, truthy: t.Optional[set] = None, falsy: t.Optional[set] = None, **kwargs):
        super().__init__(**kwargs)

        if truthy is not None:
            self.truthy = set(truthy)
        if falsy is not None:
            self.falsy = set(falsy)

    def _deserialize(self, value):
        if isinstance(value, str):
            value = value.lower()
        try:
            if value in self.truthy:
                return True
            if value in self.falsy:
                return False
        except TypeError:
            # Raised when "val" is not hashable (e.g., lists)
            pass
        self.raise_type_error(value)


class Datetime(Field):
    value_type = datetime

    def _deserialize(self, value):
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        self.raise_type_error(value)

    def _serialize(self, value):
        return value.isoformat()


class Time(Field):
    value_type = time

    def _deserialize(self, value):
        if isinstance(value, str):
            return time.fromisoformat(value)
        elif isinstance(value, time):
            return value
        self.raise_type_error(value)

    def _serialize(self, value: time):
        return value.isoformat()


class Date(Field):
    value_type = date

    def _deserialize(self, value):
        if isinstance(value, str):
            return date.fromisoformat(value)
        elif isinstance(value, date):
            return value
        self.raise_type_error(value)

    def _serialize(self, value: date):
        return value.isoformat()


class Url(Field):
    value_type = yarl.URL

    def _deserialize(self, value):
        try:
            return yarl.URL(value)
        except TypeError:
            pass
        self.raise_type_error(value)

    def _serialize(self, value):
        return str(value)


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

    def _deserialize(self, value):
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


class List(Field):
    def __init__(self, instance: Field, *, allow_empty=False, **kwargs):
        kwargs['default'] = Nothing
        super().__init__(**kwargs)
        self.instance: Field = instance
        self.allow_empty = allow_empty

    def __get__(self, instance, owner):
        value = super().__get__(instance, owner)
        if value is not None:
            return tuple(value)

    def _deserialize(self, value):
        result = []
        for item in value:
            result.append(self.instance.deserialize(item))
        if not len(result) and not self.allow_empty:
            self.raise_type_error(value)
        return tuple(result)

    def _serialize(self, value):
        result = []
        for item in value:
            result.append(self.instance.serialize(item))
        return result


class Structure(Field):
    def __init__(self, structure: t.Type[DomainStructure], **kwargs):
        kwargs['default'] = Nothing
        super().__init__(**kwargs)
        self.structure = structure

    def _deserialize(self, value):
        if isinstance(value, DomainStructure):
            return value
        else:
            return self.structure.load(value)

    def _serialize(self, value: DomainStructure):
        return value.dump()
