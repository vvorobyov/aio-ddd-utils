import json
import typing as t
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .core import DomainMessageMeta, AbstractDomainMessage, Nothing
from . import fields


_T = t.TypeVar('_T')


class DomainMessage(metaclass=DomainMessageMeta):
    __reference__ = fields.Uuid()
    __timestamp__ = fields.Float()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__data__['__reference__'] = uuid4()
        self.__data__['__timestamp__'] = datetime.now().timestamp()

    @classmethod
    @t.final
    def load(cls: t.Type[_T], data: dict) -> _T:
        obj: AbstractDomainMessage = super().load(data.get('data', {}))
        ref_value = data.get('__reference__', Nothing)
        obj.__data__['__reference__'] = cls.__metadata__.fields['__reference__'].validate_value_type(ref_value)
        ts_value = data.get('__timestamp__', Nothing)
        obj.__data__['__timestamp__'] = cls.__metadata__.fields['__timestamp__'].validate_value_type(ts_value)
        return obj

    @classmethod
    @t.final
    def loads(cls: t.Type[_T], data: str) -> _T:
        dict_data = json.loads(data)
        return cls.load(dict_data)

    @t.final
    def dump(self) -> dict:
        return super().dump()

    @t.final
    def dumps(self) -> str:
        data = self.dump()
        return json.dumps(data)


class DomainCommand(DomainMessage):
    pass


class DomainEvent(DomainMessage):
    pass




