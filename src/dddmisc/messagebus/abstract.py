import abc
import typing as t
from asyncio import AbstractEventLoop
from uuid import UUID

from dddmisc import DDDCommand
from dddmisc.aggregate import BaseAggregate
from dddmisc.messages import DDDResponse, DDDEvent

__all__ = ['AbstractSyncExternalMessageBus', 'AbstractAsyncExternalMessageBus']


class AbstractAsyncExternalMessageBus(abc.ABC):
    _loop: AbstractEventLoop

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    def set_loop(self, loop: AbstractEventLoop):
        if not hasattr(self, '_loop'):
            self._loop = loop
        else:
            raise RuntimeError('loop is already set')

    @t.overload
    async def handle(self, message: DDDCommand, timeout: float = None) -> DDDResponse:
        ...

    @t.overload
    async def handle(self, message: DDDEvent, timeout: float = None) -> t.NoReturn:
        ...

    @abc.abstractmethod
    async def handle(self, message, timeout=None):
        ...

    @abc.abstractmethod
    async def start(self):
        ...

    @abc.abstractmethod
    async def stop(self, exception: Exception = None):
        ...


class AbstractSyncExternalMessageBus(abc.ABC):

    @t.overload
    def handle(self, message: DDDCommand, timeout: float = None) -> DDDResponse: ...

    @t.overload
    def handle(self, message: DDDEvent, timeout: float = None) -> t.NoReturn: ...

    @abc.abstractmethod
    def handle(self, message, timeout=None):
        ...

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self, exception: Exception = None):
        ...


A = t.TypeVar('A', bound=BaseAggregate)
T = t.TypeVar('T')


class AbstractRepository(abc.ABC, t.Generic[A, T]):
    aggregate_class: t.Type[A]

    def __init__(self, connection: T):
        self._seen: set[A] = set()
        self._connection = connection
        self.events = set()

    @t.final
    def add(self, aggregate: A):
        if not isinstance(aggregate, self.aggregate_class):
            raise TypeError(fr'aggregate required be is instance of {self.aggregate_class!r}')
        if self._get_from_cache(aggregate.reference) is None:
            self._seen.add(aggregate)
        else:
            raise RuntimeError(f'aggregate {aggregate.reference} is exist')

    @t.final
    def _get_from_cache(self, reference: UUID) -> t.Optional[A]:
        return next((aggregate for aggregate in self._seen
                     if aggregate.reference == reference), None)

    @t.final
    def _collect_events(self):
        for aggregate in self._seen:
            self.events.update(aggregate.get_aggregate_events())

    @t.final
    def clear_events(self):
        self._collect_events()
        self.events.clear()


class AbstractAsyncRepository(AbstractRepository[A, T], abc.ABC):

    @abc.abstractmethod
    async def _add_to_storage(self, aggregate: A):
        ...

    @t.final
    async def get(self, reference: UUID) -> A:
        aggregate = self._get_from_cache(reference)
        if aggregate:
            return aggregate
        return await self._get_from_storage(reference)

    @abc.abstractmethod
    async def _get_from_storage(self, reference: UUID) -> A:
        ...

    @t.final
    async def apply_changes(self):
        for aggregate in self._seen:
            await self._add_to_storage(aggregate)
        self._collect_events()


class AbstractSyncRepository(AbstractRepository[A, T], abc.ABC):

    @abc.abstractmethod
    def _add_to_storage(self, aggregate: A):
        ...

    @t.final
    def get(self, reference: UUID) -> A:
        aggregate = self._get_from_cache(reference)
        if aggregate:
            return aggregate
        return self._get_from_storage(reference)

    @abc.abstractmethod
    def _get_from_storage(self, reference: UUID) -> A:
        ...

    @t.final
    def apply_changes(self):
        for aggregate in self._seen:
            self._add_to_storage(aggregate)
        self._collect_events()


R = t.TypeVar('R', bound=t.Union[AbstractSyncRepository, AbstractAsyncRepository])


class AbstractUnitOfWork(t.Generic[R, T]):
    repository_class: t.Type[R]
    _repository: R

    def __init__(self, engine: t.Any = None,
                 *, repository_class: t.Type[R] = None):
        self._engine = engine
        self._events: set[DDDEvent] = set()
        self._current_transaction_events: set[DDDEvent] = set()
        self._in_context = False
        self._repository_class = repository_class or type(self).repository_class
        self._transaction: T = None

    @property
    def repository(self) -> R:
        if hasattr(self, '_repository'):
            return self._repository
        else:
            raise RuntimeError('Need enter to UnitOfWork context manager before access to "repository"')

    @t.final
    def collect_events(self) -> tuple[DDDEvent]:
        """Отдаем все накопленные события"""
        events = tuple(sorted(self._events, key=lambda x: x.__timestamp__))
        self._events.clear()
        return events

    @t.final
    def _post_commit(self):
        """Добавляем события репозитория в набор событий по транзакции"""
        self._current_transaction_events.update(self.repository.events)
        self.repository.clear_events()
        delattr(self, '_repository')

    @t.final
    def _post_rollback(self):
        """Очищаем текущие события репозитория"""
        if hasattr(self, '_repository'):
            self.repository.clear_events()
            delattr(self, '_repository')

    def __enter__(self):
        if self._in_context:
            raise RuntimeError("Double enter to UnitOfWork's context manager")
        self._repository = self.repository_class(self._transaction)
        self._current_transaction_events.clear()
        self._in_context = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._events.update(self._current_transaction_events)
        self._current_transaction_events.clear()
        self._in_context = False


class AbstractAsyncUnitOfWork(AbstractUnitOfWork[R, T]):

    @t.final
    async def __aenter__(self):
        self._current_transaction_events.clear()
        self._transaction = await self._begin_transaction(self._engine)
        self.__enter__()

    @t.final
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()
        self.__exit__(exc_type, exc_val, exc_tb)

    @t.final
    async def commit(self):
        await self.repository.apply_changes()
        await self._commit_transaction(self._transaction)
        self._post_commit()

    @t.final
    async def rollback(self):
        await self._rollback_transaction(self._transaction)
        self._post_rollback()

    @abc.abstractmethod
    async def _begin_transaction(self, factory: t.Any) -> T:
        ...

    @abc.abstractmethod
    async def _commit_transaction(self, transaction: T):
        ...

    @abc.abstractmethod
    async def _rollback_transaction(self, transaction: T):
        ...


class AbstractSyncUnitOfWork(AbstractUnitOfWork[R, T]):

    @t.final
    def __enter__(self):
        self._transaction = self._begin_transaction(self._engine)
        super(AbstractSyncUnitOfWork, self).__enter__()

    @t.final
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()
        super(AbstractSyncUnitOfWork, self).__exit__(exc_type, exc_val, exc_tb)

    @t.final
    def commit(self):
        self.repository.apply_changes()
        self._commit_transaction(self._transaction)
        self._post_commit()

    @t.final
    def rollback(self):
        self._rollback_transaction(self._transaction)
        self._post_rollback()

    @abc.abstractmethod
    def _begin_transaction(self, factory: t.Any) -> T:
        ...

    @abc.abstractmethod
    def _commit_transaction(self, transaction: T):
        ...

    @abc.abstractmethod
    def _rollback_transaction(self, transaction: T):
        ...

