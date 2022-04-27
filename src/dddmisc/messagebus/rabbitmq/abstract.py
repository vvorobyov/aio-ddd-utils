import asyncio
import typing as t
import abc
from asyncio import AbstractEventLoop

from aio_pika import connect_robust
from aio_pika.abc import AbstractConnection
from yarl import URL

from dddmisc.domain_message.messages import BaseMessage
from ...domain_message import Event, Command, AbstractDomainMessage


PublisherName = str
CallbackType = t.Callable[[AbstractDomainMessage, PublisherName], t.Awaitable[t.Optional[object]]]


class AbstractRabbitDomainClient(abc.ABC):
    _connection: AbstractConnection

    def __init__(self, url: t.Union[str, URL],
                 self_domain: str, connected_domain: str,
                 events: t.Iterable[t.Type[Event]], commands: t.Iterable[t.Type[Command]],
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
    async def handle(self, message: BaseMessage):
        pass

    async def start(self):
        url = self._base_url.with_path(self.connected_domain)
        self._connection = await connect_robust(url)

    async def stop(self, exception: BaseException = None):
        await self._connection.close(exception)
