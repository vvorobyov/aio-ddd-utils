import pytest

from dddmisc.exceptions import BaseDomainError
from dddmisc.exceptions.core import DDDException


class TestDDDException:
    def test_create_baseclass_of_exception(self):
        class BaseTestError(DDDException):
            class Meta:
                domain = 'test_create_base_exception_class'
                is_baseclass = True

        assert issubclass(BaseTestError, DDDException)
        assert BaseTestError.__domain__ == 'test_create_base_exception_class'
        assert BaseTestError not in DDDException.get_exceptions_collection().values()

    def test_create_not_baseclass_of_exception(self):
        class BaseTestError(DDDException):
            class Meta:
                domain = 'test_create_not_baseclass_of_exception'
                is_baseclass = True

        class TestError(BaseTestError):
            class Meta:
                template = 'test_create_not_baseclass_of_exception'

        assert issubclass(TestError, DDDException)
        assert TestError.__domain__ == 'test_create_not_baseclass_of_exception'
        assert TestError in DDDException.get_exceptions_collection().values()
        assert TestError().message == 'test_create_not_baseclass_of_exception'

    def test_fail_redeclare_domain_in_inherit_class(self):
        class BaseTestError(DDDException):
            class Meta:
                domain = 'test_fail_redeclare_domain_and_group_in_inherit_class'

                is_baseclass = True

        class TestError(BaseTestError):
            class Meta:
                domain = 'test_fail_redeclare_domain_and_group_in_inherit_class1'

        assert BaseTestError.__domain__ == TestError.__domain__

    def test_load_and_dumps_exception(self):
        class BaseTestError(DDDException):
            class Meta:
                domain = 'test_fail_redeclare_domain_and_group_in_inherit_class'
                is_baseclass = True

        class TestError(BaseTestError):
            class Meta:
                domain = 'test_fail_redeclare_domain_and_group_in_inherit_class1'
                template = 'test {field1}'

        error = TestError(field1='TEST')

        restored_error = TestError.loads(error.dumps())

        assert error.__reference__
        assert error.__reference__ == restored_error.__reference__
        assert error.__timestamp__
        assert error.__timestamp__ == restored_error.__timestamp__
        assert error.__domain__
        assert error.__domain__ == restored_error.__domain__
        assert error.message
        assert error.message == restored_error.message
        assert error.extra
        assert error.extra == restored_error.extra

    def test_automatic_set_is_baseclass_without_domain(self):
        class BaseTestInheritError(DDDException):
            class Meta:
                is_baseclass = False

        assert BaseTestInheritError.__metadata__.is_baseclass






