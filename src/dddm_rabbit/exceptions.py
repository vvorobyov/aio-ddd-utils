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


class NotValidJsonError(IncomingMessageError):  # TODO перенести в блок ошибок базового модуля
    """
    Тело сообщения не является валидной json строкой
    """


