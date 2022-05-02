from .core import BaseDomainMessage, DomainMessageMeta


class DomainStructure(BaseDomainMessage, metaclass=DomainMessageMeta):
    class Meta:
        is_structure = True
        is_baseclass = True
