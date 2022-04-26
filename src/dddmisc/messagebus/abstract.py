import abc
from asyncio import AbstractEventLoop

from dddmisc.domain_message.messages import BaseMessage

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
    async def handle(self, message: BaseMessage):
        ...

    @abc.abstractmethod
    async def start(self):
        ...

    @abc.abstractmethod
    async def stop(self, exception: Exception = None):
        ...


class AbstractSyncExternalMessageBus(abc.ABC):

    @abc.abstractmethod
    def handle(self, message: BaseMessage):
        ...

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self, exception: Exception = None):
        ...
