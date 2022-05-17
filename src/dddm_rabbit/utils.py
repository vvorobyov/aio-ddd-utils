from typing import TypeVar, Type, Any

from aio_pika.abc import AbstractIncomingMessage

from dddmisc.exceptions.core import BaseDDDException
from dddmisc.exceptions.errors import get_error_class
from dddmisc.messages import DDDCommand, get_message_class, DDDEvent, DDDResponse

T = TypeVar('T')


def _parse_domain_message(message: AbstractIncomingMessage) -> Any:
    klass = get_message_class(message.routing_key)
    obj = klass.loads(message.body.decode())
    return obj


def parse_command(message: AbstractIncomingMessage) -> DDDCommand:
    return _parse_domain_message(message)


def parse_event(message: AbstractIncomingMessage) -> DDDEvent:
    return _parse_domain_message(message)


def parse_response(message: AbstractIncomingMessage) -> DDDResponse:
    obj = DDDResponse.loads(message.body.decode())
    return obj


def parse_error(message: AbstractIncomingMessage) -> BaseDDDException:
    class_key = message.headers.get('X-DDD-OBJECT-KEY', None)
    klass = get_error_class(class_key)
    obj = klass.loads(message.body.decode())
    return obj