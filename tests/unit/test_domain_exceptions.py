import pytest

from dddmisc.exceptions import BaseDomainError
from dddmisc.exceptions.core import BaseDomainException


class TestExceptions:

    def test_create_metadata(self):
        class BaseTestError(BaseDomainError):
            class Meta:
                domain = 'test_create_metadata'
                group_id = '01'
                error_id = '01'
                is_baseclass = True

        assert issubclass(BaseTestError, BaseDomainException)
        assert BaseTestError.__metadata__.error_id == '00'
        assert BaseTestError.__metadata__.group_id == '01'
        assert BaseTestError.__metadata__.domain == 'test_create_metadata'
        assert BaseTestError.__metadata__.is_baseclass

    def test_metadata_inherit_error_class(self):
        class BaseTestError(BaseDomainError):
            class Meta:
                domain = 'test_metadata_inherit_error_class'
                group_id = '01'
                is_baseclass = True

        class BaseTestInheritError(BaseTestError):
            class Meta:
                domain = 'test_metadata_inherit_error_class'
                error_group = '02'
                error_id = '01'

        assert BaseTestInheritError.__metadata__.error_id == '01'
        assert BaseTestInheritError.__metadata__.group_id == '01'
        assert BaseTestInheritError.__metadata__.domain == 'test_metadata_inherit_error_class'
        assert BaseTestInheritError.__metadata__.is_baseclass is False

    def test_error_inherit_error_from_base_class_without_domain(self):
        with pytest.raises(RuntimeError,
                           match='Can inherit errors class only from classes with attribute "Meta.domain".'):
            class BaseTestInheritError(BaseDomainError):
                class Meta:
                    domain = 'test_error_inherit_error_from_base_class_without_error_group'
                    error_id = '01'

    def test_error_inherit_from_no_base_error_class(self):
        class BaseTestError(BaseDomainError):
            class Meta:
                domain = 'test_error_inherit_from_no_base_error_class'
                group_id = '01'
                is_baseclass = True

        class BaseTestInheritError(BaseTestError):
            class Meta:
                domain = 'test_error_inherit_from_no_base_error_class'
                group_id = '02'
                error_id = '01'

        with pytest.raises(RuntimeError, match="Allowed inherit only from base classes."):
            class BaseTestInheritError2(BaseTestInheritError):
                class Meta:
                    domain = 'test_error_inherit_from_no_base_error_class'
                    group_id = '02'
                    error_id = '01'

    def test_error_create_no_base_class_with_error_id_00(self):
        class BaseTestError(BaseDomainError):
            class Meta:
                domain = 'test_error_create_no_base_class_with_error_id_00'
                group_id = '01'
                is_baseclass = True

        with pytest.raises(RuntimeError, match='Meta.error_id="00" reserved for base classes.'):
            class BaseTestInheritError(BaseTestError):
                class Meta:
                    domain = 'test_error_create_no_base_class_with_error_id_00'
                    group_id = '02'
                    error_id = '00'



