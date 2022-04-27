import typing as t

from dddmisc.domain_message import Event, Command


AsyncEventHandlerType = t.Callable[[Event], t.Awaitable]
AsyncCommandHandlerType = t.Callable[[Command], t.Awaitable[object]]  # Заменить на DomainResponse

SyncEventHandlerType = t.Callable[[Event], None]
SyncCommandHandlerType = t.Callable[[Command], object]  # Заменить на DomainResponse

EventHandlerType = t.Callable[[Event], t.Optional[t.Awaitable]]
CommandHandlerType = t.Callable[[Command], t.Union[object, t.Awaitable[object]]]  # Заменить на DomainResponse
