import asyncio
import typing as t
import abc
from asyncio import AbstractEventLoop

from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractConnection, AbstractMessage, AbstractIncomingMessage
from yarl import URL


from dddmisc.exceptions.core import DDDException
from dddmisc.messages.messages import DomainMessage
from dddmisc.messages import DomainEvent, DomainCommand, DomainCommandResponse

from . import exceptions, utils

PublisherName = str
ExecutorType = t.Callable[[DomainMessage, PublisherName], t.Awaitable[t.Optional[DomainCommandResponse]]]


class AbstractRabbitDomainClient(abc.ABC):
    __PARSE_METHODS = {
        'COMMAND': utils.parse_command,
        'EVENT': utils.parse_event,
        'RESPONSE': utils.parse_response,
        'ERROR': utils.parse_error
    }
    _connection: AbstractConnection

    def __init__(self, url: t.Union[str, URL],
                 self_domain: str, connected_domain: str,
                 events: t.Iterable[t.Type[DomainEvent]], commands: t.Iterable[t.Type[DomainCommand]],
                 executor: ExecutorType,
                 *, permanent_consume=True, prefetch_count=0,
                 loop: AbstractEventLoop = None):
        self._base_url = URL(url).with_path('').with_user(self_domain)
        self._self_domain = self_domain
        self._executor = executor
        self._connected_domain = connected_domain
        self._permanent_consume = permanent_consume
        self._prefetch_count = prefetch_count
        self._events = tuple(events)
        self._commands = tuple(commands)
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

    @classmethod
    def parse_message(cls, message: AbstractIncomingMessage):
        message_type = message.type.upper() if message.type else None
        if message_type not in ['COMMAND', 'EVENT', 'RESPONSE', 'ERROR']:
            raise exceptions.UnknownMessageTypeError(message_type=message_type)
        return cls.__PARSE_METHODS[message_type](message)

    def create_message(self, message, reply_to: str = None) -> AbstractMessage:
        user_id = self.self_domain
        message_id = None
        correlation_id = None
        headers = {}
        body = message.dumps().encode()
        if isinstance(message, DomainMessage):
            message_id = str(message.__reference__)
            headers['X-DDD-OBJECT-KEY'] = f'{message.get_domain_name()}.{message.__class__.__name__}'
            type_ = 'COMMAND' if isinstance(message, DomainCommand) else 'EVENT'
        elif isinstance(message, DDDException):
            correlation_id = message.__reference__
            headers['X-DDD-OBJECT-KEY'] = f'{message.__domain__}.{message.__class__.__name__}'
            type_ = 'ERROR'
        elif isinstance(message, DomainCommandResponse):
            correlation_id = message.__reference__
            type_ = 'RESPONSE'
        else:
            raise TypeError(f'Unknown message type "{type(message)}"')

        message = Message(body, user_id=user_id, type=type_, message_id=message_id, correlation_id=correlation_id,
                          headers=headers, reply_to=reply_to)
        return message
