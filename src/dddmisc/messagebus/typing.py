import typing as t

from dddmisc.domain_message import Event, Command

AsyncEventHandlerType = t.Callable[[Event], t.Awaitable]
AsyncCommandHandlerType = t.Callable[[Command], t.Awaitable[object]]  # Заменить на DomainResponse

EventHandlerType = t.Callable[[Event], None]
CommandHandlerType = t.Callable[[Command], object]  # Заменить на DomainResponse
