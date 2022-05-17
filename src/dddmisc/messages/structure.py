from dddmisc.messages.core import BaseDDDMessage, DDDMessageMeta


class DDDStructure(BaseDDDMessage, metaclass=DDDMessageMeta):
    class Meta:
        is_structure = True
        is_baseclass = True
