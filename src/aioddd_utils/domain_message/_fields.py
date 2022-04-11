import decimal
import typing as t
import uuid
from datetime import datetime, time, date

import attr
from attr import NOTHING
from marshmallow import fields as mf, utils as mu


class Field:
    __marshmallow_field__: t.Type[mf.Field]

    def __init__(self,
                 *,
                 default=NOTHING,
                 validate: t.Optional[
                     t.Union[t.Callable[[t.Any], t.Any],
                             t.Iterable[t.Callable[[t.Any], t.Any]]]
                 ] = None,
                 data_key: t.Optional[str] = None,
                 error_messages: t.Optional[dict[str, str]] = None,
                 **kwargs):
        self._validate = validate
        self._default = default
        self._error_messages = error_messages
        self._data_key = data_key

    def __get__(self, instance, owner):
        pass

    def get_attrib(self):
        params = dict(
            default=self._default,
            validator=None,
            repr=True,
            cmp=None,
            hash=None,
            init=True,
            metadata=None,
            type=None,
            converter=None,
            factory=None,
            kw_only=True,
            eq=None,
            order=None,
            on_setattr=None,
        )
        return attr.ib(**params)

    def get_marshmallow_field(self) -> t.Optional[mf.Field]:
        params = dict(
            dump_default=mu.missing,
            load_default=(mu.missing if self._default is NOTHING else self._default),
            data_key=self._data_key,
            validate=self._validate,
            allow_none=self._default is None,
            required=True,
            error_messages=self._error_messages,
            **self._get_extra_marshmallow_params()
        )
        field_class = getattr(mf, type(self).__name__)
        return field_class(**params)

    def _get_extra_marshmallow_params(self) -> dict:
        return {}


class String(Field):
    ...


class UUID(Field):
    ...


class _Number(Field):

    def __init__(self, *, as_string: bool = False, **kwargs):
        self._as_string = as_string
        super().__init__(**kwargs)

    def _get_extra_marshmallow_params(self) -> dict:
        params = super()._get_extra_marshmallow_params()
        params['as_string'] = self._as_string
        return params


class Integer(_Number):

    def __init__(self, *, strict: bool = False, **kwargs):
        self._strict = strict
        super().__init__(**kwargs)

    def _get_extra_marshmallow_params(self) -> dict:
        params = super()._get_extra_marshmallow_params()
        params['strict'] = self._strict
        return params


class Float(Field):

    def __init__(self, *, allow_nan: bool = False, **kwargs):
        self._allow_nan = allow_nan
        super().__init__(**kwargs)

    def _get_extra_marshmallow_params(self) -> dict:
        params = super()._get_extra_marshmallow_params()
        params['allow_nan'] = self._allow_nan
        return params


class Decimal(_Number):

    def __init__(self, places: t.Optional[int] = None, rounding: t.Optional[str] = None, **kwargs):
        self._places = places
        self._rounding = rounding
        super().__init__(**kwargs)

    def _get_extra_marshmallow_params(self) -> dict:
        params = super()._get_extra_marshmallow_params()
        params['places'] = self._places
        params['rounding'] = self._rounding
        return params


class Boolean(Field):

    def __init__(self, *,
                 truthy: t.Optional[set] = None,
                 falsy: t.Optional[set] = None,
                 **kwargs):
        self._truthy = truthy
        self._falsy = falsy
        super().__init__(**kwargs)

    def _get_extra_marshmallow_params(self) -> dict:
        params = super()._get_extra_marshmallow_params()
        params['truthy'] = self._truthy
        params['falsy'] = self._falsy
        return params


class DateTime(Field):  # TODO NaiveDateTime, AwareDateTime

    def __init__(self, format: t.Optional[str] = None, **kwargs):
        self._format = format
        super(DateTime, self).__init__(**kwargs)

    def _get_extra_marshmallow_params(self) -> dict:
        params = super()._get_extra_marshmallow_params()
        params['format'] = self._format
        return params


class Time(DateTime):
    ...


class Date(DateTime):
    ...


class URL(String):

    def __init__(self, *, relative: bool = False,
                 schemes=t.Union[t.Sequence[str], t.Set[str]],
                 require_tld: bool = True, **kwargs
                 ):
        self._relative = relative
        self._schemes = schemes
        self._require_tld = require_tld
        super(URL, self).__init__(**kwargs)


class Email(String):
    pass


# TODO class Nested(Field)
# TODO class List(Field)


