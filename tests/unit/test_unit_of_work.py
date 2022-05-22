import typing as t
from uuid import UUID, uuid4

import pytest

from dddmisc.messagebus.abstract import AbstractSyncRepository, A, AbstractSyncUnitOfWork, T
from dddmisc.aggregate import BaseAggregate
from dddmisc.messages import DDDEvent, fields


class TestEvent(DDDEvent):
    value = fields.String()

    class Meta:
        is_baseclass = False
        domain = 'test_unit_of_work'


class TestAggregate(BaseAggregate):
    def __init__(self, values=None, **kwargs):
        self.values = values or []
        super(TestAggregate, self).__init__(**kwargs)

    def add_value(self, value):
        self.values.append(value)
        self.add_aggregate_event(TestEvent(value=value))


class TestAbstractAggregate:

    def test_automation_set_reference(self):
        aggr = TestAggregate()
        assert isinstance(aggr.reference, UUID)

    def test_set_argument_reference(self):
        ref = uuid4()
        aggr = TestAggregate(reference=ref)
        assert aggr.reference is ref

    def test_collect_events(self):
        event = TestEvent(value='123')
        aggr = TestAggregate()
        aggr.add_aggregate_event(event)
        assert aggr.get_aggregate_events() == (event,)

    def test_clear_events_when_get_events_from_aggregate(self):
        event = TestEvent(value='123')
        aggr = TestAggregate()
        aggr.add_aggregate_event(event)
        aggr.get_aggregate_events()
        assert aggr.get_aggregate_events() == ()

    def test_equal_aggregate(self):
        aggr1 = TestAggregate()
        aggr2 = TestAggregate(reference=aggr1.reference)
        assert aggr1 == aggr2
        assert aggr1 is not aggr2
        assert hash(aggr1) == hash(aggr2)

    def test_collect_aggregate(self):
        aggr1 = TestAggregate()
        aggr2 = TestAggregate()
        aggr3 = TestAggregate(reference=aggr1.reference)
        _ = {aggr1, aggr2, aggr3}
        assert {aggr1, aggr2, aggr3} == {aggr1, aggr2}

    def test_equal_collection_of_aggregate(self):
        aggr1 = TestAggregate()
        aggr2 = TestAggregate()
        assert aggr1 == aggr1
        assert {aggr1} == {aggr1}
        assert {aggr1, aggr2} == {aggr2, aggr1}

    def test_not_add_to_set_aggregate_with_equal_reference_if_aggregate_exist_in_set(self):
        aggr1 = TestAggregate()
        aggr2 = TestAggregate(reference=aggr1.reference)

        aggrs = {aggr1}
        aggrs.add(aggr2)
        assert aggrs.pop() is aggr1


class TestRepository(AbstractSyncRepository[TestAggregate, str]):
    aggregate_class = TestAggregate

    def __init__(self, connection, *aggrs):
        self.storage = set(aggrs)
        super(TestRepository, self).__init__(connection)

    def _add_to_storage(self, aggregate):
        self.storage.add(aggregate)

    def _get_from_storage(self, reference: UUID):
        return next(aggregate for aggregate in self.storage if aggregate.reference)


class TestAbstractSyncRepository:

    def test_get_aggregate_from_storage(self):
        aggregate = TestAggregate()
        repository = TestRepository('', aggregate)
        assert repository.get(aggregate.reference) == aggregate

    def test_raise_error_if_aggregate_not_exist_in_storage(self):
        repository = TestRepository('')
        with pytest.raises(Exception):
            repository.get(uuid4())

    def test_add_aggregate_to_repository_cache(self):
        aggregate = TestAggregate()
        repository = TestRepository('')
        repository.add(aggregate)
        assert repository.storage == set()

    def test_get_aggregate_from_cash_without_save_to_storage(self):
        aggregate = TestAggregate()
        repository = TestRepository('')
        repository.add(aggregate)
        assert repository.get(aggregate.reference) is aggregate

    def test_save_aggregate_to_storage(self):
        aggregate = TestAggregate()
        repository = TestRepository('')
        repository.add(aggregate)
        repository.apply_changes()
        assert repository.storage == {aggregate}

    def test_collect_events_from_repository(self):
        aggregate = TestAggregate()
        repository = TestRepository('')
        repository.add(aggregate)
        event1 = TestEvent(value='value1')
        aggregate.add_aggregate_event(event1)
        assert repository.events == set()
        repository.apply_changes()
        assert repository.events == {event1}
        event2 = TestEvent(value='value2')
        aggregate.add_aggregate_event(event2)
        repository.apply_changes()
        assert repository.events == {event1, event2}


