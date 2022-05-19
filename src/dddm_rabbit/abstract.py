import asyncio
import typing as t
import abc
from asyncio import AbstractEventLoop
from types import MappingProxyType

from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractConnection, AbstractMessage, AbstractIncomingMessage
from yarl import URL

from dddmisc.abstract import CrossDomainObjectProtocol
from dddmisc.exceptions.core import DDDException
from dddmisc.messages.messages import DDDMessage
from dddmisc.messages import DDDEvent, DDDCommand, DDDResponse

from . import exceptions, utils

PublisherName = str
ExecutorType = t.Callable[[DDDMessage, PublisherName], t.Awaitable[t.Optional[DDDResponse]]]


class AbstractRabbitDomainClient(abc.ABC):
    __PARSE_METHODS = MappingProxyType({
        'COMMAND': utils.parse_command,
        'EVENT': utils.parse_event,
        'RESPONSE': utils.parse_response,
        'ERROR': utils.parse_error
    })

    _connection: AbstractConnection

    def __init__(self, url: t.Union[str, URL],
                 self_domain: str, connected_domain: str,
                 events: t.Iterable[t.Type[DDDEvent]], commands: t.Iterable[t.Type[DDDCommand]],
                 executor: ExecutorType,
                 *, permanent_consume=True, prefetch_count=0,
                 loop: AbstractEventLoop = None):
        """
        Клиент подключения к RabbitMQ. Клиент самостоятельно создает подключения. Необходимые queues и exchanges.
        Осуществляет настройку bindings и подписку на сообщения
        Args:
            url (str): Базовый URL для подключения к RabbitMQ. Пример amqps://guest:guest@localhost. Заданный vhost будет проигнорирован
            self_domain (str): Наименование основного домена сервиса
            connected_domain (str): Наименование домена, с которым будет осуществлять взаимодействие
            events (t.Iterable[t.Type[DDDEvent]]): Перечень событий, на которые будет осуществлена подписка/публикация клиентом
            commands (t.Iterable[t.Type[DDDCommand]]): Перечень команд, на которые будет осуществлена подписка/публикация клиентом
            executor (ExecutorType): Функция обработчик полученных команд/событий
            permanent_consume (bool, optional): Подписка с использование постоянной очереди. False будет использована временная очередь.
            prefetch_count (int, optional): Количество сообщений одновременно обрабатываемых клиентом. По умолчанию не ограничено.
            loop (AbstractEventLoop): EventLoop в котором будет работать клиент
        """
        self._self_domain = self_domain
        self._executor = executor
        self._connected_domain = connected_domain
        self._base_url = URL(url).with_path(self.connected_domain).with_user(self_domain)

        self._permanent_consume = permanent_consume
        self._prefetch_count = prefetch_count
        self._events = tuple(events)
        self._commands = tuple(commands)
        self._loop = loop or asyncio.get_event_loop()

    @property
    def self_domain(self) -> str:
        """Наименование домена, с которым будет осуществлять взаимодействие"""
        return self._self_domain

    @property
    def connected_domain(self) -> str:
        """Наименование домена, с которым будет осуществлять взаимодействие"""
        return self._connected_domain

    @abc.abstractmethod
    async def handle_command(self, command: DDDCommand, timeout: float = None) -> DDDResponse:
        """
        Метод публикации команды
        Args:
            command (DDDCommand): Команда для отправки удаленному сервису
            timeout (float, optional): Максимальное время ожидания ответа от сервиса. По умолчанию без ограничения

        Returns:
            DDDResponse: ответ сервиса
        """
        pass

    @abc.abstractmethod
    async def handle_event(self, event: DDDEvent):
        """
        Метод публикации события
        Args:
            event (DDDEvent): Публикуемое событие
        """
        pass

    async def start(self):
        """
        Метод запуска клиента
        """
        url = self._base_url.with_path(self.connected_domain)
        self._connection = await connect_robust(url)

    async def stop(self, exception: Exception = None):
        """
        Метод остановки клиента
        Args:
            exception (Exception): Исключение являющееся причиной остановки

        Returns:

        """
        await self._connection.close(exception)

    @classmethod
    def parse_message(cls, message: AbstractIncomingMessage):
        """
        Метод десериализации сообщения в объект пакета
        Args:
            message (AbstractIncomingMessage): Входящее сообщение RabbitMQ

        Returns:
            Union[DDDCommand, DDDEvent, DDDResponse, DDDException]: Десериализованный объект
        """
        message_type = message.type.upper() if message.type else None
        if message_type not in ['COMMAND', 'EVENT', 'RESPONSE', 'ERROR']:
            raise exceptions.UnknownMessageTypeError(message_type=message_type)
        return cls.__PARSE_METHODS[message_type](message)

    def create_message(self, message: CrossDomainObjectProtocol, reply_to: str = None) -> AbstractMessage:
        """
        Метод сериализации объекта в сообщение RabbitMQ
        Args:
            message (Union[DDDCommand, DDDEvent, DDDResponse, DDDException]): Объект домена для сериализации
            reply_to (str): Очередь для получения ответа на комманду

        Returns:
            AbstractMessage - класс сообщения RabbitMQ
        """

        user_id = self.self_domain
        message_id = correlation_id = str(message.__reference__)
        headers = {}
        reply_to_ = None
        body = message.dumps().encode()
        headers['X-DDD-OBJECT-KEY'] = f'{message.__domain__}.{message.__class__.__name__}'
        if isinstance(message, DDDMessage):
            type_, reply_to_ = ('COMMAND', reply_to) if isinstance(message, DDDCommand) else ('EVENT', None)
        elif isinstance(message, DDDException):
            type_ = 'ERROR'
        elif isinstance(message, DDDResponse):
            type_ = 'RESPONSE'
        else:
            raise TypeError(f'Unknown message type "{type(message)}"')

        message = Message(body, user_id=user_id, type=type_, message_id=message_id, correlation_id=correlation_id,
                          headers=headers, reply_to=reply_to_)
        return message
