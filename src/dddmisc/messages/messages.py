import datetime as dt
from uuid import uuid4

from dddmisc.messages.core import BaseDDDMessage, DDDMessageMeta


class DDDMessage(BaseDDDMessage, metaclass=DDDMessageMeta):
    from . import fields
    __reference__ = fields.Uuid(nullable=True)
    __timestamp__ = fields.Float(nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._reference = uuid4()
        self._timestamp = dt.datetime.now().timestamp()

    @property
    def __domain__(self) -> str:
        return self.__metadata__.domain

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


class DDDCommand(DDDMessage):
    pass


class DDDEvent(DDDMessage):
    pass
