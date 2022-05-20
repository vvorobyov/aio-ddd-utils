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
        self._commit = False

    @t.final
    def add(self, aggregate: A):
        if not isinstance(aggregate, self.aggregate_class):
            raise TypeError(fr'aggregate required be is instance of {self.aggregate_class!r}')
        if self._get_from_cache(aggregate.reference) is None:
            self._seen.add(aggregate)
        else:
            raise RuntimeError(f'aggregate {aggregate.reference} is exist')
        self._commit = False

    @t.final
    def _get_from_cache(self, reference: UUID) -> t.Optional[A]:
        return next((aggregate for aggregate in self._seen
                     if aggregate.reference == reference), None)

    @t.final
    def collect_events(self) -> t.Iterable[DDDEvent]:
        if not self._commit:
            return ()
        events: set[DDDEvent] = set()
        for aggregate in self._seen:
            events.update(aggregate.get_aggregate_events())
        return events


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
        self._commit = True


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
        self._commit = True


class AbstractUnitOfWork(t.Generic[A, T]):
    repository_class: t.Type[AbstractRepository[A, T]]
    _repository: AbstractRepository[A, T]

    def __init__(self, engine: t.Any = None):
        self._engine = engine
        self._events: set[DDDEvent] = set()
        self._current_transaction_events: set[DDDEvent] = set()
        self._in_context = False

        self._repository_class = type(self.repository_class)
        self._transaction: T = None

    @property
    def repository(self):
        if hasattr(self, 'repository'):
            return self._repository
        else:
            raise RuntimeError('Need enter to unit of worc context manager before access to "repository"')

    def collect_events(self) -> tuple[DDDEvent]:
        """Отдаем все накопленные события"""
        events = tuple(sorted(self._events, key=lambda x: x.__timestamp__))
        self._events.clear()
        return events

    def _post_commit(self):
        """Добавляем события репозитория в набор событий по транзакции"""
        self._current_transaction_events.update(self.repository.collect_events())
        delattr(self, 'repository')

    def _post_rollback(self):
        """Очищаем текущие события репозитория"""
        self.repository.collect_events()
        delattr(self, 'repository')

    def __enter__(self):
        if hasattr(self, '_repository'):
            raise RuntimeError("Double enter to UnitOfWork's context manager")
        self._repository = self.repository_class(self._transaction)
        self._current_transaction_events.clear()
        self._in_context = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._events.update(self._current_transaction_events)
        self._in_context = False


class AbstractAsyncUnitOfWork(AbstractUnitOfWork[A, T]):
    repository_class: t.Type[AbstractAsyncRepository[A, T]]
    repository: AbstractAsyncRepository[A, T]

    async def __aenter__(self):
        self._current_transaction_events.clear()
        self._transaction = await self._begin_transaction(self._engine)
        self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()
        self.__exit__(exc_type, exc_val, exc_tb)

    async def commit(self):
        await self.repository.apply_changes()
        await self._commit_transaction(self._transaction)
        self._post_commit()

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


class AbstractSyncUnitOfWork(AbstractUnitOfWork[A, T]):
    
    repository_class: t.Type[AbstractSyncRepository[A, T]]
    repository: AbstractSyncRepository[A, T]

    def __enter__(self):
        self._transaction = self._begin_transaction(self._engine)
        super(AbstractSyncUnitOfWork, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()
        super(AbstractSyncUnitOfWork, self).__exit__(exc_type, exc_val, exc_tb)

    def commit(self):
        self.repository.apply_changes()
        self._commit_transaction(self._transaction)
        self._post_commit()

    async def rollback(self):
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

