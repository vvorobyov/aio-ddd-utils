import asyncio
import typing as t
from collections import defaultdict

from aio_pika.abc import AbstractExchange, AbstractQueue, AbstractIncomingMessage
from yarl import URL

from dddm_rabbit.exceptions import IncomingMessageError
from dddmisc.exceptions import BaseDomainError
from dddmisc.exceptions.errors import BaseServiceError
from dddmisc.messages import get_message_class, DomainEvent, DomainCommand, DomainCommandResponse
from dddm_rabbit.abstract import AbstractRabbitDomainClient


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

    async def start(self):
        await super(RabbitSelfDomainClient, self).start()
        self._event_exchange = await self._setup_event_publisher()
        self._response_exchange = await self._setup_response_publisher()
        self._command_queue = await self._setup_command_consumer()
        self._command_consume_tag = await self._command_queue.consume(self._command_handler)

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

    async def handle_event(self, event: DomainEvent):
        message = self.create_message(event)
        routing_key = f'{event.get_domain_name()}.{event.__class__.__name__}'
        result = await self._event_exchange.publish(message, routing_key)  # todo обработать ошибки отправки

    async def _command_handler(self, message: AbstractIncomingMessage):
        """

        :param message:
        :return:
        """
        async with message.process():
            publisher = message.user_id
            try:
                domain_message = self.parse_message(message)
                result = await self._executor(domain_message, publisher)
            except (BaseServiceError, BaseDomainError, IncomingMessageError) as err:
                result = err
                result._reference = message.message_id
            except Exception:
                # TODO добавить в логирование ошибки
                raise

            response = self.create_message(result)
            await self._response_exchange.publish(response, message.reply_to)


class RabbitOtherDomainClient(AbstractRabbitDomainClient):
    _event_queue: AbstractQueue
    _command_exchange: AbstractExchange
    _response_queue: AbstractQueue

    def __init__(self, *args, **kwargs):
        super(RabbitOtherDomainClient, self).__init__(*args, **kwargs)
        self._requests: dict[str, asyncio.Future] = defaultdict(self._loop.create_future)

    async def start(self):
        await super(RabbitOtherDomainClient, self).start()
        self._event_queue = await self._setup_event_consumer()
        await self._event_queue.consume(self._event_handler)
        self._command_exchange = await self._setup_command_publisher()
        self._response_queue = await self._setup_response_consumer()
        await self._response_queue.consume(self._response_handler, no_ack=True)

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

    async def handle_command(self, command: DomainCommand, timeout: float = None) -> DomainCommandResponse:
        msg = self.create_message(command, self._response_queue.name)
        routing_key = f'{command.get_domain_name()}.{command.__class__.__name__}'
        await self._command_exchange.publish(msg, routing_key)

        future = self._requests[str(command.__reference__)]
        result = await asyncio.wait_for(future, timeout=timeout)

        if isinstance(result, BaseException):
            raise result
        else:
            return result

    async def handle_event(self, event: DomainEvent):
        pass

    async def _response_handler(self, message: AbstractIncomingMessage):
        future = self._requests.pop(message.correlation_id, None)
        if future and not future.cancelled():
            try:
                result = self.parse_message(message)
                future.set_result(result)
            except IncomingMessageError as err:
                future.set_exception(err)
            except Exception as err:
                # TODO добавить логирование не известной ошибки
                future.set_exception(err)

    async def _event_handler(self, message: AbstractIncomingMessage):
        async with message.process():
            if message.type == 'EVENT':
                event_class = get_message_class(message.routing_key)
                event = event_class.loads(data=message.body.decode())
                await self._executor(event, message.user_id)




