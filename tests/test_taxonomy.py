"""Tests for the SAS taxonomy module."""

from loop_engineering.taxonomy import (
    AdaptationContext,
    AdaptationLevel,
    AdaptationTechnique,
    AdaptationTiming,
    DecentralizationDegree,
    DecisionMetric,
    TriggerSource,
)


class TestTriggerSource:
    def test_all_members_exist(self):
        assert TriggerSource.TECHNICAL_RESOURCES
        assert TriggerSource.CONTEXT
        assert TriggerSource.USER_PREFERENCES

    def test_distinct_values(self):
        sources = list(TriggerSource)
        assert len(sources) == len(set(s.value for s in sources))


class TestAdaptationTiming:
    def test_reactive_and_proactive(self):
        assert AdaptationTiming.REACTIVE != AdaptationTiming.PROACTIVE

    def test_only_two_members(self):
        assert len(list(AdaptationTiming)) == 2


class TestAdaptationLevel:
    def test_all_levels(self):
        assert AdaptationLevel.APPLICATION
        assert AdaptationLevel.SYSTEM_SOFTWARE
        assert AdaptationLevel.COMMUNICATION


class TestAdaptationTechnique:
    def test_parameter_least_overhead(self):
        # Ensure all three techniques are distinct
        techniques = [
            AdaptationTechnique.PARAMETER,
            AdaptationTechnique.STRUCTURAL,
            AdaptationTechnique.CONTEXTUAL,
        ]
        assert len(set(t.value for t in techniques)) == 3


class TestDecisionMetric:
    def test_four_metrics(self):
        assert len(list(DecisionMetric)) == 4

    def test_utility_based_present(self):
        assert DecisionMetric.UTILITY_BASED in list(DecisionMetric)


class TestDecentralizationDegree:
    def test_three_degrees(self):
        assert len(list(DecentralizationDegree)) == 3


class TestAdaptationContext:
    def test_construction(self):
        ctx = AdaptationContext(
            when=AdaptationTiming.REACTIVE,
            why=TriggerSource.CONTEXT,
            where=AdaptationLevel.APPLICATION,
            what=AdaptationTechnique.PARAMETER,
            how=DecisionMetric.RULES,
        )
        assert ctx.when == AdaptationTiming.REACTIVE
        assert ctx.why == TriggerSource.CONTEXT
        assert ctx.where == AdaptationLevel.APPLICATION
        assert ctx.what == AdaptationTechnique.PARAMETER
        assert ctx.how == DecisionMetric.RULES

    def test_frozen(self):
        import pytest

        ctx = AdaptationContext(
            when=AdaptationTiming.PROACTIVE,
            why=TriggerSource.TECHNICAL_RESOURCES,
            where=AdaptationLevel.SYSTEM_SOFTWARE,
            what=AdaptationTechnique.STRUCTURAL,
            how=DecisionMetric.UTILITY_BASED,
        )
        with pytest.raises((AttributeError, TypeError)):
            ctx.when = AdaptationTiming.REACTIVE  # type: ignore[misc]
