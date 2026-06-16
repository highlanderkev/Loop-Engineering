"""Tests for the Planner component."""

import pytest

from loop_engineering.analyze import AnalysisResult
from loop_engineering.knowledge import KnowledgeBase, Policy
from loop_engineering.plan import AdaptationPlan, Planner
from loop_engineering.taxonomy import (
    AdaptationTiming,
    DecisionMetric,
    TriggerSource,
)


@pytest.fixture()
def kb() -> KnowledgeBase:
    return KnowledgeBase()


@pytest.fixture()
def planner(kb) -> Planner:
    return Planner(kb)


def _reactive_anomaly(metric: str = "cpu") -> AnalysisResult:
    return AnalysisResult(
        metric_name=metric,
        timing=AdaptationTiming.REACTIVE,
        trigger=TriggerSource.TECHNICAL_RESOURCES,
        anomaly_detected=True,
        details="threshold exceeded",
    )


def _no_anomaly(metric: str = "cpu") -> AnalysisResult:
    return AnalysisResult(
        metric_name=metric,
        timing=AdaptationTiming.REACTIVE,
        trigger=None,
        anomaly_detected=False,
    )


def _proactive(metric: str = "cpu", predicted: float = 90.0) -> AnalysisResult:
    return AnalysisResult(
        metric_name=metric,
        timing=AdaptationTiming.PROACTIVE,
        trigger=None,
        anomaly_detected=False,
        predicted_value=predicted,
    )


class TestPlan:
    def test_no_anomaly_returns_no_action_plan(self, planner):
        plan = planner.plan(_no_anomaly())
        assert plan.goal == "no_action"
        assert plan.actions == []
        assert plan.utility == 0.0

    def test_anomaly_with_matching_policy_creates_action(self, planner, kb):
        kb.add_policy(Policy("p1", condition="cpu", action="scale_out"))
        plan = planner.plan(_reactive_anomaly("cpu"))
        assert plan.goal == "resolve_cpu"
        assert len(plan.actions) == 1
        assert plan.actions[0].name == "scale_out"

    def test_anomaly_with_no_matching_policy_empty_actions(self, planner, kb):
        kb.add_policy(Policy("p1", condition="memory", action="gc"))
        plan = planner.plan(_reactive_anomaly("cpu"))
        assert plan.goal == "resolve_cpu"
        assert plan.actions == []

    def test_multiple_matching_policies(self, planner, kb):
        kb.add_policy(Policy("p1", condition="cpu", action="scale_out", priority=2))
        kb.add_policy(Policy("p2", condition="cpu", action="alert_ops", priority=1))
        plan = planner.plan(_reactive_anomaly("cpu"))
        action_names = [a.name for a in plan.actions]
        assert "scale_out" in action_names
        assert "alert_ops" in action_names

    def test_proactive_result_triggers_plan(self, planner, kb):
        kb.add_policy(Policy("p1", condition="cpu", action="pre_scale"))
        plan = planner.plan(_proactive("cpu"))
        assert plan.goal == "resolve_cpu"
        assert any(a.name == "pre_scale" for a in plan.actions)

    def test_plan_metric_is_rules(self, planner):
        plan = planner.plan(_reactive_anomaly())
        assert plan.metric == DecisionMetric.RULES

    def test_utility_equals_number_of_actions(self, planner, kb):
        kb.add_policy(Policy("p1", condition="cpu", action="a1"))
        kb.add_policy(Policy("p2", condition="cpu", action="a2"))
        plan = planner.plan(_reactive_anomaly("cpu"))
        assert plan.utility == float(len(plan.actions))


class TestPlanUtilityBased:
    def test_selects_highest_utility(self, planner):
        p1 = AdaptationPlan(goal="low", utility=1.0)
        p2 = AdaptationPlan(goal="high", utility=5.0)
        p3 = AdaptationPlan(goal="mid", utility=3.0)
        selected = planner.plan_utility_based([p1, p2, p3])
        assert selected is p2

    def test_empty_candidates_returns_none(self, planner):
        assert planner.plan_utility_based([]) is None

    def test_single_candidate_returned(self, planner):
        p = AdaptationPlan(goal="only", utility=2.0)
        assert planner.plan_utility_based([p]) is p
