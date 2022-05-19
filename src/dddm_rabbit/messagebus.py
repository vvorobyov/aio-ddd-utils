import asyncio
import typing as t

from dddmisc.messages import DDDEvent, DDDCommand, DDDResponse
from dddmisc.messages.messages import DDDMessage
from dddmisc.messagebus.abstract import AbstractAsyncExternalMessageBus, AbstractSyncExternalMessageBus
from dddm_rabbit.abstract import AbstractRabbitDomainClient
from dddm_rabbit.base import BaseRabbitMessageBus
from dddm_rabbit.domain_clients import RabbitSelfDomainClient, RabbitOtherDomainClient


class AsyncRabbitMessageBus(BaseRabbitMessageBus, AbstractAsyncExternalMessageBus):

    def __init__(self, *args,
                 self_domain_class: t.Type[AbstractRabbitDomainClient] = None,
                 other_domain_client: t.Type[AbstractRabbitDomainClient] = None,
                 **kwargs):
        self._domain_clients: t.Dict[str, AbstractRabbitDomainClient] = {}
        self._self_domain_class = self_domain_class or RabbitSelfDomainClient
        self._other_domain_class = other_domain_client or RabbitOtherDomainClient
        super(AsyncRabbitMessageBus, self).__init__(*args, **kwargs)

    async def start(self):
        start_coroutines = []

        for domain in self.registered_domains:
            events = self._events_configs.get_events_by_domain_name(domain)
            commands = self._commands_configs.get_commands_by_domain_name(domain)
            if domain == self._domain:
                client = self._self_domain_class(
                    self._url, self.domain, '', events, commands, self._execute_command_handler)
            else:
                client = self._other_domain_class(self._url, self.domain, domain, events, commands,
                                                  self._execute_event_handlers)
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

    async def _execute_event_handlers(self, event: DDDEvent, publisher: str):
        if event.get_domain_name() != publisher:
            return
        handlers = self._events_configs.get_event_handlers(event)
        for handler in handlers:
            await handler(event)

    async def _execute_command_handler(self, command: DDDCommand, publisher: str) -> DDDResponse:
        domain = command.get_domain_name()
        if domain == self.domain and self._commands_configs.check_command_permission(command, publisher):
            handler = self._commands_configs.get_command_handler(command)
            return await handler(command)

    @t.overload
    async def handle(self, message: DDDEvent, timeout: float = None) -> t.NoReturn:
        ...

    @t.overload
    async def handle(self, message: DDDCommand, timeout: float = None) -> DDDResponse:
        ...

    async def handle(self, message: t.Union[DDDEvent, DDDCommand], timeout=None):
        domain = message.__domain__
        client = self._domain_clients.get(domain)
        if isinstance(message, DDDCommand):
            return await self._handle_command(message, timeout)
        elif isinstance(message, DDDEvent):
            return await client.handle_event(message)

    async def _handle_command(self, command: DDDCommand, timeout: float = None) -> DDDResponse:
        domain = command.get_domain_name()
        if domain in self.registered_domains:
            client = self._domain_clients.get(domain)
            return await client.handle_command(command, timeout)
        else:
            raise ValueError(f'Domain "{domain}" not registered in {self}')

    async def _handle_event(self, event: DDDEvent):
        domain = event.get_domain_name()
        if domain == self.domain:
            client = self._domain_clients.get(domain)
            return await client.handle_event(event)
        else:
            raise RuntimeError(f'Forbidden to publish events not of yourself domain. '
                               f'Event "{event.__class__.__name__}" of "{domain}" domain')


class SyncRabbitMessageBus(BaseRabbitMessageBus, AbstractSyncExternalMessageBus):
    def handle(self, message: DDDMessage):
        pass

    def start(self):
        pass

    def stop(self, exception: Exception = None):
        pass
