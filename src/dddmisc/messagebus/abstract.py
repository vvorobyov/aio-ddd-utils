import abc
import typing as t
from asyncio import AbstractEventLoop

from dddmisc.messages import DomainCommandResponse
from dddmisc.messages.messages import DomainMessage

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
    async def handle(self, message: DomainMessage, timeout: float = None) -> t.Optional[DomainCommandResponse]:
        ...

    @abc.abstractmethod
    async def start(self):
        ...

    @abc.abstractmethod
    async def stop(self, exception: Exception = None):
        ...


class AbstractSyncExternalMessageBus(abc.ABC):

    @abc.abstractmethod
    def handle(self, message: DomainMessage):
        ...

    @abc.abstractmethod
    def start(self):
        ...

    @abc.abstractmethod
    def stop(self, exception: Exception = None):
        ...
