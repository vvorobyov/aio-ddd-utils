import json
import typing as t
import warnings
from dataclasses import dataclass
from uuid import UUID
import datetime as dt
from types import MappingProxyType

from dddmisc.messages import DomainCommand


@dataclass(frozen=True)
class Metadata:
    domain: str
    group_id: str
    error_id: str
    is_baseclass: bool

    @property
    def code(self):
        return f'{self.group_id}{self.error_id}'


T = t.TypeVar('T')


class BaseDomainException(BaseException):
    __metadata__: Metadata

    def __init__(self, message: str, **extra):
        self._message: str = message
        self._extra: dict = extra
        self._code: str = self.__metadata__.code
        self._domain: t.Optional[str] = self.__metadata__.domain
        self._timestamp: float = dt.datetime.now().timestamp()
        self._reference: t.Optional[UUID] = None

    def set_command_context(self, command: DomainCommand):
        self._reference = command.__reference__
        self._domain = command.get_domain_name()

    def __repr__(self):
        return '{name}(domain={domain}, code={code}): {message}.'.format(
            name=self.__class__.__name__,
            domain=self._domain if self._domain else '"domain not set"',
            message=self._message,
            code=self._code
        )

    @property
    def __reference__(self) -> UUID:
        return self._reference

    @property
    def __timestamp__(self) -> float:
        return self._timestamp

    @property
    def message(self) -> str:
        return self._message

    @property
    def extra(self) -> MappingProxyType[str, t.Any]:
        return MappingProxyType(self._extra)

    def dump(self) -> dict:
        return dict(
            reference=str(self.__reference__),
            timestamp=self.__timestamp__,
            data=self._extra,
            message=self.message,
            code=self._code,
            domain=self._domain
        )

    def dumps(self) -> str:
        data = self.dump()
        return json.dumps(data)

    @classmethod
    def load(cls: t.Type[T], data: dict) -> T:
        message = data.get('message', '')
        extra = data.get('data', {})
        error: BaseDomainException = cls(message, **extra)

        reference = data.get('reference', None)
        error._reference = UUID(reference) if reference else None
        error._timestamp = data.get('timestamp')
        if error._domain == '***':
            error._domain = data.get('domain')
            error._code = data.get('code')
        return error


class DomainExceptionMeta(type):
    __EXCEPTIONS_COLLECTION: dict[t.Tuple[str, str], t.Type[BaseDomainException]] = {}

    def __new__(mcs, name: str, bases: t.Tuple[t.Type], attrs: dict) -> BaseDomainException:
        module = attrs.get('__module__')
        fullname = f'{module}.{name}'
        base_class = mcs._get_base_class(fullname, bases)
        if base_class not in bases:
            bases = (base_class, *bases)
        attrs['__metadata__'] = mcs._create_metadata(fullname, base_class, attrs.get('Meta', None))
        klass = super().__new__(mcs, name, bases, attrs)
        mcs._register_error_class(klass)
        return klass

    @staticmethod
    def _create_metadata(name: str, base: t.Type[BaseDomainException], meta: t.Type) -> Metadata:
        base_meta = getattr(base, '__metadata__', Metadata(None, None, None, True))
        if base_meta.is_baseclass is False:
            raise RuntimeError(f'Cannot inherit {name} from {base!r}. Allowed inherit only from base classes.')

        class_domain = base_meta.domain or getattr(meta, 'domain', None)
        class_group_id = getattr(meta, 'group_id', None)
        class_error_id = getattr(meta, 'error_id', None)
        is_baseclass = getattr(meta, 'is_baseclass', False)
        if is_baseclass:
            domain = base_meta.domain or class_domain
            group_id = base_meta.group_id or class_group_id
            if group_id == '00' and domain != '***':
                raise RuntimeError(f'Error create class {name}({base.__name__}). '
                                   f'Error group id "00" reserved for common errors.')
            error_id = '00'
            if class_error_id:
                warnings.warn(RuntimeWarning(f'Attribute Meta.error_id ignored for class "{name}".'))
        else:
            domain = base_meta.domain
            if domain is None:
                raise RuntimeError(f'Error create class {name}({base.__name__}). '
                                   f'Can inherit errors class only from classes with attribute "Meta.domain".')

            group_id = base_meta.group_id
            if class_group_id and class_group_id != group_id:
                warnings.warn(RuntimeWarning(f'Attribute Meta.group_id ignored for class "{name}".'))

            error_id = class_error_id
            if error_id is None:
                raise RuntimeError(f'Required set Meta.error_id for {name} class.')
            if error_id == '00':
                raise RuntimeError(f'Error create class {name}. Meta.error_id="00" reserved for base classes.')

        return Metadata(domain, group_id, error_id, is_baseclass)

    @staticmethod
    def _get_base_class(name: str, bases: t.Tuple[t.Type]) -> t.Type[BaseDomainException]:
        domain_bases = [base for base in bases if issubclass(base, BaseDomainException)]
        if len(domain_bases) > 1:
            raise RuntimeError(f'{name} inherit from many "BaseDomainException" classes')
        elif len(domain_bases) == 0:
            return BaseDomainException
        else:
            return domain_bases[0]

    @classmethod
    def _register_error_class(mcs, klass: t.Type[BaseDomainException]):
        if not issubclass(klass, BaseDomainException) or klass.__metadata__.is_baseclass:
            return
        domain = klass.__metadata__.domain
        code = klass.__metadata__.code
        if (domain, code) is mcs.__EXCEPTIONS_COLLECTION:
            raise RuntimeError(
                f'Multiple register error class in domain "{klass.__metadata__.domain}" with code "{code}"')
        mcs.__EXCEPTIONS_COLLECTION[(domain, code)] = klass

    @classmethod
    def get_exception_collection(mcs) -> MappingProxyType[t.Tuple[str, str], t.Type[BaseDomainException]]:
        return MappingProxyType(mcs.__EXCEPTIONS_COLLECTION)

