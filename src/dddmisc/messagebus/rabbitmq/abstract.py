import asyncio
import typing as t
import abc
from asyncio import AbstractEventLoop

from aio_pika import connect_robust
from aio_pika.abc import AbstractConnection
from yarl import URL

from dddmisc.messages.messages import DomainMessage
from dddmisc.messages import DomainEvent, DomainCommand, DomainCommandResponse


PublisherName = str
CallbackType = t.Callable[[DomainMessage, PublisherName], t.Awaitable[t.Optional[DomainCommandResponse]]]


class AbstractRabbitDomainClient(abc.ABC):
    _connection: AbstractConnection

    def __init__(self, url: t.Union[str, URL],
                 self_domain: str, connected_domain: str,
                 events: t.Iterable[t.Type[DomainEvent]], commands: t.Iterable[t.Type[DomainCommand]],
                 callback: CallbackType,
                 *, permanent_consume=True, prefetch_count=0,
                 loop: AbstractEventLoop = None):
        self._base_url = URL(url).with_path('')
        self._self_domain = self_domain
        self._callback = callback
        self._connected_domain = connected_domain
        self._permanent_consume = permanent_consume
        self._prefetch_count = prefetch_count
        self._events = events
        self._commands = commands
        self._loop = loop or asyncio.get_event_loop()

    @property
    def self_domain(self) -> str:
        return self._self_domain

    @property
    def connected_domain(self) -> str:
        return self._connected_domain

    @abc.abstractmethod
    async def handle_command(self, command: DomainCommand, timeout: float = None):
        pass

    @abc.abstractmethod
    async def handle_event(self, event: DomainEvent):
        pass

    async def start(self):
        url = self._base_url.with_path(self.connected_domain)
        self._connection = await connect_robust(url)

    async def stop(self, exception: BaseException = None):
        await self._connection.close(exception)
