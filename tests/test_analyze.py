"""Tests for the Analyzer component."""

import pytest

from loop_engineering.analyze import Analyzer
from loop_engineering.knowledge import KnowledgeBase, MonitoringRecord
from loop_engineering.taxonomy import AdaptationTiming, TriggerSource


@pytest.fixture()
def kb() -> KnowledgeBase:
    return KnowledgeBase()


@pytest.fixture()
def analyzer(kb) -> Analyzer:
    return Analyzer(kb)


def _populate(kb: KnowledgeBase, metric: str, values: list[float]) -> None:
    for i, v in enumerate(values):
        kb.store_monitoring_record(
            MonitoringRecord(timestamp=float(i), metric_name=metric, value=v)
        )


class TestDetectAnomaly:
    def test_anomaly_when_latest_exceeds_threshold(self, analyzer, kb):
        _populate(kb, "cpu", [10.0, 20.0, 95.0])
        result = analyzer.detect_anomaly("cpu", threshold=80.0)
        assert result.anomaly_detected is True
        assert result.timing == AdaptationTiming.REACTIVE
        assert result.trigger == TriggerSource.TECHNICAL_RESOURCES

    def test_no_anomaly_when_latest_below_threshold(self, analyzer, kb):
        _populate(kb, "cpu", [50.0, 60.0, 70.0])
        result = analyzer.detect_anomaly("cpu", threshold=80.0)
        assert result.anomaly_detected is False
        assert result.trigger is None

    def test_no_data_returns_no_anomaly(self, analyzer):
        result = analyzer.detect_anomaly("cpu", threshold=80.0)
        assert result.anomaly_detected is False
        assert "No monitoring data" in result.details

    def test_custom_trigger_source(self, analyzer, kb):
        _populate(kb, "light", [900.0])
        result = analyzer.detect_anomaly(
            "light", threshold=500.0, trigger=TriggerSource.CONTEXT
        )
        assert result.trigger == TriggerSource.CONTEXT

    def test_result_contains_raw_values(self, analyzer, kb):
        _populate(kb, "cpu", [1.0, 2.0, 3.0])
        result = analyzer.detect_anomaly("cpu", threshold=10.0)
        assert result.raw_values == [1.0, 2.0, 3.0]

    def test_timing_is_reactive(self, analyzer, kb):
        _populate(kb, "cpu", [99.0])
        result = analyzer.detect_anomaly("cpu", threshold=80.0)
        assert result.timing == AdaptationTiming.REACTIVE


class TestForecast:
    def test_upward_trend_prediction(self, analyzer, kb):
        _populate(kb, "mem", [10.0, 20.0, 30.0])
        result = analyzer.forecast("mem", window=3)
        assert result.timing == AdaptationTiming.PROACTIVE
        assert result.predicted_value == pytest.approx(50.0)  # trend=20, next=30+20

    def test_downward_trend_prediction(self, analyzer, kb):
        _populate(kb, "cpu", [90.0, 60.0, 30.0])
        result = analyzer.forecast("cpu", window=3)
        assert result.predicted_value == pytest.approx(-30.0)  # trend=-60, next=30-60

    def test_flat_trend_prediction(self, analyzer, kb):
        _populate(kb, "cpu", [50.0, 50.0, 50.0])
        result = analyzer.forecast("cpu", window=3)
        assert result.predicted_value == pytest.approx(50.0)

    def test_insufficient_data(self, analyzer, kb):
        _populate(kb, "cpu", [42.0])
        result = analyzer.forecast("cpu")
        assert result.predicted_value is None
        assert "Insufficient" in result.details

    def test_no_data(self, analyzer):
        result = analyzer.forecast("nonexistent")
        assert result.predicted_value is None

    def test_anomaly_not_set_in_forecast(self, analyzer, kb):
        _populate(kb, "cpu", [10.0, 20.0])
        result = analyzer.forecast("cpu")
        assert result.anomaly_detected is False

    def test_window_limits_data_used(self, analyzer, kb):
        # Window of 2 should only consider the last 2 records
        _populate(kb, "cpu", [100.0, 1.0, 2.0])
        result = analyzer.forecast("cpu", window=2)
        # trend = 2.0 - 1.0 = 1.0; predicted = 2.0 + 1.0 = 3.0
        assert result.predicted_value == pytest.approx(3.0)

    def test_result_timing_is_proactive(self, analyzer, kb):
        _populate(kb, "cpu", [1.0, 2.0])
        result = analyzer.forecast("cpu")
        assert result.timing == AdaptationTiming.PROACTIVE
