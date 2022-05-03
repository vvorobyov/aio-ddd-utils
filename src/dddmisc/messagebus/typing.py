import typing as t

from dddmisc.messages import DomainEvent, DomainCommand, DomainCommandResponse

AsyncEventHandlerType = t.Callable[[DomainEvent], t.Awaitable]
AsyncCommandHandlerType = t.Callable[[DomainCommand], t.Awaitable[DomainCommandResponse]]

SyncEventHandlerType = t.Callable[[DomainEvent], None]
SyncCommandHandlerType = t.Callable[[DomainCommand], DomainCommandResponse]

EventHandlerType = t.Callable[[DomainEvent], t.Optional[t.Awaitable]]
CommandHandlerType = t.Callable[
    [DomainCommand],
    t.Union[DomainCommandResponse, t.Awaitable[DomainCommandResponse]]]
