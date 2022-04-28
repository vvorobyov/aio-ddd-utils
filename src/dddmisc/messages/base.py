import abc
import typing as t
from types import MappingProxyType

from dddmisc.messages.abstract import AbstractDomainMessage, Metadata, AbstractField


def __make_register_functions():

    MESSAGE_REGISTER: t.Dict[t.Tuple[str, str], t.Type[AbstractDomainMessage]] = {}

    def register(klass: t.Type[AbstractDomainMessage]):
        if klass.__metadata__.is_baseclass:
            return
        domain = klass.__metadata__.domain
        name = klass.__name__
        if (domain, name) in MESSAGE_REGISTER:
            raise RuntimeError(f'Multiple message class in domain "{klass.__metadata__.domain}" with name "{name}"')
        MESSAGE_REGISTER[(domain, name)] = klass

    def get(key: t.Union[t.Tuple[str, str], str]) -> t.Type[AbstractDomainMessage]:
        if isinstance(key, str):
            domain, name = key.split('.')
            key_ = (domain, name)
        else:
            key_ = key
        if key_ in MESSAGE_REGISTER:
            return MESSAGE_REGISTER[key_]
        raise ValueError(f"Message class by '{key}' not found")

    return register, get


register_message_class, get_message_class = __make_register_functions()


class DomainMessageMeta(abc.ABCMeta):
    def __new__(mcs, name: str, bases: t.Tuple[t.Type], attrs: dict):
        domain_message_bases = [base for base in bases if issubclass(base, AbstractDomainMessage)]
        base_dm_count = len(domain_message_bases)
        if base_dm_count > 1:
            raise TypeError('Inherit from more one "AbstractDomainMessage" class')
        if base_dm_count == 0:
            bases = (AbstractDomainMessage, *bases)
            domain_message_bases = [AbstractDomainMessage]
        new_attrs = {**attrs}

        for key in ['Meta', 'load', 'loads', 'dump', 'dumps']:
            new_attrs.pop(key, None)

        new_attrs['__metadata__'] = mcs._get_metadata(domain_message_bases[0], **attrs)
        klass = super(DomainMessageMeta, mcs).__new__(mcs, name, bases, new_attrs)
        register_message_class(klass)  # noqa
        return klass

    @staticmethod
    def _get_metadata(base: t.Optional[t.Type[AbstractDomainMessage]], **attrs) -> Metadata:
        fields = {key: field for key, field in attrs.items() if isinstance(field, AbstractField)}
        meta_info = attrs.get('Meta', None)
        is_baseclass = getattr(meta_info, 'is_baseclass', False)
        base_metadata: Metadata = getattr(base, '__metadata__', None)
        domain = getattr(base_metadata, 'domain', None) or getattr(meta_info, 'domain', None)
        if domain is None:
            is_baseclass = True
        base_fields = dict(getattr(base_metadata, 'fields', {}))
        return Metadata(fields=MappingProxyType({**base_fields, **fields}),
                        domain=domain, is_baseclass=is_baseclass)

