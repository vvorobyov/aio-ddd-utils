import asyncio
import typing as t

from dddmisc.messages import DomainEvent, DomainCommand, DomainCommandResponse
from dddmisc.messages.messages import DomainMessage
from dddmisc.messagebus.abstract import AbstractAsyncExternalMessageBus, AbstractSyncExternalMessageBus
from dddmisc.messagebus.rabbitmq.abstract import AbstractRabbitDomainClient
from dddmisc.messagebus.rabbitmq.base import BaseRabbitMessageBus
from dddmisc.messagebus.rabbitmq.domain_clients import RabbitSelfDomainClient, RabbitOtherDomainClient


class AsyncRabbitMessageBus(BaseRabbitMessageBus, AbstractAsyncExternalMessageBus):

    def __init__(self, *args, **kwargs):
        self._domain_clients: t.Dict[str, AbstractRabbitDomainClient] = {}
        super(AsyncRabbitMessageBus, self).__init__(*args, **kwargs)

    async def start(self):
        start_coroutines = []

        for domain in self.registered_domains:
            events = self._events_configs.get_events_by_domain_name(domain)
            commands = self._commands_configs.get_commands_by_domain_name(domain)
            if domain == self._domain:
                client = RabbitSelfDomainClient(self._url, self.domain, '', events, commands, self._command_callback)
            else:
                client = RabbitOtherDomainClient(self._url, self.domain, domain, events, commands, self._event_callback)
            self._domain_clients[domain] = client
            start_coroutines.append(client.start())
        results = await asyncio.gather(*start_coroutines, return_exceptions=True)
        errors = [result for result in results if isinstance(result, BaseException)]
        if errors:
            await self.stop(errors[0])
            raise errors[0]

    async def stop(self, exception: BaseException = None):
        await asyncio.gather(*(client.stop(exception) for client in self._domain_clients.values()),
                             return_exceptions=True)

    async def _event_callback(self, event: DomainEvent, publisher: str):
        if event.get_domain_name() != publisher:
            return
        handlers = self._events_configs.get_event_handlers(event)
        for handler in handlers:
            await handler(event)

    async def _command_callback(self, command: DomainCommand, publisher: str) -> DomainCommandResponse:
        domain = command.get_domain_name()
        if domain == self.domain and self._commands_configs.check_command_permission(command, publisher):
            handler = self._commands_configs.get_command_handler(command)
            return await handler(command)

    async def handle(self, message: DomainMessage, timeout: float = None) -> t.Optional[DomainCommandResponse]:
        domain = message.get_domain_name()
        client = self._domain_clients.get(domain)
        if isinstance(message, DomainCommand):
            return await self._handler_command(message, timeout)
        elif isinstance(message, DomainEvent):
            return await client.handle_event(message)

    async def _handler_command(self, command: DomainCommand, timeout: float = None) -> DomainCommandResponse:
        domain = command.get_domain_name()
        if domain in self.registered_domains:
            client = self._domain_clients.get(domain)
            return await client.handle_command(command, timeout)
        else:
            raise ValueError(f'Domain "{domain}" not registered in {self}')

    async def _handle_event(self, event: DomainEvent):
        domain = event.get_domain_name()
        if domain == self.domain:
            client = self._domain_clients.get(domain)
            return await client.handle_event(event)
        else:
            raise RuntimeError(f'Forbidden to publish events not of yourself domain. '
                               f'Event "{event.__class__.__name__}" of "{domain}" domain')


class SyncRabbitMessageBus(BaseRabbitMessageBus, AbstractSyncExternalMessageBus):
    def handle(self, message: DomainMessage):
        pass

    def start(self):
        pass

    def stop(self, exception: Exception = None):
        pass
