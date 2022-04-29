import decimal
from dataclasses import dataclass, FrozenInstanceError
from datetime import datetime, timezone, time, date, timedelta
from decimal import Decimal
from urllib.parse import urlparse, ParseResult
from uuid import UUID

import attr
import pytest
import yarl

from dddmisc.messages import fields
from dddmisc.messages.core import Metadata, AbstractDomainMessage, DomainMessageMeta
from dddmisc.messages.core import get_message_class
from dddmisc.messages.domain_command import DomainCommand, DomainMessage


class TestFields:

    @pytest.mark.parametrize('field, value, result', [
        (fields.String(), 'Abc', 'Abc'),
        (fields.Uuid(), UUID('b4c21ca6-ffe1-4df4-a350-ad221b3dc26d'), UUID('b4c21ca6-ffe1-4df4-a350-ad221b3dc26d')),
        (fields.Integer(), 123, 123),
        (fields.Float(), 456.789, 456.789),
        (fields.Float(), 456, 456.0),
        (fields.Decimal(), '234.56', Decimal('234.56')),
        (fields.Decimal(2, decimal.ROUND_FLOOR), 234.56, Decimal('234.56').quantize(Decimal('0.01'))),
        (fields.Decimal(2), 234, Decimal('234.00')),
        (fields.Boolean(), True, True),
        (fields.Boolean(), "True", True),
        (fields.Boolean(), "t", True),
        (fields.Boolean(), "Yes", True),
        (fields.Boolean(), "Y", True),
        (fields.Boolean(), "On", True),
        (fields.Boolean(), "1", True),
        (fields.Boolean(), 1, True),
        (fields.Boolean(), False, False),
        (fields.Boolean(), "false", False),
        (fields.Boolean(), "f", False),
        (fields.Boolean(), "no", False),
        (fields.Boolean(), "n", False),
        (fields.Boolean(), "off", False),
        (fields.Boolean(), "0", False),
        (fields.Boolean(), 0, False),
        (fields.Datetime(), '2022-01-01T12:13:14', datetime(2022, 1, 1, 12, 13, 14).astimezone(timezone.utc)),
        (fields.Datetime(), '2022-01-02T12:13:14+03:00',
         datetime(2022, 1, 2, 12, 13, 14, tzinfo=timezone(timedelta(hours=3))).astimezone(timezone.utc)),
        (fields.Datetime(), datetime(2022, 1, 3, 12, 13, 14),
         datetime(2022, 1, 3, 12, 13, 14).astimezone(timezone.utc)),
        (fields.Datetime(), datetime(2022, 1, 4, 12, 13, 14, tzinfo=timezone(timedelta(hours=4))),
         datetime(2022, 1, 4, 8, 13, 14, tzinfo=timezone.utc)),
        (fields.Time(), '12:13:14', time(12, 13, 14)),
        (fields.Time(), time(12, 13, 15), time(12, 13, 15)),
        (fields.Date(), '2022-01-01', date(2022, 1, 1)),
        (fields.Date(), date(2022, 1, 2), date(2022, 1, 2)),
        (fields.Url(), 'https://www.example.com:80/test?search=123',
         yarl.URL('https://www.example.com:80/test?search=123')),
        (fields.Url(), yarl.URL('https://www.example.com:80/test?search=123'),
         yarl.URL('https://www.example.com:80/test?search=123')),
        (fields.Email(), 'user@example.com', 'user@example.com'),
        (fields.Email(), 'user@localhost', 'user@localhost'),
    ])
    def test_validate_value(self, field: fields.Field, value, result):
        field.__set_name__(None, 'test')
        assert field.validate_value_type(value) == result


