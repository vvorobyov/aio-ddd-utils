from dddmisc.exceptions import BaseDomainError
from dddmisc.exceptions.core import BaseDomainException, DomainExceptionMeta


class BaseRabbitError(BaseDomainException, metaclass=DomainExceptionMeta):

    class Meta:
        domain = '__ddd_rabbit__'
        is_baseclass = True


class IncomingMessageError(BaseRabbitError):
    """
    Базовый класс ошибок связаных с входящими сообщениями
    """

    class Meta:
        is_baseclass = True
        group_id = '01'


class UnknownMessageTypeError(IncomingMessageError):
    """
    Ошибка возникающая при получении сообщения неизвестного типа (properties.type)
    """

    class Meta:
        error_id = '01'


class NotRegisteredMessageClassError(IncomingMessageError):  # TODO перенести в блок ошибок базового модуля
    """
    Нет зарегистрированного класса объекта с заданным ключом
    """
    class Meta:
        error_id = '02'


class NotValidObjectType(IncomingMessageError):
    """
    Класс объекта с заданным ключом не соответствует типу указанном(properties.type) в сообщении
    """
    class Meta:
        error_id = '03'


class NotValidJsonError(IncomingMessageError):  # TODO перенести в блок ошибок базового модуля
    """
    Тело сообщения не является валидной json строкой
    """
    class Meta:
        error_id = '04'


class ValidationError(IncomingMessageError):  # TODO перенести в блок ошибок базового модуля
    """
    Ошибка десериалзиции сообщения в запрос
    """
    class Meta:
        error_id = '05'
