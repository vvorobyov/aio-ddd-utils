import asyncio
import typing as t
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractExchange, AbstractQueue, AbstractRobustConnection, AbstractConnection, \
    AbstractIncomingMessage
from yarl import URL

from dddmisc.exceptions import BaseDomainError, InternalServiceError
from dddmisc.exceptions.errors import get_error_class, load_error
from dddmisc.messages import get_message_class, DomainEvent, DomainCommand, DomainCommandResponse
from dddmisc.messages.messages import DomainMessage
from dddmisc.messagebus.rabbitmq.abstract import AbstractRabbitDomainClient


class RabbitSelfDomainClient(AbstractRabbitDomainClient):
    _event_exchange: AbstractExchange
    _response_exchange: AbstractExchange
    _command_queue: AbstractQueue
    _command_consume_tag: str

    def __init__(self, url: t.Union[str, URL], self_domain: str, connected_domain: str, *args, **kwargs):
        super(RabbitSelfDomainClient, self).__init__(url, self_domain, self_domain, *args, **kwargs)

    async def handle_command(self, command: DomainCommand, timeout: float = None):
        raise NotImplementedError
        pass

    async def handle_event(self, event: DomainEvent):
        message = aio_pika.Message(event.dumps().encode(),
                                   user_id=self.self_domain, type='EVENT',
                                   message_id=str(event.__reference__))
        routing_key = f'{event.get_domain_name()}.{event.__class__.__name__}'

        result = await self._event_exchange.publish(message, routing_key)  # todo обработать ошибки отправки

    async def start(self):
        await super(RabbitSelfDomainClient, self).start()
        self._event_exchange = await self._setup_event_publisher()
        self._response_exchange = await self._setup_response_publisher()
        self._command_queue = await self._setup_command_consumer()
        self._command_consume_tag = await self._command_queue.consume(self._command_callback)

    async def stop(self, exception: BaseException = None):
        await self._command_queue.cancel(self._command_consume_tag)
        await super(RabbitSelfDomainClient, self).stop(exception)

    async def _setup_event_publisher(self) -> AbstractExchange:
        event_publisher_channel = await self._connection.channel()
        return await event_publisher_channel.declare_exchange('events', type='fanout', durable=True)

    async def _setup_response_publisher(self) -> AbstractExchange:
        response_publisher_channel = await self._connection.channel()
        return response_publisher_channel.default_exchange

    async def _setup_command_consumer(self) -> AbstractQueue:
        command_consumer_channel = await self._connection.channel(publisher_confirms=False)
        await command_consumer_channel.declare_exchange('commands', type='fanout', durable=True)
        await command_consumer_channel.set_qos(prefetch_count=self._prefetch_count)
        command_queue = await command_consumer_channel.declare_queue(
            'commands', durable=self._permanent_consume, auto_delete=not self._permanent_consume)
        for command in self._commands:
            await command_queue.bind('commands', f'{self.self_domain}.{command.__name__}')
        return command_queue

    async def _command_callback(self, message: AbstractIncomingMessage):
        """

        :param message:
        :return:
        """
        async with message.process():
            publisher = message.user_id
            message_class = get_message_class(message.routing_key)
            domain_message = message_class.loads(message.body.decode())
            if isinstance(domain_message, DomainCommand):
                try:
                    result = await self._callback(domain_message, publisher)
                except BaseDomainError as err:
                    result = err
                    result.set_command_context(domain_message)
                except Exception as err:  # TODO не происходит возврат сообщения при ошибке
                    result = InternalServiceError.from_exception(err)
                    result.set_command_context(domain_message)
                await self._publish_response(result, message.reply_to)

    async def _publish_response(self, response, reply_to):
        if isinstance(response, DomainCommandResponse):
            message_type = 'SUCCESS'
        else:
            message_type = 'ERROR'
        message = aio_pika.Message(response.dumps().encode(),
                                   user_id=self.self_domain, type=message_type,
                                   correlation_id=str(response.__reference__))

        # todo предусмотреть повторные попытки публикации сообщения на случай обрыва связи
        result = await self._response_exchange.publish(message, reply_to)


class RabbitOtherDomainClient(AbstractRabbitDomainClient):
    _event_queue: AbstractQueue
    _command_exchange: AbstractExchange
    _response_queue: AbstractQueue

    def __init__(self, *args, **kwargs):
        super(RabbitOtherDomainClient, self).__init__(*args, **kwargs)
        self._requests: dict[str, asyncio.Future] = {}

    async def start(self):
        await super(RabbitOtherDomainClient, self).start()
        self._event_queue = await self._setup_event_consumer()
        await self._event_queue.consume(self._event_callback)
        self._command_exchange = await self._setup_command_publisher()
        self._response_queue = await self._setup_response_consumer()
        await self._response_queue.consume(self._response_callback, no_ack=True)

    async def handle_command(self, command: DomainCommand, timeout: float = None) -> DomainCommandResponse:
        if isinstance(command, DomainCommand):
            msg = aio_pika.Message(command.dumps().encode(),
                                   user_id=self.self_domain,
                                   reply_to=self._response_queue.name,
                                   message_id=str(command.__reference__))
            routing_key = f'{command.get_domain_name()}.{command.__class__.__name__}'
            await self._command_exchange.publish(msg, routing_key)
            future = self._requests.setdefault(str(command.__reference__),
                                               self._loop.create_future())
            if timeout is None:
                return await future
            else:
                return await asyncio.wait_for(future, timeout=timeout)

    async def handle_event(self, event: DomainEvent):
        pass

    async def _setup_event_consumer(self) -> AbstractQueue:
        event_consume_channel = await self._connection.channel()

        await event_consume_channel.declare_exchange('events', type='fanout', durable=True)
        await event_consume_channel.set_qos(prefetch_count=self._prefetch_count)
        event_queue = await event_consume_channel.declare_queue(
            self.self_domain, durable=self._permanent_consume, auto_delete=not self._permanent_consume)
        for event in self._events:
            routing_key = f'{self.connected_domain}.{event.__name__}'
            await event_queue.bind('events', routing_key)
        return event_queue

    async def _setup_command_publisher(self) -> AbstractExchange:
        command_publish_channel = await self._connection.channel()
        command_exchange = await command_publish_channel.declare_exchange('commands', type='fanout', durable=True)
        return command_exchange

    async def _setup_response_consumer(self) -> AbstractQueue:
        response_consume_channel = await self._connection.channel()
        response_queue = await response_consume_channel.declare_queue(exclusive=True, auto_delete=True)
        return response_queue

    async def _response_callback(self, message: AbstractIncomingMessage):
        future = self._requests.pop(message.correlation_id, None)
        if future and not future.cancelled():
            if message.type == 'SUCCESS':
                result = DomainCommandResponse.loads(message.body.decode())
                future.set_result(result)
            else:
                result = load_error(message.body.decode())
                future.set_exception(result)

    async def _event_callback(self, message: AbstractIncomingMessage):
        async with message.process():
            if message.type == 'EVENT':
                event_class = get_message_class(message.routing_key)
                event = event_class.loads(data=message.body.decode())
                await self._callback(event, message.user_id)




