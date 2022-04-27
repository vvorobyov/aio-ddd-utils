import decimal
from datetime import datetime, timezone, time, date
from decimal import Decimal
from urllib.parse import urlparse, ParseResult
from uuid import UUID

import pytest

from dddmisc.messages import fields
from dddmisc.messages.domain_command import DomainCommand


class TestFields:
    @pytest.mark.parametrize('klass, value, result', [
        (fields.String(), 'Abc', 'Abc'),
        (fields.Uuid(), 'b4c21ca6-ffe1-4df4-a350-ad221b3dc26d', UUID('b4c21ca6-ffe1-4df4-a350-ad221b3dc26d')),
        (fields.Integer(), 123, 123),
        (fields.Integer(), '123', 123),
        (fields.Float(), 456.789, 456.789),
        (fields.Float(), '456.789', 456.789),
        (fields.Decimal(2, decimal.ROUND_FLOOR), '234.56', Decimal('234.56')),
        (fields.Decimal(2, decimal.ROUND_FLOOR), 234.56, Decimal('234.56')),
        (fields.Boolean(), False, False),
        (fields.Boolean(), True, True),
        (fields.Datetime(), '2022-04-24T17:18:35.865385+00:00',
         datetime(2022, 4, 24, 17, 18, 35, 865385, tzinfo=timezone.utc)),
        (fields.Time(), '17:18:35.865385', time(17, 18, 35, 865385)),
        (fields.Date(), '2022-04-24', date(2022, 4, 24)),
        (fields.Url(), 'http://example.com:80/test/path/', ParseResult(scheme='http', netloc='example.com:80',
                                                                       path='/test/path/', params='',
                                                                       query='', fragment='')),
        (fields.Email(), 'test@example.com',
         'test@example.com'),
    ])
    def test_success_serialize(self, klass, value, result):
        assert klass.serialize(value) == result


class TestDomainCommand:
    def test_load_command(self):
        test_data = {
            '__reference__': 'b4c21ca6-ffe1-4df4-a350-ad221b3dc26d',
            '__timestamp__': 1650819915.277321,
            'data': {
                'string_field': 'Abc',
                'uuid_field': '00000000-0000-0000-0000-000000000000',
                'integer_field': 123,
                'float_field': 456.789,
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

        class TestCommand(DomainCommand):
            string_field = fields.String()
            uuid_field = fields.Uuid()
            integer_field = fields.Integer()
            float_field = fields.Float()
            decimal_field = fields.Decimal()
            boolean_field = fields.Boolean()
            datetime_field = fields.Datetime()
            time_field = fields.Time()
            date_field = fields.Date()
            url_field = fields.Url()
            email_field = fields.Email()

            class Meta:
                domain = 'test-domain-command'

        obj = TestCommand.load(data=test_data)
        assert obj.reference == UUID('b4c21ca6-ffe1-4df4-a350-ad221b3dc26d')
        assert obj.timestamp == datetime(2022, 4, 24, 17, 5, 15, 277321, tzinfo=timezone.utc)
        assert obj.string_field == 'Abc'
        assert obj.uuid_field == UUID('00000000-0000-0000-0000-000000000000')
        assert obj.integer_field == 123
        assert obj.float_field == 456.789
        assert obj.boolean_field is False
        assert obj.datetime_field == datetime(2022, 4, 24, 17, 18, 35, 865385, tzinfo=timezone.utc)
        assert obj.time_field == time(17, 18, 35, 865385)
        assert obj.date_field == date(2022, 4, 24)
        assert obj.url_field == urlparse('http://example.com:80/test/path/')
        assert obj.email == 'test@example.com'

