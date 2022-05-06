from uuid import uuid4
import typing as t
import datetime as dt

from .core import BaseDomainMessage, DomainMessageMeta
from . import fields


class DomainMessage(BaseDomainMessage, metaclass=DomainMessageMeta):
    __reference__ = fields.Uuid(nullable=True)
    __timestamp__ = fields.Float(nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reference = uuid4()
        self._timestamp = dt.datetime.now().timestamp()

    def get_attr(self, item: str):
        if item == '__reference__':
            return self._reference
        elif item == '__timestamp__':
            return self._timestamp
        else:
            return super().get_attr(item)

    @classmethod
    def get_domain_name(cls) -> str:
        return cls.__metadata__.domain

    @classmethod
    def load(cls, data):
        obj = super().load(data.get('data', {}))
        if ref_value := data.get('__reference__', None):
            obj._reference = cls.__metadata__.fields['__reference__'].deserialize(ref_value)
        if ts_value := data.get('__timestamp__', None):
            obj._timestamp = cls.__metadata__.fields['__timestamp__'].deserialize(ts_value)
        return obj

    def dump(self):
        result = {
            '__reference__': self.__metadata__.fields['__reference__'].serialize(self._reference),
            '__timestamp__': self.__metadata__.fields['__timestamp__'].serialize(self._timestamp),
            'data': super().dump()}
        return result


class DomainCommand(DomainMessage):
    pass


class DomainEvent(DomainMessage):
    pass


def get_message_class(key: t.Union[t.Tuple[str, str], str]) -> t.Type[DomainMessage]:
    if isinstance(key, str):
        domain, name = key.split('.')
        key_ = (domain, name)
    else:
        key_ = key
    collection = DomainMessageMeta.get_message_collection()
    if key_ in collection:
        return collection[key_]
    raise RuntimeError(f"Message class by '{key}' not found")
