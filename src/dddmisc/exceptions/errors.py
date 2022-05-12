import json
import typing as t
from .core import DDDExceptionMeta, BaseDDDException, DDDException


def get_error_class(key: str) -> t.Type[BaseDDDException]:
    collection = DDDExceptionMeta.get_exceptions_collection()
    if key in collection:
        return collection[key]
    raise UnregisteredMessageClass(f'Not found error class with key {key}')


def load_error(response: str) -> BaseDDDException:
    data = json.loads(response)
    code = data.get('code', None)
    domain = data.get('domain', None)
    error_class = get_error_class((domain, code))
    error = error_class.load(data)
    return error


class BaseDomainError(DDDException, metaclass=DDDExceptionMeta):
    pass


class BaseServiceError(DDDException, metaclass=DDDExceptionMeta):
    class Meta:
        domain = '__ddd_service__'
        is_baseclass = True


class UnregisteredErrorClass(BaseServiceError):
    class Meta:
        template = '91'


class UnregisteredMessageClass(BaseServiceError):
    class Meta:
        template = '92'


class JsonDecodeError(BaseServiceError):
    class Meta:
        template = '93'


class ValidationError(BaseServiceError):
    class Meta:
        template = '94'


class InternalServiceError(BaseServiceError):

    class Meta:
        template = '01'


# TODO дописать классы исключений




