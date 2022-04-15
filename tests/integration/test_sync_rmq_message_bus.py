import os

from aioddd_utils.domain_message import AbstractDomainMessage, Event, Command
from aioddd_utils.rmq_message_bus import SyncAMQPMessagebus, DomainBus


class TestSyncAMQPMessagebus:
    def test_init_arguments(self):
        mb = SyncAMQPMessagebus('test-domain', 'test-host', 1234, 'test-username', 'test-password')
        assert mb.self_domain == 'test-domain'
        params = mb.get_connection_params('ddd-test')
        assert params.host == 'test-host'
        assert params.port == 1234
        assert params._virtual_host == 'ddd-test'
        assert params.credentials.username == 'test-username'
        assert params.credentials.password == 'test-password'

    def test_read_config_from_environ(self, load_environment):
        import os
        os.environ['DDD_SELFDOMAIN'] = 'TEST_DDD_SELFDOMAIN'
        os.environ['DDD_MESSAGEBUS_HOST'] = 'amqp://test-host/'
        os.environ['DDD_MESSAGEBUS_PORT'] = '5678'
        os.environ['DDD_MESSAGEBUS_USERNAME'] = 'TEST_DDD_MESSAGEBUS_USERNAME'
        os.environ['DDD_MESSAGEBUS_PASSWORD'] = 'TEST_DDD_MESSAGEBUS_PASSWORD'
        mb = SyncAMQPMessagebus()
        params = mb.get_connection_params('ddd-test')
        assert mb.self_domain == 'TEST_DDD_SELFDOMAIN'
        assert params.host == 'amqp://test-host'
        assert params.port == 5678
        assert params.credentials.username == 'TEST_DDD_MESSAGEBUS_USERNAME'
        assert params.credentials.password == 'TEST_DDD_MESSAGEBUS_PASSWORD'

    def test_register(self, load_environment):
        class TestMessage1(AbstractDomainMessage):
            __domain_name__ = 'test1'

        class TestMessage2(AbstractDomainMessage):
            __domain_name__ = 'test1'

        class TestMessage3(AbstractDomainMessage):
            __domain_name__ = 'test2'

        mb = SyncAMQPMessagebus()
        mb.register(TestMessage1)
        mb.register(TestMessage2)
        mb.register(TestMessage3)

        assert set(mb.get_message_types_by_domain('test1')) == {TestMessage1, TestMessage2}
        assert set(mb.get_message_types_by_domain('test2')) == {TestMessage3}


class TestDomainBus:
    def test_init(self, load_environment):

        class TestEvent1(Event):
            __domain_name__ = 'ddd-test'

        class TestEvent2(Event):
            __domain_name__ = 'ddd-test'

        class TestCommand1(Command):
            __domain_name__ = 'ddd-test'

        class TestCommand2(Command):
            __domain_name__ = 'other-domain'

        mb = SyncAMQPMessagebus()
        mb.register(TestEvent1)
        mb.register(TestEvent2)
        mb.register(TestCommand1)
        mb.register(TestCommand2)

        db = DomainBus('ddd-test', mb)

        assert db.domain == 'ddd-test'
        assert db.connection_params
        assert db.connection_params._virtual_host == 'ddd-test'
        assert db.is_self_domain is True
        assert db.registered_events == {TestEvent1, TestEvent2}
        assert db.registered_commands == {TestCommand1}

    def test_start(self, load_environment):

        class TestEvent1(Event):
            __domain_name__ = 'ddd-test'

        class TestEvent2(Event):
            __domain_name__ = 'ddd-test'

        class TestCommand1(Command):
            __domain_name__ = 'ddd-test'

        mb1 = SyncAMQPMessagebus()
        mb1.register(TestEvent1)
        mb1.register(TestEvent2)
        mb1.register(TestCommand1)
        import os
        os.environ['DDD_SELFDOMAIN'] = 'TEST_DDD_SELFDOMAIN'

        mb2 = SyncAMQPMessagebus()
        mb2.register(TestEvent1)
        mb2.register(TestEvent2)
        mb2.register(TestCommand1)
        db1 = DomainBus('ddd-test', mb1, permanent_consume=False)
        db2 = DomainBus('ddd-test', mb2, permanent_consume=False)
        db1.start()
        db2.start()
        print()

