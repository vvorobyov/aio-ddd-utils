import abc
import logging
import typing as t

import attr
from pika.adapters.blocking_connection import BlockingChannel, BlockingConnection

from aioddd_utils.domain_message import Event, Command, AbstractDomainMessage
import environ
import pika

from aioddd_utils.domain_message.messages import BaseMessage

logger = logging.getLogger('ddd.amqp_messagebus')


@attr.s(frozen=True)
class MessageConfig:
    message_type: t.Type[BaseMessage] = attr.ib()
    _allowed_domains: t.Optional[tuple[str, ...]] = attr.ib(default=None)

    @property
    def routing_key(self) -> str:
        return f'{self.message_type.__domain_name__}.{self.message_type.__name__}'

    @property
    def allowed_domains(self) -> tuple[str, ...]:
        if self._allowed_domains is None:
            return ()
        return tuple(self._allowed_domains)

    @property
    def domain(self) -> str:
        return self.message_type.__domain_name__


class AbstractSyncAMQPMessagebus(abc.ABC):
    self_domain: str

    @abc.abstractmethod
    def get_connection_params(self, domain: str) -> pika.ConnectionParameters:
        pass

    @abc.abstractmethod
    def get_messages_cfg_by_domain(self, domain: str) -> t.Iterable[MessageConfig]:
        pass


class DomainBus:
    def __init__(self, domain: str, messagebus: AbstractSyncAMQPMessagebus,
                 prefetch_count=1, permanent_consume=True):
        self.prefetch_count = prefetch_count
        self.permanent_consume = permanent_consume
        self.domain = domain
        self.connection_params = messagebus.get_connection_params(domain)
        self.is_self_domain = messagebus.self_domain == domain
        self.registered_events = set(event_cfg
                                     for event_cfg in messagebus.get_messages_cfg_by_domain(domain)
                                     if issubclass(event_cfg.message_type, Event))  # type: set[MessageConfig]
        self.registered_commands = set(command_cfg
                                       for command_cfg in messagebus.get_messages_cfg_by_domain(domain)
                                       if issubclass(command_cfg.message_type, Command))  # type: set[MessageConfig]

    def start(self) -> dict[str, BlockingChannel]:
        connection = self._create_connection()
        if self.is_self_domain:
            config = self._self_domain_channels(connection)
        else:
            config = self._other_domain_channels(connection)
        return config

    def _self_domain_channels(self, connection: BlockingConnection) -> dict[str, BlockingChannel]:
        # Задачи класса для собственного домена:
        # - Публикация событий собственного сервиса
        event_publish_ch = connection.channel()
        event_publish_ch.exchange_declare('events', durable=True)

        # - Получение комманд от других сервисов
        cmd_consume_ch = connection.channel()
        cmd_consume_ch.exchange_declare('commands', durable=True)
        cmd_consume_ch.queue_declare('commands', durable=self.permanent_consume, auto_delete=not self.permanent_consume)
        self._consume_to_messages(channel=cmd_consume_ch,
                                  queue_name='commands', exchange_name='commands',
                                  message_configs=self.registered_commands)
        cmd_consume_ch.basic_qos(prefetch_count=self.prefetch_count)
        cmd_consume_ch.basic_consume('commands', lambda *x, **z: print(x, z))  # TODO заменить

        # - Публикация ответов на команды
        response_publish_ch = connection.channel()

        return {
            'event_publish_ch': event_publish_ch,
            'cmd_consume_ch': cmd_consume_ch,
            'response_publish_ch': response_publish_ch,
        }

    def _other_domain_channels(self, connection: BlockingConnection) -> dict[str, BlockingChannel]:
        # Задачи класса для другого домена:
        # - Получение событий от других сервисов
        events_consume_ch = connection.channel()
        events_consume_ch.exchange_declare('events', durable=True)

        events_consume_ch.queue_declare(
            self.domain, durable=self.permanent_consume, auto_delete=not self.permanent_consume)

        self._consume_to_messages(channel=events_consume_ch,
                                  queue_name=self.domain, exchange_name='events',
                                  message_configs=self.registered_events)
        events_consume_ch.basic_qos(prefetch_count=self.prefetch_count)
        events_consume_ch.basic_consume(self.domain, lambda *x, **z: print(x, z))  # TODO заменить

        # - Публикация комманд для других сервисов
        cmd_publish_ch = connection.channel()
        cmd_publish_ch.exchange_declare('commands', durable=True)

        # - Получение персональных ответов на комманды
        response_consume_ch = connection.channel()
        declare_res = response_consume_ch.queue_declare('', exclusive=True, auto_delete=True)
        response_queue = declare_res.method.queue
        response_consume_ch.basic_consume(response_queue, auto_ack=True,
                                          on_message_callback=lambda *x, **z: print(x, z))  # TODO заменить

        return {
            'events_consume_ch': events_consume_ch,
            'cmd_publish_ch': cmd_publish_ch,
            'response_consume_ch': response_consume_ch,
        }

    def _create_connection(self) -> pika.BlockingConnection:
        params = self.connection_params
        connection = pika.BlockingConnection(parameters=params)
        return connection

    @staticmethod
    def _consume_to_messages(channel: BlockingChannel,
                             queue_name: str, exchange_name: str,
                             message_configs: t.Iterable[MessageConfig]):
        for cfg in message_configs:
            channel.queue_bind(queue_name, exchange_name, cfg.routing_key)
        return channel

    def _callback_message_handler(self, *args, **kwargs):
        pass

    def _consume_message_handler(self, *args, **kwargs):
        pass


