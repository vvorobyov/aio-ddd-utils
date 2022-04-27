import inspect
import typing as t

import attr

from dddmisc.domain_message import Event, Command
from dddmisc.messagebus.typing import EventHandlerType, CommandHandlerType


@attr.s(frozen=True)
class EventConfig:
    event_type: t.Type[Event] = attr.ib()
    _handlers: t.Set[EventHandlerType] = attr.ib(init=False, factory=set)

    @property
    def domain(self) -> str:
        return self.event_type.__domain_name__

    @property
    def handlers(self) -> t.Iterable[EventHandlerType]:
        return tuple(self._handlers)

    def add_handlers(self, handlers: t.Iterable[EventHandlerType]):
        self._handlers.update(handlers)


class EventConfigsCollection:
    def __init__(self):
        self._configs: dict[t.Type[Event], EventConfig] = {}

    def add(self, event_type: t.Type[Event], *handlers: EventHandlerType):
        self._configs.setdefault(event_type, EventConfig(event_type)).add_handlers(handlers)

    def get_events_by_domain_name(self, domain_name: str):
        return (event_cfg.event_type
                for event_cfg in self._configs.values()
                if event_cfg.domain == domain_name)

    def get_event_handlers(self, event: t.Type[Event]) -> t.Tuple[EventHandlerType, ...]:
        event_cfg = self._configs.get(event, None)
        if event_cfg:
            return tuple(event_cfg.handlers)
        else:
            return ()

    def __contains__(self, item: t.Union[t.Type[Event], Event]):
        if not inspect.isclass(item):
            item = type(item)
        if not issubclass(item, Event):
            return False
        return item in self._configs


@attr.s(frozen=True)
class CommandConfig:

    command_type: t.Type[Command] = attr.ib()
    _handler: CommandHandlerType = attr.ib(default=None)
    _allowed_domains: t.Set[str] = attr.ib(factory=set)

    @property
    def domain(self) -> str:
        return self.command_type.__domain_name__

    @property
    def handler(self) -> CommandHandlerType:
        return self._handler

    def set_handler(self, handler):
        object.__setattr__(self, '_handler', handler)

    def add_permissions(self, allowed_domains: t.Iterable[str]):
        self._allowed_domains.update(allowed_domains)

    def check_permission(self, publisher: str):
        return publisher in self._allowed_domains


class CommandConfigsCollection:

    def __init__(self):
        self._configs: dict[t.Type[Command], CommandConfig] = {}

    def set(self, command_type: t.Type[Command], handler: CommandHandlerType):
        self._configs.setdefault(command_type, CommandConfig(command_type)).set_handler(handler)

    def set_permissions(self, command_type: t.Type[Command], *allowed_domains: str):
        self._configs.setdefault(command_type, CommandConfig(command_type)).add_permissions(allowed_domains)

    def get_commands_by_domain_name(self, domain_name: str):
        return (command_cfg.command_type
                for command_cfg in self._configs.values()
                if command_cfg.domain == domain_name)

    def get_command_handler(self, command: t.Type[Command]) -> t.Optional[CommandHandlerType]:
        command_cfg = self._configs.get(command, None)
        if command_cfg:
            return command_cfg.handler

    def check_command_permission(self, command: t.Type[Command], publisher: str) -> bool:
        command_cfg = self._configs.get(command, None)
        if command_cfg:
            return command_cfg.check_permission(publisher)
        return False

    def __contains__(self, item: t.Union[t.Type[Command], Command]):
        if not inspect.isclass(item):
            item = type(item)
        if not issubclass(item, Command):
            return False
        return item in self._configs


class BaseExternalMessageBus:
    def __init__(self, *, domain: str):
        self._domain = domain
        self._registered_domains = set()
        self._events_handlers = EventConfigsCollection()
        self._commands_handlers = CommandConfigsCollection()

    @property
    def domain(self) -> str:
        return self._domain

    def consume_event(self, event: t.Type[Event], *handlers: EventHandlerType):
        self._registered_domains.add(event.__domain_name__)
        self._events_handlers.add(event, *handlers)

    def consume_command(self, command: t.Type[Command], handler: CommandHandlerType):
        self._registered_domains.add(command.__domain_name__)
        self._commands_handlers.set(command, handler)

    def set_permission_for_command(self, command: t.Type[Command], *allowed_domains: str):
        self._registered_domains.add(command.__domain_name__)
        self._commands_handlers.set_permissions(command, *allowed_domains)

    def get_registered_domains(self) -> t.Iterable[str]:
        return tuple(self._registered_domains)
