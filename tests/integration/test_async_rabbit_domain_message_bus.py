import asyncio
from asyncio import AbstractEventLoop

import aio_pika
import pytest
from aio_pika import RobustExchange, RobustQueue
from aio_pika.abc import AbstractRobustExchange

from dddmisc.domain_message import Event, fields
from dddmisc.messagebus.rabbitmq.domain_clients import RabbitSelfDomainClient, RabbitOtherDomainClient
from dddmisc.messagebus.rabbitmq import AsyncRabbitMessageBus
from integration.conftest import random_word


class TestRabbitDomainClient:

    async def test_start_and_stop_self_domain_client(self, event_loop: AbstractEventLoop, rabbit):
        async with rabbit() as cfg:
            client = RabbitSelfDomainClient(cfg.url, cfg.vhost, '', (), (), None)

            await client.start()

            assert client._connection.connected
            assert client._response_exchange.name == ''
            assert client._event_exchange.name == 'events'
            assert client._command_queue.name == 'commands'

            await client.stop()

    async def test_start_and_stop_other_domain_client(self, event_loop: AbstractEventLoop, rabbit):
        async with rabbit() as cfg:
            self_domain = random_word()
            client = RabbitOtherDomainClient(cfg.url, self_domain, cfg.vhost, (), (), None)
            await client.start()

            assert client._connection.connected
            assert client._event_queue.name == self_domain
            assert client._command_exchange.name == 'commands'
            assert client._response_queue.name != self_domain

            await client.stop()

    # async def test_self_domain_command_consume(self, rabbit):
    #     async with rabbit() as cfg:
    #         client = RabbitSelfDomainClient(cfg.url, self_domain=cfg.vhost)
    #
    #         await client.start()
    #
    #
    #
    #         await client.stop()



    # async def test_publish_event(self, event_loop: AbstractEventLoop, rabbit):
    #
    #     async with rabbit() as cfg:
    #
    #         class TestEvent(Event):
    #             __domain_name__ = cfg.vhost
    #             field = fields.String()
    #
    #         event = TestEvent(field='test publish event')
    #
    #         # Make publisher
    #         mode = RabbitSelfDomainMode(cfg.vhost)
    #         client = RabbitDomainClient(cfg.url, mode)
    #         client.set_loop(event_loop)
    #         await client.start()
    #
    #         # Make consumer
    #
    #         await client.publish(event)
    #
    #         await client.stop()
    #         connections = [conn for conn in await cfg.client.list_connections()
    #                        if conn['vhost'] == cfg.vhost]
    #         assert len(connections) == 0





