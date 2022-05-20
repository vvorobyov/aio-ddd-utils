import abc
import typing as t
from uuid import uuid4, UUID

from dddmisc.messages import DDDEvent


class BaseAggregate(abc.ABC):

    def __init__(self, *, reference=None):
        self._reference = reference or uuid4()
        self._events = set()

    @property
    def reference(self) -> UUID:
        return self._reference

    @t.final
    def add_aggregate_event(self, event: DDDEvent):
        self._events.add(event)

    @t.final
    def get_aggregate_events(self) -> t.Iterable[DDDEvent]:
        events = tuple(self._events)
        self._events.clear()
        return events

    def __eq__(self, other):
        return isinstance(other, type(self)) and self._reference == other.reference

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return self._reference > other.reference

    def __lt__(self, other):
        return self._reference < other.reference

    def __hash__(self):
        return hash(self.reference)
