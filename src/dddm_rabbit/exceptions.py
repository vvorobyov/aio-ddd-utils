from dddmisc.exceptions import BaseDomainError
from dddmisc.exceptions.core import BaseDDDException, DDDExceptionMeta


class BaseRabbitError(BaseDDDException, metaclass=DDDExceptionMeta):

    class Meta:
        domain = '__ddd_rabbit__'
        is_baseclass = True


class IncomingMessageError(BaseRabbitError):
    """
    Базовый класс ошибок связаных с входящими сообщениями
    """

    class Meta:
        is_baseclass = True


class UnknownMessageTypeError(IncomingMessageError):
    """
    Ошибка возникающая при получении сообщения неизвестного типа (properties.type)
    """
    def __init__(self, *args, message_type, **kwargs):
        super(UnknownMessageTypeError, self).__init__(*args, message_type=message_type, **kwargs)

    class Meta:
        template = 'Unknown message type: "{message_type}"'


class OutcomeMessageError(BaseRabbitError):
    """
    Базовый класс ошибок связанных с исходящим сообщением
    """

    class Meta:
        is_baseclass = True


class InvalidObjectTypeError(OutcomeMessageError):
    """
    Ошибка возникающая при получении объекта для отправки не известного типа
    """

    def __init__(self, *args, object_type, **kwargs):
        super().__init__(*args, object_type=object_type, **kwargs)

    class Meta:
        template = 'Invalid object type: "{object_type}"'