class SyncAMQPMessagebus(AbstractSyncAMQPMessagebus):

    def __init__(self, self_domain: str = None,
                 host: str = None, port: int = None,
                 username: str = None, password: str = None):
        env = environ.Env()
        self.self_domain = env.str('DDD_SELFDOMAIN', '').strip() or self_domain
        host = env.str('DDD_MESSAGEBUS_HOST', '').strip().removesuffix('/') or host
        port = env.int('DDD_MESSAGEBUS_PORT', 0) or port
        username = env.str('DDD_MESSAGEBUS_USERNAME', '') or username
        password = env.str('DDD_MESSAGEBUS_PASSWORD', '') or password
        assert (username and password), (
            'Not set all required parameters for SyncAMQPMessagebus')
        assert (self.self_domain and host and port), (
            'Not set all required parameters for SyncAMQPMessagebus')
        self._get_connection_params = lambda domain: (
            pika.ConnectionParameters(host=host, port=port, virtual_host=domain,
                                      credentials=pika.PlainCredentials(username, password))
        )
        self._registered_messages: set[MessageConfig] = set()

    def get_connection_params(self, domain: str):
        return self._get_connection_params(domain)

    def register(self, message_type: t.Type[AbstractDomainMessage], allowed_domains: tuple[str, ...] = None):
        if issubclass(message_type, Event):
            if message_type.__domain_name__ == self.self_domain:
                message_config = MessageConfig(message_type)
            else:
                message_config = MessageConfig(message_type, (message_type.__domain_name__,))
        elif issubclass(message_type, Command):
            if message_type.__domain_name__ == self.self_domain:
                message_config = MessageConfig(message_type, allowed_domains)
            else:
                message_config = MessageConfig(message_type)
        else:
            raise TypeError('Unknown message type "%r"' % message_type)
        self._registered_messages.add(message_config)

    def get_messages_cfg_by_domain(self, domain: str) -> t.Iterable[MessageConfig]:
        yield from (message_config
                    for message_config in self._registered_messages
                    if message_config.domain == domain)

    def publish_command(self, command: Command):
        pass

    def start(self):
        pass

    def stop(self, exception: Exception):
        pass

    def publish_event(self, event: Event):
        if event.__domain_name__ != self.self_domain:
            logger.warning('Attempt publish event not self domain %s %s, %r', event.__domain_name__, event)
            return
        if not event.__registered__:
            logger.warning('Attempt publish not registered event %r', event)
            return
        # self.event_exchange.publish(event)
