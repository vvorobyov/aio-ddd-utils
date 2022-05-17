import abc
import typing as t
from asyncio import AbstractEventLoop

from dddmisc.messages import DDDResponse
from dddmisc.messages.messages import DDDMessage

__all__ = ['AbstractSyncExternalMessageBus', 'AbstractAsyncExternalMessageBus']


class AbstractAsyncExternalMessageBus(abc.ABC):
    _loop: AbstractEventLoop

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    def set_loop(self, loop: AbstractEventLoop):
        if not hasattr(self, '_loop'):
            self._loop = loop
        raise RuntimeError('loop is already set')

    @abc.abstractmethod
    async def handle(self, message: DDDMessage, timeout: float = None) -> t.Optional[DDDResponse]:
        ...

    @abc.abstractmethod
    async def start(self):
        ...

    @abc.abstractmethod
    async def stop(self, exception: Exception = None):
        ...


class AbstractSyncExternalMessageBus(abc.ABC):

    @abc.abstractmethod
    def handle(self, message: DDDMessage):
        ...

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self, exception: Exception = None):
        ...
