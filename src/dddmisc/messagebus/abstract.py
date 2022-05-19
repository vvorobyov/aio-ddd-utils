import abc
import typing as t
from asyncio import AbstractEventLoop

from dddmisc import DDDCommand
from dddmisc.messages import DDDResponse, DDDEvent

__all__ = ['AbstractSyncExternalMessageBus', 'AbstractAsyncExternalMessageBus']


class AbstractAsyncExternalMessageBus(abc.ABC):
    _loop: AbstractEventLoop

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    def set_loop(self, loop: AbstractEventLoop):
        if not hasattr(self, '_loop'):
            self._loop = loop
        else:
            raise RuntimeError('loop is already set')

    @t.overload
    async def handle(self, message: DDDCommand, timeout: float = None) -> DDDResponse:
        ...

    @t.overload
    async def handle(self, message: DDDEvent, timeout: float = None) -> t.NoReturn:
        ...

    @abc.abstractmethod
    async def handle(self, message, timeout=None):
        ...

    @abc.abstractmethod
    async def start(self):
        ...

    @abc.abstractmethod
    async def stop(self, exception: Exception = None):
        ...


class AbstractSyncExternalMessageBus(abc.ABC):

    @t.overload
    def handle(self, message: DDDCommand, timeout: float = None) -> DDDResponse: ...

    @t.overload
    def handle(self, message: DDDEvent, timeout: float = None) -> t.NoReturn: ...

    @abc.abstractmethod
    def handle(self, message, timeout=None):
        ...

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self, exception: Exception = None):
        ...
