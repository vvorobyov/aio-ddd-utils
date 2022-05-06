import asyncio
from asyncio import AbstractEventLoop
from datetime import datetime
from uuid import uuid4, UUID

import aio_pika
import pytest
from aio_pika import RobustExchange, RobustQueue
from aio_pika.abc import AbstractRobustExchange

from dddmisc.exceptions import InternalServiceError
from dddmisc.messages import DomainEvent, fields, DomainCommand, DomainCommandResponse
from dddmisc.messagebus.rabbitmq.domain_clients import RabbitSelfDomainClient, RabbitOtherDomainClient
from dddmisc.messagebus.rabbitmq import AsyncRabbitMessageBus
from integration.conftest import random_word


class TestRabbitDomainClient:

    async def test_publish_command_with_success_response(self, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestCommand(DomainCommand):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost
                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')
                results = []

                async def tst_cmd_handler(command: DomainCommand, publisher: str):
                    results.append((command, publisher))
                    return DomainCommandResponse(uuid4(), command.__reference__)

                cons_client = RabbitSelfDomainClient(
                    cfg1.url, self_domain=cfg1.vhost, connected_domain=cfg1.vhost,
                    events=[], commands=[TestCommand],
                    callback=tst_cmd_handler)
                pub_client = RabbitOtherDomainClient(
                    cfg2.url, self_domain=cfg2.vhost, connected_domain=cfg1.vhost,
                    events=[], commands=[],
                    callback=tst_cmd_handler)

                await cons_client.start()
                await pub_client.start()

                cmd = TestCommand(value='Abc')

                response = await asyncio.wait_for(pub_client.handle_command(cmd), 5)

                assert isinstance(response, DomainCommandResponse)
                assert response.__reference__ == cmd.__reference__
                assert isinstance(response.reference, UUID)
                assert len(results) == 1
                assert results[0] == (cmd, cfg2.vhost)
                # assert datetime.now().timestamp() - cmd.__timestamp__ == 0

                await pub_client.stop()
                await cons_client.stop()

    async def test_publish_command_with_timeout(self, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestCommand(DomainCommand):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost
                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')

                async def tst_cmd_handler(command: DomainCommand, publisher: str):
                    await asyncio.sleep(2)
                    return DomainCommandResponse(uuid4(), command.__reference__)

                cons_client = RabbitSelfDomainClient(
                    cfg1.url, self_domain=cfg1.vhost, connected_domain=cfg1.vhost,
                    events=[], commands=[TestCommand],
                    callback=tst_cmd_handler)
                pub_client = RabbitOtherDomainClient(
                    cfg2.url, self_domain=cfg2.vhost, connected_domain=cfg1.vhost,
                    events=[], commands=[],
                    callback=tst_cmd_handler)

                await cons_client.start()
                await pub_client.start()

                with pytest.raises(asyncio.TimeoutError):
                    cmd = TestCommand(value='Abc')
                    await pub_client.handle_command(cmd, 0.1)

                await pub_client.stop()
                await cons_client.stop()

    async def test_publish_command_with_error_response(self, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestCommand(DomainCommand):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost

                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')

                async def tst_cmd_handler(command: DomainCommand, publisher: str):
                    1/0

                cons_client = RabbitSelfDomainClient(
                    cfg1.url, self_domain=cfg1.vhost, connected_domain=cfg1.vhost,
                    events=[], commands=[TestCommand],
                    callback=tst_cmd_handler)
                pub_client = RabbitOtherDomainClient(
                    cfg2.url, self_domain=cfg2.vhost, connected_domain=cfg1.vhost,
                    events=[], commands=[],
                    callback=tst_cmd_handler)

                await cons_client.start()
                await pub_client.start()

                with pytest.raises(InternalServiceError):
                    cmd = TestCommand(value='Abc')
                    await pub_client.handle_command(cmd, 5)

                await pub_client.stop()
                await cons_client.stop()

    async def test_publish_event(self, event_loop: AbstractEventLoop, rabbit):

        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestEvent(DomainEvent):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost

                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')
                result = event_loop.create_future()

                async def tst_event_handler(event: DomainEvent, publisher: str):
                    result.set_result((event, publisher))

                pub_client = RabbitSelfDomainClient(
                    cfg1.url, self_domain=cfg1.vhost, connected_domain=cfg1.vhost,
                    events=[TestEvent], commands=[],
                    callback=tst_event_handler, loop=event_loop)
                cons_client = RabbitOtherDomainClient(
                    cfg2.url, self_domain=cfg2.vhost, connected_domain=cfg1.vhost,
                    events=[TestEvent], commands=[],
                    callback=tst_event_handler, loop=event_loop)

                await pub_client.start()
                await cons_client.start()

                tst_event = TestEvent(value='Abc')

                await asyncio.wait_for(pub_client.handle_event(tst_event), 5)

                result = await asyncio.wait_for(result, 5)

                assert result == (tst_event, cfg1.vhost)

                await pub_client.stop()
                await cons_client.stop()
