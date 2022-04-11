


from uuid import UUID

import pytest

from aioddd_utils.domain_message import BaseEvent, BaseCommand, get_message_class, fields as f


class TestDomainMessages:

    def test_message_meta(self):
        class TestEvent(BaseEvent):
            __domain_name__ = 'test'

            uuid_field = f.UUID()
            str_field = f.String()
            int_field = f.Integer()

        obj = TestEvent.load({
            'uuid_field': 'e13f492d-ab8c-40f8-a7f0-2818573cde67',
            'str_field': 'test abc',
            'int_field': 123,
            'other_data': 'fsdfsfsdf',
        })
        assert obj.uuid_field == UUID('e13f492d-ab8c-40f8-a7f0-2818573cde67')
        assert obj.int_field == 123
        assert obj.str_field == 'test abc'

        assert obj.dump() == {
            'uuid_field': 'e13f492d-ab8c-40f8-a7f0-2818573cde67',
            'str_field': 'test abc',
            'int_field': 123,
        }

    def test_message_meta_inheritance(self):
        class TestEvent(BaseEvent):
            __domain_name__ = 'test'

            uuid_field = f.UUID()
            str_field = f.String()
            int_field = f.Integer()

        class TestEventWithBool(TestEvent):
            bool_field = f.Boolean()

            @classmethod
            def load(cls, data):
                pass

            def dump(self, data):
                pass

        obj = TestEventWithBool.load({
            'uuid_field': 'e13f492d-ab8c-40f8-a7f0-2818573cde67',
            'str_field': 'test abc',
            'int_field': 123,
            'bool_field': 'false',
            'other_data': 'fsdfsfsdf',
        })

        assert obj.uuid_field == UUID('e13f492d-ab8c-40f8-a7f0-2818573cde67')
        assert obj.int_field == 123
        assert obj.str_field == 'test abc'
        assert obj.bool_field is False

        assert obj.dump() == {
            'uuid_field': 'e13f492d-ab8c-40f8-a7f0-2818573cde67',
            'str_field': 'test abc',
            'int_field': 123,
            'bool_field': False,
        }

    def test_not_set_domain_name(self):

        with pytest.raises(ValueError, match='Required set value to "__domain_name__" class attr for'):
            class TestEvent(BaseEvent):
                str_field = f.String()

    def test_get_document_class(self):
        from aioddd_utils.domain_message import messages
        messages.MESSAGES_REGISTRY = {}

        class TestEvent(BaseEvent):
            __domain_name__ = 'test'
            str_field = f.String()

        class TestCommand(BaseCommand):
            __domain_name__ = 'test'
            str_field = f.String()

        class TestCommand2(TestCommand):
            int_field = f.Integer()

        assert get_message_class('test', 'testevent') is TestEvent
        assert get_message_class('test', 'testcommand') is TestCommand
        assert get_message_class('test', 'testcommand2') is TestCommand2

