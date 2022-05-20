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


class TestUnitOfWork(AbstractSyncUnitOfWork[TestRepository, str]):
    repository_class = TestRepository

    def __init__(self, factory):
        self.transaction_begin = False
        self.transaction_commit = False
        self.transaction_rollback = False
        super(TestUnitOfWork, self).__init__(factory)

    def _begin_transaction(self, factory):
        self.transaction_begin = True
        return uuid4()

    def _commit_transaction(self, transaction):
        self.transaction_commit = True

    def _rollback_transaction(self, transaction):
        self.transaction_rollback = True
