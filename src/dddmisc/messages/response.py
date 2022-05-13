import json
from uuid import UUID
import datetime as dt

from .core import Nothing
from ..exceptions import JsonDecodeError


class DomainCommandResponse:

    def __init__(self, aggregator_ref: UUID, command_ref: UUID):
        self._command_ref = command_ref
        self._timestamp = dt.datetime.now().timestamp()
        self._aggregator_ref = aggregator_ref

    @property
    def __reference__(self) -> UUID:
        """Идентификатор команды для которой предназначен ответ"""
        return self._command_ref

    @property
    def reference(self) -> UUID:
        """Идентификатор """
        return self._aggregator_ref

    @property
    def __timestamp__(self) -> float:
        return self._timestamp

    @classmethod
    def load(cls, data: dict):
        aggr_ref = UUID(data.get('data', {}).get('reference', Nothing))
        command_ref = UUID(data['__reference__'])
        obj = cls(aggr_ref, command_ref)
        if ref_value := data.get('__reference__', None):
            obj._reference = UUID(ref_value)
        if ts_value := data.get('__timestamp__', None):
            obj._timestamp = ts_value
        return obj

    @classmethod
    def loads(cls, data):
        try:
            dict_data = json.loads(data)
            return cls.load(dict_data)
        except json.JSONDecodeError as err:
            raise JsonDecodeError(str(err))

    def dump(self):
        result = {
            '__reference__': str(self.__reference__),
            '__timestamp__': self.__timestamp__,
            'data': {'reference': str(self.reference)}
        }
        return result

    def dumps(self):
        data = self.dump()
        return json.dumps(data)

    def __eq__(self, other):
        return (isinstance(other, DomainCommandResponse)
                and self.__reference__ == other.__reference__
                and self.__timestamp__ == other.__timestamp__
                and self.__reference__ == other.__reference__)

    def __hash__(self):
        return hash(f'{self.__class__.__name__}.{self.reference}.'
                    f'{self.__reference__}.{self.__timestamp__}')