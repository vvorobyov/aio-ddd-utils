import asyncio
import typing as t

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractConnection

from dddmisc.messages.messages import DomainMessage
from dddmisc.messagebus.abstract import AbstractAsyncExternalMessageBus, AbstractSyncExternalMessageBus
from dddmisc.messagebus.rabbitmq.abstract import AbstractRabbitDomainClient
from dddmisc.messagebus.rabbitmq.base import BaseRabbitMessageBus
from dddmisc.messagebus.rabbitmq.domain_clients import RabbitSelfDomainClient, RabbitOtherDomainClient


class AsyncRabbitMessageBus(BaseRabbitMessageBus, AbstractAsyncExternalMessageBus):
    _connection: AbstractRobustConnection

    def __init__(self, *args, **kwargs):
        self._domain_connections: t.Dict[str, AbstractConnection] = {}
        self._domain_clients: t.Dict[str, AbstractRabbitDomainClient] = {}
        super(AsyncRabbitMessageBus, self).__init__(*args, **kwargs)

    async def handle(self, message: DomainMessage):
        return await self._domain_clients[message.get_domain_name()].handle(message)

    async def start(self):

        for domain in self.get_registered_domains():
            events = self._events_configs.get_events_by_domain_name(domain)
            commands = self._commands_configs.get_commands_by_domain_name(domain)
            if domain == self._domain:
                client = RabbitSelfDomainClient(self._url, self.domain, '', events, commands)  # TODO обдумать конфиг для подключения к домену
            else:
                client = RabbitOtherDomainClient(self._url, self.domain, domain, events, commands) # TODO обдумать конфиг для подключения к домену
            self._domain_clients[domain] = client

    async def stop(self, exception: Exception = None):
        await asyncio.gather(*(client.stop(exception) for client in self._domain_clients.values()),
                             return_exceptions=True)
        await asyncio.gather(*(conn.close(exception) for conn in self._domain_connections.values()),
                             return_exceptions=True)


class SyncRabbitMessageBus(BaseRabbitMessageBus, AbstractSyncExternalMessageBus):
    def handle(self, message: DomainMessage):
        pass

    def start(self):
        pass

    def stop(self, exception: Exception = None):
        pass
