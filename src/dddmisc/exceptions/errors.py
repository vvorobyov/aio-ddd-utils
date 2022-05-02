import typing as t
from .core import DomainExceptionMeta, BaseDomainException


class BaseDomainError(BaseDomainException, metaclass=DomainExceptionMeta):
    class Meta:
        is_baseclass = True


def get_error_class(key: t.Union[t.Tuple[str, str], str]) -> t.Type[BaseDomainError]:
    if isinstance(key, str):
        domain, code = key.split('.')
        key = (domain, code)
    domain, code = key
    if code.startwith('00'):
        domain = '***'
    collection = DomainExceptionMeta.get_exception_collection()
    return collection.get((domain, code), UnknownCommonError)


class CommonDomainError(BaseDomainError):
    class Meta:
        is_baseclass = True
        domain = '***'
        group_id = '00'


class UnknownCommonError(CommonDomainError):
    class Meta:
        error_id = '01'


class InternalServiceError(CommonDomainError):

    class Meta:
        error_id = '02'

    @classmethod
    def from_exception(cls, error: Exception):
        obj = cls(str(error))
        return obj

# TODO дописать классы исключений