class TestDomainMessageMeta:

    def test_set_default_metadata(self):
        class Test(metaclass=DomainMessageMeta):
            pass

        assert hasattr(Test, '__metadata__')
        assert isinstance(Test.__metadata__, Metadata)
        assert Test.__metadata__.domain is None
        assert Test.__metadata__.is_baseclass
        assert Test.__metadata__.fields == {}

    def test_set_metadata_from_meta(self):
        class Test(AbstractDomainMessage, metaclass=DomainMessageMeta):
            class Meta:
                is_baseclass = True
                domain = 'test-meta-class'

        assert Test.__metadata__.domain == 'test-meta-class'
        assert Test.__metadata__.is_baseclass

    def test_automatic_set_abstract_base_class(self):
        class Test(metaclass=DomainMessageMeta):
            pass

        assert issubclass(Test, AbstractDomainMessage)
        assert Test.__metadata__.domain is None
        assert Test.__metadata__.is_baseclass is True

    def test_inherit_metadata(self):
        class Test(AbstractDomainMessage, metaclass=DomainMessageMeta):
            class Meta:
                is_baseclass = True
                domain = 'test-meta-class'

        class Test2(Test): ...

        class Test3(Test):
            class Meta:
                is_baseclass = True
                domain = 'other-domain'

        assert Test2.__metadata__.domain == 'test-meta-class'
        assert Test2.__metadata__.is_baseclass is False
        assert Test3.__metadata__.domain == 'test-meta-class'
        assert Test3.__metadata__.is_baseclass

    def test_set_fields(self):
        class Test(AbstractDomainMessage, metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()
            other_str_fields = fields.String()

            class Meta:
                domain = 'test-set-fields'

        assert Test.__metadata__.fields == {
            '__reference__': Test.__reference__,
            '__timestamp__': Test.__timestamp__,
            'other_str_fields': Test.other_str_fields,
        }

    def test_inherit_fields(self):
        class Test(AbstractDomainMessage, metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()
            other_str_fields = fields.String()

        class Test2(Test):
            ...

        assert Test2.__metadata__.fields == {
            '__reference__': Test.__reference__,
            '__timestamp__': Test.__timestamp__,
            'other_str_fields': Test.other_str_fields,
        }

    def test_replace_inherit_fields(self):
        class Test(AbstractDomainMessage, metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()
            other_str_fields = fields.String()

        class Test2(Test):
            __timestamp__ = fields.Integer()

        assert Test2.__metadata__.fields == {
            '__reference__': Test.__reference__,
            '__timestamp__': Test2.__timestamp__,
            'other_str_fields': Test.other_str_fields,
        }

    def test_double_registered_class(self):
        def register_class():
            class Test(AbstractDomainMessage, metaclass=DomainMessageMeta):
                __reference__ = fields.Uuid()
                __timestamp__ = fields.Datetime()
                other_str_fields = fields.String()

                class Meta:
                    domain = 'test-double-register'

        register_class()
        with pytest.raises(RuntimeError,
                           match='Multiple message class in domain "test-double-register" with name "Test"'):
            register_class()

    def test_validators_on_init_class_instance(self):
        class Test(metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()
            other_str_fields = fields.String()
            test_nullable = fields.String(nullable=True)
            test_default = fields.Integer(default=100)

            class Meta:
                domain = 'test-validators-on-init-class-instance'

        obj = Test(other_str_fields='test')
        assert obj.other_str_fields == 'test'
        assert obj.test_nullable is None
        assert obj.test_default == 100

        with pytest.raises(FrozenInstanceError, match="cannot assign to field 'other_str_fields'"):
            obj.other_str_fields = 'Test'

        with pytest.raises(AttributeError, match='Not set required attributes other_str_fields'):
            Test()

    def test_init_baseclass(self):
        class Test(metaclass=DomainMessageMeta):
            pass

        with pytest.raises(TypeError, match="cannot create instance of 'Test' class, because this is BaseClass"):
            Test()

    def test_class_by_name(self):
        class Test1(metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()
            other_str_fields = fields.String()
            test_nullable = fields.String(nullable=True)
            test_default = fields.Integer(default=100)

            class Meta:
                domain = 'test_class_by_name'

        class Test2(metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()

            class Meta:
                domain = 'test_class_by_name'

        class Test3(metaclass=DomainMessageMeta):
            __reference__ = fields.Uuid()
            __timestamp__ = fields.Datetime()

            class Meta:
                domain = 'test_class_by_name2'

        assert get_message_class(('test_class_by_name', 'Test1')) is Test1
        assert get_message_class('test_class_by_name.Test1') is Test1
        assert get_message_class('test_class_by_name.Test2') is Test2
        assert get_message_class('test_class_by_name2.Test3') is Test3

        with pytest.raises(ValueError, match="Message class by 'test_class_by_name2.Test4' not found"):
            get_message_class('test_class_by_name2.Test4')


class TestDomainMessage:
    def test_load(self):
        test_data = {
            '__reference__': 'b4c21ca6-ffe1-4df4-a350-ad221b3dc26d',
            '__timestamp__': 1650819915.277321,
            'data': {
                'string_field': 'Abc',
                'uuid_field': '00000000-0000-0000-0000-000000000000',
                'integer_field': 123,
                'float_field': 456.789,
                'decimal_field': 456.783,
                'boolean_field': False,
                'datetime_field': '2022-04-24T17:18:35.865385+00:00',
                'time_field': '17:18:35.865385',
                'date_field': '2022-04-24',
                'url_field': 'http://example.com:80/test/path/',
                'email_field': 'test@example.com',
                # 'nested_field': None
                # 'list_field': [1,2,3,4,5]
                # 'dict_field': {'test': 'data'}
            }
        }

        class TestCommand(DomainMessage):
            string_field = fields.String()
            uuid_field = fields.Uuid()
            integer_field = fields.Integer()
            float_field = fields.Float()
            decimal_field = fields.Decimal(places=2)
            boolean_field = fields.Boolean()
            datetime_field = fields.Datetime()
            time_field = fields.Time()
            date_field = fields.Date()
            url_field = fields.Url()
            email_field = fields.Email()

            class Meta:
                domain = 'test-domain-command'

        obj = TestCommand.load(data=test_data)
        assert obj.__reference__ == UUID('b4c21ca6-ffe1-4df4-a350-ad221b3dc26d')
        assert obj.__timestamp__ == 1650819915.277321
        assert obj.string_field == 'Abc'
        assert obj.uuid_field == UUID('00000000-0000-0000-0000-000000000000')
        assert obj.integer_field == 123
        assert obj.float_field == 456.789
        assert obj.decimal_field == Decimal('456.78')
        assert obj.boolean_field is False
        assert obj.datetime_field == datetime(2022, 4, 24, 17, 18, 35, 865385, tzinfo=timezone.utc)
        assert obj.time_field == time(17, 18, 35, 865385)
        assert obj.date_field == date(2022, 4, 24)
        assert obj.url_field == yarl.URL('http://example.com:80/test/path/')
        assert obj.email_field == 'test@example.com'


