import typing as t
import json
from uuid import UUID
import datetime as dt

from .core import Nothing
from ..exceptions import JsonDecodeError
from ..aggregate import BaseAggregate


class DDDResponse:

    def __init__(self, reference: UUID, *, aggregate_ref: UUID = None, aggregate: BaseAggregate = None):
        self._reference = reference
        self._timestamp = dt.datetime.now().timestamp()
        self._aggregator_ref = aggregate.reference if aggregate else aggregate_ref
        self._aggregate = aggregate

    @property
    def __domain__(self):
        return None

    @property
    def __reference__(self) -> UUID:
        """Идентификатор команды для которой предназначен ответ"""
        return self._reference

    @property
    def __timestamp__(self) -> float:
        return self._timestamp

    @property
    def aggregate_ref(self) -> UUID:
        """Идентификатор Агрегата"""
        return self._aggregator_ref

    @property
    def aggregate(self) -> t.Optional[BaseAggregate]:
        return self._aggregate

    @classmethod
    def load(cls, data: dict):
        aggregate_ref = UUID(data.get('data', {}).get('reference', Nothing))
        reference = UUID(data['__reference__'])
        obj = cls(reference, aggregate_ref=aggregate_ref)
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
            'data': {'reference': str(self.aggregate_ref)}
        }
        return result

    def dumps(self):
        data = self.dump()
        return json.dumps(data)

    def __eq__(self, other):
        return isinstance(other, DDDResponse) and hash(self) == hash(other)

    def __hash__(self):
        return hash(f'DDDResponse.{self.aggregate_ref}.'
                    f'{self.__reference__}.{self.__timestamp__}')
