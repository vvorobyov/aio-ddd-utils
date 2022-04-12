import abc
import typing as t

from marshmallow import Schema


class AbstractDomainMessage(abc.ABC):
    __schema__: Schema = Schema()

    def __init__(self, **kwargs):
        pass
