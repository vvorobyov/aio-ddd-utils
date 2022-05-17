import inspect
import typing as t

import attr

from dddmisc.messages import DDDEvent, DDDCommand
from dddmisc.messagebus.typing import EventHandlerType, CommandHandlerType


@attr.s(frozen=True)
class EventConfig:
    event_type: t.Type[DDDEvent] = attr.ib()
    _handlers: t.Set[EventHandlerType] = attr.ib(init=False, factory=set)

    @property
    def domain(self) -> str:
        return self.event_type.get_domain_name()

    @property
    def handlers(self) -> t.Iterable[EventHandlerType]:
        return tuple(self._handlers)

    def add_handlers(self, handlers: t.Iterable[EventHandlerType]):
        self._handlers.update(handlers)


class EventConfigsCollection:
    def __init__(self):
        self._configs: dict[t.Type[DDDEvent], EventConfig] = {}

    def add(self, event_type: t.Type[DDDEvent], *handlers: EventHandlerType):
        self._configs.setdefault(event_type, EventConfig(event_type)).add_handlers(handlers)

    def get_events_by_domain_name(self, domain_name: str):
        return (event_cfg.event_type
                for event_cfg in self._configs.values()
                if event_cfg.domain == domain_name)

    def get_event_handlers(self, event: t.Union[t.Type[DDDEvent], DDDEvent]) -> t.Tuple[EventHandlerType, ...]:
        event_cfg = self._configs.get(type(event), self._configs.get(event, None))
        if event_cfg:
            return tuple(event_cfg.handlers)
        else:
            return ()

    def __contains__(self, item: t.Union[t.Type[DDDEvent], DDDEvent]):
        if not inspect.isclass(item):
            item = type(item)
        if not issubclass(item, DDDEvent):
            return False
        return item in self._configs


@attr.s(frozen=True)
class CommandConfig:

    command_type: t.Type[DDDCommand] = attr.ib()
    _handler: CommandHandlerType = attr.ib(default=None)
    _allowed_domains: t.Set[str] = attr.ib(factory=set)

    @property
    def domain(self) -> str:
        return self.command_type.get_domain_name()

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
        self._configs: dict[t.Type[DDDCommand], CommandConfig] = {}

    def set(self, command_type: t.Type[DDDCommand], handler: CommandHandlerType):
        self._configs.setdefault(command_type, CommandConfig(command_type)).set_handler(handler)

    def set_permissions(self, command_type: t.Type[DDDCommand], *allowed_domains: str):
        self._configs.setdefault(command_type, CommandConfig(command_type)).add_permissions(allowed_domains)

    def get_commands_by_domain_name(self, domain_name: str):
        return (command_cfg.command_type
                for command_cfg in self._configs.values()
                if command_cfg.domain == domain_name)

    def get_command_handler(self, command: t.Union[t.Type[DDDCommand], DDDCommand]) -> t.Optional[CommandHandlerType]:
        command_cfg = self._configs.get(type(command), self._configs.get(command, None))
        if command_cfg:
            return command_cfg.handler

    def check_command_permission(self, command: t.Union[t.Type[DDDCommand], DDDCommand], publisher: str) -> bool:
        command_cfg = self._configs.get(type(command), self._configs.get(command, None))
        if command_cfg:
            return command_cfg.check_permission(publisher)
        return False

    def __contains__(self, item: t.Union[t.Type[DDDCommand], DDDCommand]):
        if not inspect.isclass(item):
            item = type(item)
        if not issubclass(item, DDDCommand):
            return False
        return item in self._configs


class BaseExternalMessageBus:
    def __init__(self, domain: str, **kwargs):
        self._domain = domain
        self._registered_domains = {domain}
        self._events_configs = EventConfigsCollection()
        self._commands_configs = CommandConfigsCollection()

    @property
    def domain(self) -> str:
        return self._domain

    @property
    def registered_domains(self) -> t.Iterable[str]:
        return tuple(self._registered_domains)

    def register_domains(self, *domains: str):
        """
        Метод регистрации наименований доменов внешних сервисов с которыми будет взаимодействовать класс,
        в частности отправлять комманды. Для каждого зарегистрированного домена будет поднято подключение
        к соответствующему vhost. Регистрация допускается только до запуска шины методом start.
        :param domains: перечень доменов регистрацию которых необходимо произвести в классе
        :return:
        """
        self._registered_domains.update(domains)

    def register_event_handlers(self, event: t.Type[DDDEvent], *handlers: EventHandlerType):
        self.register_domains(event.get_domain_name())
        self._events_configs.add(event, *handlers)

    def register_command_handler(self, command: t.Type[DDDCommand], handler: CommandHandlerType,
                                 *allowed_domains: str):
        self.register_domains(command.get_domain_name())
        self._commands_configs.set(command, handler)
        self.set_permission_for_command(command, *allowed_domains)

    def set_permission_for_command(self, command: t.Type[DDDCommand], *allowed_domains: str):
        self.register_domains(command.get_domain_name())
        self._commands_configs.set_permissions(command, *allowed_domains)


