import json
import typing as t
from dataclasses import dataclass
from uuid import UUID, uuid4
import datetime as dt
from types import MappingProxyType

from dddmisc.abstract import CrossDomainObjectProtocol


@dataclass(frozen=True)
class Metadata:
    domain: str
    is_baseclass: bool
    template: str = ''


T = t.TypeVar('T')


class BaseDDDException(Exception):
    __metadata__: Metadata

    def __init__(self, message: str = None, **extra):
        self._message: str = message or self.__metadata__.template.format(**extra)
        self._extra: dict = extra
        self._timestamp: float = dt.datetime.now().timestamp()
        self._reference: t.Optional[UUID] = uuid4()
        self._domain = None

    @property
    def __reference__(self) -> UUID:
        return self._reference

    @property
    def __timestamp__(self) -> float:
        return self._timestamp

    @property
    def __domain__(self) -> str:
        return self.__metadata__.domain

    @property
    def message(self) -> str:
        return self._message

    @property
    def extra(self) -> MappingProxyType[str, t.Any]:
        return MappingProxyType(self._extra)

    def set_context_from_command(self, command: CrossDomainObjectProtocol):
        self.set_reference(command.__reference__)

    def set_reference(self, reference: t.Union[UUID, str]):
        if isinstance(reference, str):
            reference = UUID(reference)
        if isinstance(reference, UUID):
            self._reference = reference
        else:
            raise TypeError(f"the reference mast be str or UUID, not {type(reference)!r}")

    def dump(self) -> dict:
        return dict(
            reference=str(self.__reference__),
            timestamp=self.__timestamp__,
            data=self._extra,
            message=self.message,
            domain=self._domain
        )

    def dumps(self) -> str:
        data = self.dump()
        return json.dumps(data)

    @classmethod
    def load(cls: t.Type[T], data: dict) -> T:
        message = data.get('message', '')
        extra = data.get('data', {})
        error: BaseDDDException = cls(message, **extra)
        error._reference = UUID(data['reference'])
        error._timestamp = data['timestamp']
        error._domain = data['domain']
        return error

    @classmethod
    def loads(cls: t.Type[T], data: str) -> T:
        from .errors import JsonDecodeError
        try:
            data = json.loads(data)
            return cls.load(data)
        except json.JSONDecodeError as err:
            raise JsonDecodeError(str(err))

    def __repr__(self):
        domain = self.__domain__
        return '{name}(domain="{domain}"): {message}.'.format(
            name=self.__class__.__name__,
            domain=domain if domain else 'domain not set',
            message=self._message,
        )


class DDDExceptionMeta(type):
    __EXCEPTIONS_COLLECTION: dict[str, t.Type[BaseDDDException]] = {}

    def __new__(mcs, name: str, bases: t.Tuple[t.Type], attrs: dict) -> BaseDDDException:
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
    def _create_metadata(name: str, base: t.Type[BaseDDDException], meta: t.Type) -> Metadata:
        base_meta = getattr(base, '__metadata__', Metadata(None, True))
        if base_meta.is_baseclass is False:
            raise RuntimeError(f'Cannot inherit {name} from {base!r}. Allowed inherit only from base classes.')

        is_baseclass = getattr(meta, 'is_baseclass', False)
        domain = base_meta.domain or getattr(meta, 'domain', None)
        if domain is None:
            is_baseclass = True
        template = getattr(meta, 'template', '')

        return Metadata(domain, is_baseclass, template)

    @staticmethod
    def _get_base_class(name: str, bases: t.Tuple[t.Type]) -> t.Type[BaseDDDException]:
        domain_bases = [base for base in bases if issubclass(base, BaseDDDException)]
        if len(domain_bases) > 1:
            raise RuntimeError(f'{name} inherit from many "BaseDDDException" classes')
        elif len(domain_bases) == 0:
            return BaseDDDException
        else:
            return domain_bases[0]

    @classmethod
    def _register_error_class(mcs, klass: t.Type[BaseDDDException]):
        if not issubclass(klass, BaseDDDException) or klass.__metadata__.is_baseclass:
            return
        domain = klass.__domain__
        name = klass.__name__
        key = f'{domain}.{name}'
        if key in mcs.__EXCEPTIONS_COLLECTION:
            raise RuntimeError(
                f'Multiple register error class in domain "{domain}" with name "{name}"')
        mcs.__EXCEPTIONS_COLLECTION[key] = klass

    @classmethod
    def get_exceptions_collection(mcs) -> MappingProxyType[str, t.Type[BaseDDDException]]:
        return MappingProxyType(mcs.__EXCEPTIONS_COLLECTION)

    @property
    def __domain__(cls: BaseDDDException) -> str:
        return cls.__metadata__.domain


class DDDException(BaseDDDException, metaclass=DDDExceptionMeta):
    pass
