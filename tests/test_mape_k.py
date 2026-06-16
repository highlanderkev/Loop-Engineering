"""Tests for the MAPEKLoop orchestrator."""

import pytest

from loop_engineering.knowledge import KnowledgeBase, Policy
from loop_engineering.mape_k import LoopResult, MAPEKLoop
from loop_engineering.monitor import Sensor
from loop_engineering.taxonomy import DecentralizationDegree, TriggerSource


@pytest.fixture()
def loop() -> MAPEKLoop:
    return MAPEKLoop()


class TestMAPEKLoopConstruction:
    def test_default_decentralization(self, loop):
        assert loop.decentralization == DecentralizationDegree.CENTRALIZED

    def test_custom_knowledge_base(self):
        kb = KnowledgeBase()
        loop = MAPEKLoop(knowledge_base=kb)
        assert loop.knowledge_base is kb

    def test_components_share_knowledge_base(self, loop):
        assert loop.monitor._kb is loop.knowledge_base
        assert loop.analyzer._kb is loop.knowledge_base
        assert loop.planner._kb is loop.knowledge_base
        assert loop.executor._kb is loop.knowledge_base

    def test_custom_decentralization(self):
        loop = MAPEKLoop(decentralization=DecentralizationDegree.HYBRID)
        assert loop.decentralization == DecentralizationDegree.HYBRID


class TestRunCycle:
    def test_empty_cycle_returns_loop_result(self, loop):
        result = loop.run_cycle()
        assert isinstance(result, LoopResult)
        assert result.monitoring_count == 0
        assert result.analysis_results == []
        assert result.plans == []
        assert result.execution_results == []

    def test_monitoring_count(self, loop):
        loop.monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 50.0)
        )
        loop.monitor.register_sensor(
            Sensor("mem", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 30.0)
        )
        result = loop.run_cycle()
        assert result.monitoring_count == 2

    def test_anomaly_detected_in_cycle(self, loop):
        loop.monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 95.0)
        )
        result = loop.run_cycle(anomaly_thresholds={"cpu": 80.0})
        assert result.anomalies_detected == 1

    def test_no_anomaly_when_below_threshold(self, loop):
        loop.monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 50.0)
        )
        result = loop.run_cycle(anomaly_thresholds={"cpu": 80.0})
        assert result.anomalies_detected == 0

    def test_full_mape_k_cycle(self, loop):
        """Integration: sensor → anomaly → policy → effector → success."""
        loop.monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 95.0)
        )
        loop.knowledge_base.add_policy(
            Policy(name="throttle", condition="cpu", action="scale_out")
        )
        loop.executor.register_effector("scale_out", lambda action: True)

        result = loop.run_cycle(anomaly_thresholds={"cpu": 80.0})

        assert result.monitoring_count == 1
        assert result.anomalies_detected == 1
        assert result.actions_succeeded == 1
        assert result.actions_failed == 0

    def test_actions_failed_counter(self, loop):
        loop.monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 95.0)
        )
        loop.knowledge_base.add_policy(
            Policy(name="p", condition="cpu", action="unknown_action")
        )
        result = loop.run_cycle(anomaly_thresholds={"cpu": 80.0})
        assert result.actions_failed == 1
        assert result.actions_succeeded == 0

    def test_multiple_metrics(self, loop):
        loop.monitor.register_sensor(
            Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 90.0)
        )
        loop.monitor.register_sensor(
            Sensor("mem", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 90.0)
        )
        result = loop.run_cycle(
            anomaly_thresholds={"cpu": 80.0, "mem": 80.0}
        )
        assert result.anomalies_detected == 2

    def test_custom_trigger_source(self, loop):
        loop.monitor.register_sensor(
            Sensor("light", TriggerSource.CONTEXT, sampler=lambda: 900.0)
        )
        result = loop.run_cycle(
            anomaly_thresholds={"light": 500.0},
            trigger=TriggerSource.CONTEXT,
        )
        assert result.analysis_results[0].trigger == TriggerSource.CONTEXT


class TestLoopResultProperties:
    def _make_result(self, anomalies: int, successes: int, failures: int) -> LoopResult:
        from loop_engineering.analyze import AnalysisResult
        from loop_engineering.execute import EffectorResult
        from loop_engineering.taxonomy import AdaptationTiming

        analysis = [
            AnalysisResult(
                metric_name="cpu",
                timing=AdaptationTiming.REACTIVE,
                trigger=TriggerSource.TECHNICAL_RESOURCES,
                anomaly_detected=True,
            )
            for _ in range(anomalies)
        ]
        exec_results = [
            EffectorResult("act", success=True) for _ in range(successes)
        ] + [
            EffectorResult("act", success=False) for _ in range(failures)
        ]
        return LoopResult(
            monitoring_count=0,
            analysis_results=analysis,
            execution_results=exec_results,
        )

    def test_anomalies_detected(self):
        r = self._make_result(3, 0, 0)
        assert r.anomalies_detected == 3

    def test_actions_succeeded(self):
        r = self._make_result(0, 2, 1)
        assert r.actions_succeeded == 2

    def test_actions_failed(self):
        r = self._make_result(0, 2, 1)
        assert r.actions_failed == 1
