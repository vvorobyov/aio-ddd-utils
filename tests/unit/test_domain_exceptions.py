from uuid import uuid4

import pytest

from dddmisc.exceptions import BaseDomainError, JsonDecodeError
from dddmisc.exceptions.core import DDDException, DDDExceptionMeta, BaseDDDException


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
                domain = 'test_load_and_dumps_exception'
                is_baseclass = True

        class TestError(BaseTestError):
            class Meta:
                domain = 'test_load_and_dumps_exception'
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

    def test_set_reference(self):
        class TestError(DDDException):
            class Meta:
                domain = 'test_set_reference'

        ref = uuid4()

        err = TestError()
        err.set_reference(ref)
        assert err.__reference__ == ref

        err = TestError()
        err.set_reference(str(ref))
        assert err.__reference__ == ref

        with pytest.raises(TypeError):
            err = TestError()
            err.set_reference(123)

    def test_raise_internal_json_decode_error(self):
        class TestError(DDDException):
            class Meta:
                domain = 'test_raise_internal_json_decode_error'

        with pytest.raises(JsonDecodeError):
            TestError.loads('{')

    def test_repr_exception(self):
        class TestError(DDDException):
            pass

        err = TestError('Test error message')
        assert repr(err) == 'TestError(domain="domain not set"): Test error message.'

        class TestError2(DDDException):
            class Meta:
                domain = 'test_repr_exception'

        err = TestError2('Test error message')
        assert repr(err) == 'TestError2(domain="test_repr_exception"): Test error message.'

    def test_automation_set_baseclass(self):
        class TestError(metaclass=DDDExceptionMeta):
            ...

        assert issubclass(TestError, BaseDDDException)

    def test_except_inherit_from_no_base_class(self):
        class TestError1(DDDException):
            class Meta:
                domain = 'test_except_inherit_from_no_base_class'

        with pytest.raises(RuntimeError, match='Allowed inherit only from base classes.'):
            class TestError2(TestError1):
                ...

    def test_many_inheritance(self):
        class TestError1(DDDException):
            class Meta:
                domain = 'test_many_inheritance'
                is_baseclass = True

        class TestError2(DDDException):
            class Meta:
                domain = 'test_many_inheritance'
                is_baseclass = True

        with pytest.raises(RuntimeError, match='inherit from many "BaseDDDException" classes'):
            class Test3(TestError1, TestError2):
                ...

    def test_duplicate_class_register(self):
        def create_class():
            class TestError(DDDException):
                class Meta:
                    domain = 'test_duplicate_class_register'

        create_class()
        with pytest.raises(RuntimeError, match="Multiple register error class in domain"):
            create_class()

