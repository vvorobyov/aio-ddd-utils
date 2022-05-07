import asyncio
from asyncio import AbstractEventLoop
from uuid import uuid4, UUID

import pytest

from dddmisc.exceptions import InternalServiceError
from dddmisc.messages import DomainEvent, fields, DomainCommand, DomainCommandResponse
from dddm_rabbit import AsyncRabbitMessageBus


class TestAsyncRabbitMessageBus:
    async def test_publish_event(self, event_loop: AbstractEventLoop, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestEvent(DomainEvent):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost

                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')
                result = event_loop.create_future()

                async def tst_event_handler(event: DomainEvent):
                    result.set_result(event)

                self_mb = AsyncRabbitMessageBus(url=cfg1.url, domain=cfg1.vhost)
                other_mb = AsyncRabbitMessageBus(url=cfg2.url, domain=cfg2.vhost)

                other_mb.register_event_handlers(TestEvent, tst_event_handler)

                await self_mb.start()
                await other_mb.start()

                tst_event = TestEvent(value='Abc')

                await asyncio.wait_for(self_mb.handle(tst_event), 5)

                result = await asyncio.wait_for(result, 5)

                assert result == tst_event

                await self_mb.stop()
                await other_mb.stop()

    async def test_publish_command_with_success_response(self, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestCommand(DomainCommand):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost

                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')
                results = []

                async def tst_cmd_handler(command: DomainCommand):
                    results.append(command)
                    return DomainCommandResponse(uuid4(), command.__reference__)

                self_mb = AsyncRabbitMessageBus(url=cfg1.url, domain=cfg1.vhost)
                other_mb = AsyncRabbitMessageBus(url=cfg2.url, domain=cfg2.vhost)

                self_mb.register_command_handler(TestCommand, tst_cmd_handler)
                self_mb.set_permission_for_command(TestCommand, cfg2.vhost)
                other_mb.register_domains(cfg1.vhost)

                await self_mb.start()
                await other_mb.start()

                cmd = TestCommand(value='Abc')
                response = await asyncio.wait_for(other_mb.handle(cmd), 5)

                assert isinstance(response, DomainCommandResponse)
                assert response.__reference__ == cmd.__reference__
                assert isinstance(response.reference, UUID)
                assert len(results) == 1
                assert results[0] == cmd

                await self_mb.stop()
                await other_mb.stop()

    async def test_publish_command_with_timeout(self, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestCommand(DomainCommand):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost

                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')

                async def tst_cmd_handler(command: DomainCommand):
                    await asyncio.sleep(1)
                    return DomainCommandResponse(uuid4(), command.__reference__)

                self_mb = AsyncRabbitMessageBus(url=cfg1.url, domain=cfg1.vhost)
                other_mb = AsyncRabbitMessageBus(url=cfg2.url, domain=cfg2.vhost)

                self_mb.register_command_handler(TestCommand, tst_cmd_handler, cfg2.vhost)
                other_mb.register_domains(cfg1.vhost)

                await self_mb.start()
                await other_mb.start()

                with pytest.raises(asyncio.TimeoutError):
                    cmd = TestCommand(value='Abc')
                    await other_mb.handle(cmd, 0.1)

                await other_mb.stop()
                await self_mb.stop()

    async def test_publish_command_with_error_response(self, rabbit):
        async with rabbit() as cfg1:
            async with rabbit() as cfg2:
                class TestCommand(DomainCommand):
                    value = fields.String()

                    class Meta:
                        domain = cfg1.vhost

                await cfg1.client.create_user_permission(cfg2.vhost, cfg1.vhost, '.*', '.*', '.*')

                async def tst_cmd_handler(command: DomainCommand):
                    1 / 0

                self_mb = AsyncRabbitMessageBus(url=cfg1.url, domain=cfg1.vhost)
                other_mb = AsyncRabbitMessageBus(url=cfg2.url, domain=cfg2.vhost)

                self_mb.register_command_handler(TestCommand, tst_cmd_handler, cfg2.vhost)
                other_mb.register_domains(cfg1.vhost)

                await self_mb.start()
                await other_mb.start()

                with pytest.raises(InternalServiceError):
                    cmd = TestCommand(value='Abc')
                    await other_mb.handle(cmd, 5)

                await self_mb.stop()
                await other_mb.stop()
