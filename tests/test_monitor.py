"""Tests for the Monitor component."""

import pytest

from loop_engineering.knowledge import KnowledgeBase
from loop_engineering.monitor import Monitor, Sensor
from loop_engineering.taxonomy import TriggerSource


@pytest.fixture()
def kb() -> KnowledgeBase:
    return KnowledgeBase()


@pytest.fixture()
def monitor(kb) -> Monitor:
    return Monitor(kb)


class TestSensorRegistration:
    def test_register_and_retrieve(self, monitor):
        sensor = Sensor(name="cpu", source=TriggerSource.TECHNICAL_RESOURCES)
        monitor.register_sensor(sensor)
        assert monitor.get_sensor("cpu") is sensor

    def test_missing_returns_none(self, monitor):
        assert monitor.get_sensor("missing") is None

    def test_list_sensors(self, monitor):
        monitor.register_sensor(Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES))
        monitor.register_sensor(Sensor("mem", TriggerSource.TECHNICAL_RESOURCES))
        assert set(monitor.list_sensors()) == {"cpu", "mem"}

    def test_unregister(self, monitor):
        monitor.register_sensor(Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES))
        removed = monitor.unregister_sensor("cpu")
        assert removed is True
        assert monitor.get_sensor("cpu") is None

    def test_unregister_missing_returns_false(self, monitor):
        assert monitor.unregister_sensor("ghost") is False


class TestSampling:
    def test_sample_stores_record(self, monitor, kb):
        monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 55.0)
        )
        rec = monitor.sample("cpu")
        assert rec is not None
        assert rec.metric_name == "cpu"
        assert rec.value == 55.0
        stored = kb.get_monitoring_records("cpu")
        assert len(stored) == 1

    def test_sample_missing_sensor_returns_none(self, monitor):
        assert monitor.sample("nonexistent") is None

    def test_sample_no_sampler_returns_none(self, monitor):
        monitor.register_sensor(Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES))
        assert monitor.sample("cpu") is None

    def test_sample_all_only_includes_sensors_with_samplers(self, monitor):
        monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 10.0)
        )
        monitor.register_sensor(
            Sensor("mem", TriggerSource.TECHNICAL_RESOURCES)  # no sampler
        )
        records = monitor.sample_all()
        assert len(records) == 1
        assert records[0].metric_name == "cpu"

    def test_record_source_matches_trigger_source(self, monitor):
        monitor.register_sensor(
            Sensor("net", TriggerSource.CONTEXT, sampler=lambda: 99)
        )
        rec = monitor.sample("net")
        assert rec.source == TriggerSource.CONTEXT.name


class TestAnomalyDetection:
    def test_value_above_threshold_is_anomaly(self, monitor):
        monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, threshold=80.0)
        )
        assert monitor.is_anomaly("cpu", 95.0) is True

    def test_value_at_threshold_is_not_anomaly(self, monitor):
        monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, threshold=80.0)
        )
        assert monitor.is_anomaly("cpu", 80.0) is False

    def test_value_below_threshold_is_not_anomaly(self, monitor):
        monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, threshold=80.0)
        )
        assert monitor.is_anomaly("cpu", 50.0) is False

    def test_no_threshold_never_anomaly(self, monitor):
        monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES)  # no threshold
        )
        assert monitor.is_anomaly("cpu", 999.0) is False

    def test_unknown_sensor_never_anomaly(self, monitor):
        assert monitor.is_anomaly("ghost", 999.0) is False

    def test_non_numeric_value_not_anomaly(self, monitor):
        monitor.register_sensor(
            Sensor("status", TriggerSource.CONTEXT, threshold=1.0)
        )
        assert monitor.is_anomaly("status", "ok") is False
