import typing as t

from dddmisc.messages import DDDEvent, DDDCommand, DDDResponse

AsyncEventHandlerType = t.Callable[[DDDEvent], t.Awaitable]
AsyncCommandHandlerType = t.Callable[[DDDCommand], t.Awaitable[DDDResponse]]

SyncEventHandlerType = t.Callable[[DDDEvent], None]
SyncCommandHandlerType = t.Callable[[DDDCommand], DDDResponse]

EventHandlerType = t.Callable[[DDDEvent], t.Optional[t.Awaitable]]
CommandHandlerType = t.Callable[
    [DDDCommand],
    t.Union[DDDResponse, t.Awaitable[DDDResponse]]]