class TestUnitOfWork(AbstractSyncUnitOfWork[TestRepository, str]):
    repository_class = TestRepository

    def __init__(self, factory, *, repository_class=None):
        self.transaction_begin = False
        self.transaction_commit = False
        self.transaction_rollback = False
        super(TestUnitOfWork, self).__init__(factory, repository_class=repository_class)

    def _begin_transaction(self, factory):
        self.transaction_begin = True
        return uuid4()

    def _commit_transaction(self, transaction):
        self.transaction_commit = True

    def _rollback_transaction(self, transaction):
        self.transaction_rollback = True


class TestAbstractSyncUnitOfWork:

    def test_set_specify_repository_by_init_parameter(self):
        class TestRepository2(TestRepository):
            ...

        uof = TestUnitOfWork(123, repository_class=TestRepository2)
        assert uof._repository_class is TestRepository2

    def test_set_repository_from_class_attr(self):
        uow = TestUnitOfWork(123)
        assert uow._repository_class is TestRepository

    def test_fail_get_repository_before_enter_to_context(self):
        uow = TestUnitOfWork('test_fail_get_repository_when_uof_not_enter')
        with pytest.raises(RuntimeError, match='Need enter to UnitOfWork context manager before access to "repository"'):
            _ = uow.repository

    def test_init_repository_when_enter_to_context(self):
        uow = TestUnitOfWork('test_fail_get_repository_when_uof_not_enter')
        with uow:
            assert isinstance(uow.repository, TestRepository)
            assert isinstance(uow.repository._connection, UUID)
            assert uow._current_transaction_events == set()

    def test_fail_get_repository_after_exit_from_context_manager(self):
        uow = TestUnitOfWork('test_fail_get_repository_after_exit_from_context_manager')
        with uow:
            assert uow.repository

        with pytest.raises(RuntimeError, match='Need enter to UnitOfWork context manager before access to "repository"'):
            _ = uow.repository

    def test_fail_double_enter_to_context(self):
        uow = TestUnitOfWork('test_fail_double_enter_to_context')
        with uow:
            with pytest.raises(RuntimeError, match="Double enter to UnitOfWork's context manager"):
                with uow:
                    pass

    def test_call_begin_commit_and_rollback_transaction(self):
        uow = TestUnitOfWork('test_fail_double_enter_to_context')
        assert uow.transaction_begin is False
        assert uow.transaction_commit is False
        assert uow.transaction_rollback is False

        with uow:
            uow.commit()

        assert uow.transaction_begin is True
        assert uow.transaction_commit is True
        assert uow.transaction_rollback is True

    def test_rollback_transaction_when_exit_from_context(self):
        uow = TestUnitOfWork('test_rollback_transaction_when_exit_from_context')
        assert uow.transaction_begin is uow.transaction_commit is uow.transaction_rollback is False
        with uow:
            pass

        assert uow.transaction_begin is uow.transaction_rollback is True
        assert uow.transaction_commit is False

    def test_collect_only_commited_events(self):
        uow = TestUnitOfWork('test_collect_event_when_commit')
        with uow:
            aggr = TestAggregate('')
            uow.repository.add(aggr)
            aggr.add_value('test1')
            aggr.add_value('test2')
            uow.commit()
            aggr.add_value('test3')

        with uow:
            aggr = TestAggregate('')
            uow.repository.add(aggr)
            aggr.add_value('test4')
            uow.commit()
            aggr.add_value('test5')

        events = [event.value for event in uow.collect_events()]
        assert events == ['test1', 'test2', 'test4']
        assert len(uow.collect_events()) == 0

    def test_create_new_repository_when_enter_to_context(self):
        uow = TestUnitOfWork('test_create_new_repository_when_enter_to_context')
        with uow:
            repository1 = uow.repository

        with uow:
            repository2 = uow.repository

        assert type(repository1) == type(repository2)
        assert repository1 is not repository2

