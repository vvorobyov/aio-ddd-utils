import abc
import typing as t

from marshmallow import Schema


class AbstractDomainMessage(abc.ABC):
    __schema__: Schema = Schema()
    __domain_name__: str
    __registered__: bool

    def __init__(self, **kwargs):
        pass
