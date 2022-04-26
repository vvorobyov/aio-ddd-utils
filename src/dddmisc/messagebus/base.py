import typing as t
from collections import defaultdict

from dddmisc.domain_message import Event, Command
from dddmisc.messagebus.typing import AsyncEventHandlerType, AsyncCommandHandlerType, \
    EventHandlerType, CommandHandlerType

_RegisteredEventsType = dict[str, dict[t.Type[Event],
                                       list[t.Union[EventHandlerType, AsyncEventHandlerType]]]]
_RegisteredCommandsType = dict[str, dict[t.Type[Command],
                                         tuple[t.Union[CommandHandlerType, AsyncCommandHandlerType], tuple[str]]]]


class BaseExternalMessageBus:
    def __init__(self, *, domain: str):
        self._domain = domain
        self._registered_events: _RegisteredEventsType = defaultdict(lambda: defaultdict(list))
        self._registered_commands: _RegisteredCommandsType = defaultdict(dict)

    @property
    def domain(self) -> str:
        return self._domain

    def consume_event(self, event: t.Type[Event],
                      handler: EventHandlerType):
        self._registered_events[event.__domain_name__][event].append(handler)

    def consume_command(self, command: t.Type[Command],
                        handler: AsyncCommandHandlerType, allowed_domains: t.Iterable[str]):
        self._registered_commands[command.__domain_name__][command] = (handler, tuple(allowed_domains))

    def get_registered_domains(self) -> t.Set[str]:
        return {*self._registered_events.keys(), *self._registered_commands.keys()}
