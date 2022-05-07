from dddmisc.messages import DomainEvent, DomainCommand
from dddmisc.messagebus.base import BaseExternalMessageBus, EventConfigsCollection, CommandConfigsCollection


class TestBaseExternalMessageBus:
    def test_init(self):
        bus = BaseExternalMessageBus(domain='test')
        assert bus.domain == 'test'
        bus = BaseExternalMessageBus(domain='test2')
        assert bus.domain == 'test2'
        assert isinstance(bus._registered_domains, set)
        assert isinstance(bus._events_configs, EventConfigsCollection)
        assert isinstance(bus._commands_configs, CommandConfigsCollection)

    def test_consume_event(self):
        class TestEvent(DomainEvent):
            class Meta:
                domain = 'test-consume-event'

        class TestEvent2(DomainEvent):
            class Meta:
                domain = 'test-consume-event'

        class TestEvent3(DomainEvent):
            class Meta:
                domain = 'test-consume-event'

        handlers = [
            lambda event: None,
            lambda event: None,
            lambda event: None,
        ]

        bus = BaseExternalMessageBus(domain='test')
        bus.register_event_handlers(TestEvent, *handlers)
        bus.register_event_handlers(TestEvent2)
        assert list(bus._events_configs.get_events_by_domain_name('test-consume-event')) == [TestEvent, TestEvent2]
        assert list(bus._events_configs.get_events_by_domain_name('other-test-domain')) == []
        assert set(bus._events_configs.get_event_handlers(TestEvent)) == set(handlers)
        assert len(bus._events_configs.get_event_handlers(TestEvent)) == 3
        assert len(bus._events_configs.get_event_handlers(TestEvent2)) == 0
        assert TestEvent in bus._events_configs
        assert TestEvent() in bus._events_configs
        assert TestEvent2 in bus._events_configs
        assert TestEvent3 not in bus._events_configs

        handlers.append(lambda event: None)
        bus.register_event_handlers(TestEvent, *handlers)
        assert set(bus._events_configs.get_event_handlers(TestEvent)) == set(handlers)
        assert len(bus._events_configs.get_event_handlers(TestEvent)) == 4

    def test_consume_command(self):
        class TestCommand1(DomainCommand):
            class Meta:
                domain = 'test-consume-command'

        class TestCommand2(DomainCommand):
            class Meta:
                domain = 'test-consume-command'

        class TestCommand3(DomainCommand):
            class Meta:
                domain = 'test-consume-command'

        handler1 = lambda event: 1
        handler2 = lambda event: 2

        bus = BaseExternalMessageBus(domain='test')

        bus.register_command_handler(TestCommand1, handler1)
        bus.set_permission_for_command(TestCommand2, 'test')

        assert set(bus._commands_configs.get_commands_by_domain_name(
            'test-consume-command')) == {TestCommand1, TestCommand2}
        assert set(bus._commands_configs.get_commands_by_domain_name('test')) == set()

        assert bus._commands_configs.get_command_handler(TestCommand1) is handler1
        bus.register_command_handler(TestCommand1, handler2)
        assert bus._commands_configs.get_command_handler(TestCommand1) is handler2
        assert bus._commands_configs.get_command_handler(TestCommand2) is None

        assert bus._commands_configs.check_command_permission(TestCommand1, 'test') is False
        assert bus._commands_configs.check_command_permission(TestCommand2, 'test')
        bus.set_permission_for_command(TestCommand1, 'test')
        assert bus._commands_configs.check_command_permission(TestCommand1, 'test')

        assert bus._commands_configs.check_command_permission(TestCommand2, 'test2') is False
        bus.set_permission_for_command(TestCommand2, 'test2')
        assert bus._commands_configs.check_command_permission(TestCommand2, 'test2')

        assert TestCommand1 in bus._commands_configs
        assert TestCommand1() in bus._commands_configs
        assert TestCommand2 in bus._commands_configs
        assert TestCommand3 not in bus._commands_configs








