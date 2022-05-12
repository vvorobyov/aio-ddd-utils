import json
from typing import TypeVar, Type

from aio_pika.abc import AbstractIncomingMessage

from dddm_rabbit import exceptions
from dddmisc.exceptions.core import BaseDDDException
from dddmisc.exceptions.errors import get_error_class
from dddmisc.messages import DomainCommand, get_message_class, DomainEvent, DomainCommandResponse

T = TypeVar('T')


def _parse_domain_message(message: AbstractIncomingMessage, type_: Type[T]) -> T:
    try:
        klass = get_message_class(message.routing_key)
        if not issubclass(klass, type_):
            raise exceptions.NotValidObjectType('Тип объекта не соответствует типу объекта указанному в сообщении')
        obj = klass.loads(message.body.decode())  # TODO ошибка разбора json, ошибка валидации
        return obj
    except ValueError as err:
        raise exceptions.NotRegisteredMessageClassError(str(err))


def parse_command(message: AbstractIncomingMessage) -> DomainCommand:
    return _parse_domain_message(message, DomainCommand)


def parse_event(message: AbstractIncomingMessage) -> DomainEvent:
    return _parse_domain_message(message, DomainEvent)


def parse_response(message: AbstractIncomingMessage) -> DomainCommandResponse:
    obj = DomainCommandResponse.loads(message.body.decode())
    return obj


def parse_error(message: AbstractIncomingMessage) -> BaseDDDException:
    class_key = message.headers.get('X-DDD-OBJECT-KEY', None)
    if class_key is None:
        raise exceptions.NotRegisteredMessageClassError('Не задан ключ идентификатор ошибка')
    klass = get_error_class(class_key)
    obj = klass.load(json.loads(message.body.decode())) # TODO ошибка разбора json, ошибка валидации
    return obj