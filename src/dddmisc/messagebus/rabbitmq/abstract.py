import abc

from aio_pika.abc import AbstractRobustConnection

from dddmisc.domain_message.messages import BaseMessage


class AbstractRabbitDomainClient(abc.ABC):
    def __init__(self, connection: AbstractRobustConnection,
                 self_domain: str, connected_domain: str, permanent_consume=True, prefetch_count=0):
        self._self_domain = self_domain
        self._connected_domain = connected_domain
        self._connection = connection
        self._permanent_consume = permanent_consume
        self._prefetch_count = prefetch_count

    @property
    def self_domain(self) -> str:
        return self._self_domain

    @property
    def connected_domain(self) -> str:
        return self._connected_domain

    @abc.abstractmethod
    async def handle(self, message: BaseMessage):
        pass

    @abc.abstractmethod
    async def start(self):
        ...

    @abc.abstractmethod
    async def stop(self, exception: Exception = None):
        ...
