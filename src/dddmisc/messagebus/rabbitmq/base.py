import typing as t

from environ import environ
from yarl import URL

from dddmisc.messagebus.base import BaseExternalMessageBus


class BaseRabbitMessageBus(BaseExternalMessageBus):
    def __init__(self,  url: t.Union[str, URL], *args, **kwargs):
        env = environ.Env()
        self._url = URL(env.str('DDD_RMQ_MESSAGEBUS_URL', '') or url)
        super(BaseRabbitMessageBus, self).__init__(*args, **kwargs)
