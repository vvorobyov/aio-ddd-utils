from dddmisc.domain_message import Event, Command
from dddmisc.messagebus.base import BaseExternalMessageBus, EventConfigsCollection, CommandConfigsCollection


class TestBaseExternalMessageBus:
    def test_init(self):
        bus = BaseExternalMessageBus(domain='test')
        assert bus.domain == 'test'
        bus = BaseExternalMessageBus(domain='test2')
        assert bus.domain == 'test2'
        assert isinstance(bus._registered_domains, set)
        assert isinstance(bus._events_handlers, EventConfigsCollection)
        assert isinstance(bus._commands_handlers, CommandConfigsCollection)

    def test_consume_event(self):
        class TestEvent(Event):
            __domain_name__ = 'test-consume-event'

        class TestEvent2(Event):
            __domain_name__ = 'test-consume-event'

        class TestEvent3(Event):
            __domain_name__ = 'test-consume-event'

        handlers = [
            lambda event: None,
            lambda event: None,
            lambda event: None,
        ]

        bus = BaseExternalMessageBus(domain='test')
        bus.consume_event(TestEvent, *handlers)
        bus.consume_event(TestEvent2)
        assert list(bus._events_handlers.get_events_by_domain_name('test-consume-event')) == [TestEvent, TestEvent2]
        assert list(bus._events_handlers.get_events_by_domain_name('other-test-domain')) == []
        assert set(bus._events_handlers.get_event_handlers(TestEvent)) == set(handlers)
        assert len(bus._events_handlers.get_event_handlers(TestEvent)) == 3
        assert len(bus._events_handlers.get_event_handlers(TestEvent2)) == 0
        assert TestEvent in bus._events_handlers
        assert TestEvent() in bus._events_handlers
        assert TestEvent2 in bus._events_handlers
        assert TestEvent3 not in bus._events_handlers

        handlers.append(lambda event: None)
        bus.consume_event(TestEvent, *handlers)
        assert set(bus._events_handlers.get_event_handlers(TestEvent)) == set(handlers)
        assert len(bus._events_handlers.get_event_handlers(TestEvent)) == 4

    def test_consume_command(self):
        class TestCommand1(Command):
            __domain_name__ = 'test-consume-command'

        class TestCommand2(Command):
            __domain_name__ = 'test-consume-command'

        class TestCommand3(Command):
            __domain_name__ = 'test-consume-command'

        handler1 = lambda event: 1
        handler2 = lambda event: 2

        bus = BaseExternalMessageBus(domain='test')

        bus.consume_command(TestCommand1, handler1)
        bus.set_permission_for_command(TestCommand2, 'test')

        assert set(bus._commands_handlers.get_commands_by_domain_name(
            'test-consume-command')) == {TestCommand1, TestCommand2}
        assert set(bus._commands_handlers.get_commands_by_domain_name('test')) == set()

        assert bus._commands_handlers.get_command_handler(TestCommand1) is handler1
        bus.consume_command(TestCommand1, handler2)
        assert bus._commands_handlers.get_command_handler(TestCommand1) is handler2
        assert bus._commands_handlers.get_command_handler(TestCommand2) is None

        assert bus._commands_handlers.check_command_permission(TestCommand1, 'test') is False
        assert bus._commands_handlers.check_command_permission(TestCommand2, 'test')
        bus.set_permission_for_command(TestCommand1, 'test')
        assert bus._commands_handlers.check_command_permission(TestCommand1, 'test')

        assert bus._commands_handlers.check_command_permission(TestCommand2, 'test2') is False
        bus.set_permission_for_command(TestCommand2, 'test2')
        assert bus._commands_handlers.check_command_permission(TestCommand2, 'test2')

        assert TestCommand1 in bus._commands_handlers
        assert TestCommand1() in bus._commands_handlers
        assert TestCommand2 in bus._commands_handlers
        assert TestCommand3 not in bus._commands_handlers








