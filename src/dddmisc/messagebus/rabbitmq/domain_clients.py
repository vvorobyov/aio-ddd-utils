import typing as t

from aio_pika.abc import AbstractExchange, AbstractQueue, AbstractRobustConnection, AbstractConnection, \
    AbstractIncomingMessage
from dddmisc.domain_message.messages import BaseMessage
from dddmisc.messagebus.rabbitmq.abstract import AbstractRabbitDomainClient


class RabbitSelfDomainClient(AbstractRabbitDomainClient):
    async def handle(self, message: BaseMessage):
        pass

    _event_exchange: AbstractExchange
    _response_exchange: AbstractExchange
    _command_queue: AbstractQueue

    def __init__(self, connection: AbstractRobustConnection,
                 self_domain: str, connected_domain: str = None,
                 permanent_consume=True, prefetch_count=0):
        super(RabbitSelfDomainClient, self).__init__(connection, self_domain, self_domain, permanent_consume,
                                                   prefetch_count)

    async def start(self):
        self._event_exchange = await self._setup_event_publisher(self._connection)
        self._response_exchange = await self._setup_response_publisher(self._connection)
        await self._setup_command_consumer(self._connection, self.self_domain,
                                           self._prefetch_count, self._permanent_consume)

    async def stop(self, exception: Exception = None):
        pass

    @staticmethod
    async def _setup_event_publisher(connection: AbstractRobustConnection) -> AbstractExchange:
        event_publisher_channel = await connection.channel()
        return await event_publisher_channel.declare_exchange('events', type='fanout', durable=True)

    @staticmethod
    async def _setup_response_publisher(connection: AbstractRobustConnection) -> AbstractExchange:
        response_publisher_channel = await connection.channel()
        return response_publisher_channel.default_exchange

    @staticmethod
    async def _setup_command_consumer(connection: AbstractConnection, domain: str,
                                      prefetch_count=0, permanent_consume=True) -> AbstractQueue:
        command_consumer_channel = await connection.channel(publisher_confirms=False)
        await command_consumer_channel.declare_exchange('commands', type='fanout', durable=True)

        await command_consumer_channel.set_qos(prefetch_count=prefetch_count)
        command_queue = await command_consumer_channel.declare_queue(
            'commands', durable=permanent_consume, auto_delete=not permanent_consume)
        await command_queue.bind('commands', f'{domain}.*')
        return command_queue


class RabbitOtherDomainClient(AbstractRabbitDomainClient):
    async def handle(self, message: BaseMessage):
        pass

    _event_queue: AbstractQueue
    _command_exchange: AbstractExchange
    _response_queue: AbstractQueue

    async def start(self):
        self._event_queue = await self._setup_event_consumer(
            self._connection, self.self_domain, [f'{self.connected_domain}.*'],
            self._prefetch_count, self._permanent_consume)
        self._command_exchange = await self._setup_command_publisher(self._connection)
        self._response_queue = await self._setup_response_consumer(self._connection)
        await self._response_queue.consume(self._response_callback)

    async def stop(self, exception: Exception = None):
        pass

    @staticmethod
    async def _setup_event_consumer(connection: AbstractRobustConnection,
                                    queue_name: str, binding_list: t.Iterable[str],
                                    prefetch_count=0, permanent_consume=True) -> AbstractQueue:
        event_consume_channel = await connection.channel()
        await event_consume_channel.declare_exchange('events', type='fanout', durable=True)
        await event_consume_channel.set_qos(prefetch_count=prefetch_count)
        event_queue = await event_consume_channel.declare_queue(
            queue_name, durable=permanent_consume, auto_delete=not permanent_consume)
        for routing_key in binding_list:
            await event_queue.bind('events', routing_key)
        return event_queue

    @staticmethod
    async def _setup_command_publisher(connection: AbstractConnection) -> AbstractExchange:
        command_publish_channel = await connection.channel()
        command_exchange = await command_publish_channel.declare_exchange('commands', durable=True)
        return command_exchange

    @staticmethod
    async def _setup_response_consumer(connection: AbstractConnection) -> AbstractQueue:
        response_consume_channel = await connection.channel()
        response_queue = await response_consume_channel.declare_queue(exclusive=True, auto_delete=True)
        return response_queue

    async def _response_callback(self, message: AbstractIncomingMessage):
        pass
