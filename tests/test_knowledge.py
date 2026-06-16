"""Tests for the KnowledgeBase module."""

import pytest

from loop_engineering.knowledge import (
    ArchitecturalModel,
    KnowledgeBase,
    MonitoringRecord,
    Policy,
)


@pytest.fixture()
def kb() -> KnowledgeBase:
    return KnowledgeBase()


class TestMonitoringRecords:
    def test_store_and_retrieve_all(self, kb):
        rec = MonitoringRecord(timestamp=1.0, metric_name="cpu", value=42.0)
        kb.store_monitoring_record(rec)
        records = kb.get_monitoring_records()
        assert len(records) == 1
        assert records[0] is rec

    def test_filter_by_metric_name(self, kb):
        kb.store_monitoring_record(MonitoringRecord(1.0, "cpu", 50.0))
        kb.store_monitoring_record(MonitoringRecord(2.0, "mem", 70.0))
        kb.store_monitoring_record(MonitoringRecord(3.0, "cpu", 60.0))
        cpu_records = kb.get_monitoring_records("cpu")
        assert len(cpu_records) == 2
        assert all(r.metric_name == "cpu" for r in cpu_records)

    def test_empty_returns_empty_list(self, kb):
        assert kb.get_monitoring_records() == []
        assert kb.get_monitoring_records("cpu") == []

    def test_get_all_returns_copy(self, kb):
        kb.store_monitoring_record(MonitoringRecord(1.0, "cpu", 10.0))
        records = kb.get_monitoring_records()
        records.clear()
        assert len(kb.get_monitoring_records()) == 1


class TestArchitecturalModels:
    def test_store_and_retrieve(self, kb):
        model = ArchitecturalModel(
            name="service_mesh",
            components=["A", "B"],
            connections={"A": ["B"]},
        )
        kb.store_architectural_model(model)
        retrieved = kb.get_architectural_model("service_mesh")
        assert retrieved is model

    def test_missing_returns_none(self, kb):
        assert kb.get_architectural_model("nonexistent") is None

    def test_replace_model(self, kb):
        m1 = ArchitecturalModel(name="app", components=["X"])
        m2 = ArchitecturalModel(name="app", components=["Y"])
        kb.store_architectural_model(m1)
        kb.store_architectural_model(m2)
        assert kb.get_architectural_model("app").components == ["Y"]

    def test_list_models(self, kb):
        kb.store_architectural_model(ArchitecturalModel("alpha"))
        kb.store_architectural_model(ArchitecturalModel("beta"))
        names = kb.list_architectural_models()
        assert set(names) == {"alpha", "beta"}


class TestPolicies:
    def test_add_and_retrieve(self, kb):
        policy = Policy(name="scale_out", condition="cpu_usage > 80", action="add_node")
        kb.add_policy(policy)
        policies = kb.get_policies()
        assert len(policies) == 1
        assert policies[0].name == "scale_out"

    def test_priority_ordering(self, kb):
        low = Policy("low", "metric > 1", "act_low", priority=1)
        high = Policy("high", "metric > 1", "act_high", priority=10)
        medium = Policy("medium", "metric > 1", "act_medium", priority=5)
        kb.add_policy(low)
        kb.add_policy(high)
        kb.add_policy(medium)
        names = [p.name for p in kb.get_policies()]
        assert names == ["high", "medium", "low"]

    def test_remove_policy(self, kb):
        kb.add_policy(Policy("p1", "x > 0", "act1"))
        kb.add_policy(Policy("p2", "y > 0", "act2"))
        removed = kb.remove_policy("p1")
        assert removed is True
        names = [p.name for p in kb.get_policies()]
        assert "p1" not in names

    def test_remove_missing_returns_false(self, kb):
        assert kb.remove_policy("ghost") is False

    def test_get_policies_returns_copy(self, kb):
        kb.add_policy(Policy("p1", "x > 0", "act"))
        policies = kb.get_policies()
        policies.clear()
        assert len(kb.get_policies()) == 1
