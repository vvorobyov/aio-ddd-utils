import asyncio
from asyncio import AbstractEventLoop

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

            mode = RabbitSelfDomainClient(cfg.vhost)
            client = AsyncRabbitMessageBus(cfg.url, mode)
            client.set_loop(event_loop)
            await client.start()

            assert client._connection.connected
            assert mode._command_exchange.name == 'commands'
            assert mode._event_exchange.name == 'events'
            assert mode._command_queue.name == 'commands'

            await client.stop()
            connections = [conn for conn in await cfg.client.list_connections()
                           if conn['vhost'] == cfg.vhost]
            assert len(connections) == 0

    async def test_start_and_stop_other_domain_client(self, event_loop: AbstractEventLoop, rabbit):
        async with rabbit() as cfg:
            self_domain = random_word()
            mode = RabbitOtherDomainClient(self_domain)
            client = AsyncRabbitMessageBus(cfg.url, mode)
            client.set_loop(event_loop)
            await client.start()

            assert client._connection.connected
            assert mode._event_queue.name == self_domain
            assert mode._command_exchange.name == 'commands'
            assert mode._response_queue.name != self_domain

            await client.stop()
            connections = [conn for conn in await cfg.client.list_connections()
                           if conn['vhost'] == cfg.vhost]
            assert len(connections) == 0

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





