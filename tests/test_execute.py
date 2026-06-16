"""Tests for the Executor component."""

import pytest

from loop_engineering.execute import Executor
from loop_engineering.knowledge import KnowledgeBase
from loop_engineering.plan import AdaptationAction, AdaptationPlan
from loop_engineering.taxonomy import AdaptationLevel, AdaptationTechnique


@pytest.fixture()
def kb() -> KnowledgeBase:
    return KnowledgeBase()


@pytest.fixture()
def executor(kb) -> Executor:
    return Executor(kb)


def _action(name: str = "scale_out") -> AdaptationAction:
    return AdaptationAction(
        name=name,
        level=AdaptationLevel.APPLICATION,
        technique=AdaptationTechnique.PARAMETER,
    )


class TestEffectorRegistry:
    def test_register_and_list(self, executor):
        executor.register_effector("scale_out", lambda a: True)
        assert "scale_out" in executor.list_effectors()

    def test_unregister(self, executor):
        executor.register_effector("scale_out", lambda a: True)
        removed = executor.unregister_effector("scale_out")
        assert removed is True
        assert "scale_out" not in executor.list_effectors()

    def test_unregister_missing_returns_false(self, executor):
        assert executor.unregister_effector("ghost") is False


class TestExecuteAction:
    def test_successful_effector(self, executor):
        executor.register_effector("scale_out", lambda a: True)
        result = executor.execute_action(_action("scale_out"))
        assert result.success is True
        assert result.action_name == "scale_out"

    def test_failing_effector(self, executor):
        executor.register_effector("scale_out", lambda a: False)
        result = executor.execute_action(_action("scale_out"))
        assert result.success is False

    def test_no_effector_returns_failure(self, executor):
        result = executor.execute_action(_action("unknown"))
        assert result.success is False
        assert "No effector registered" in result.details

    def test_effector_exception_returns_failure(self, executor):
        def boom(action):
            raise RuntimeError("disk full")

        executor.register_effector("risky", boom)
        result = executor.execute_action(_action("risky"))
        assert result.success is False
        assert "disk full" in result.details

    def test_action_parameters_forwarded(self, executor):
        received = {}

        def capture(action):
            received.update(action.parameters)
            return True

        executor.register_effector("capture", capture)
        action = AdaptationAction(
            name="capture",
            level=AdaptationLevel.SYSTEM_SOFTWARE,
            technique=AdaptationTechnique.STRUCTURAL,
            parameters={"key": "value"},
        )
        executor.execute_action(action)
        assert received == {"key": "value"}


class TestExecutePlan:
    def test_empty_plan_returns_empty_list(self, executor):
        plan = AdaptationPlan(goal="no_action")
        assert executor.execute_plan(plan) == []

    def test_all_actions_executed(self, executor):
        executor.register_effector("a1", lambda a: True)
        executor.register_effector("a2", lambda a: True)
        plan = AdaptationPlan(
            goal="test",
            actions=[_action("a1"), _action("a2")],
        )
        results = executor.execute_plan(plan)
        assert len(results) == 2
        assert all(r.success for r in results)

    def test_mixed_results(self, executor):
        executor.register_effector("good", lambda a: True)
        executor.register_effector("bad", lambda a: False)
        plan = AdaptationPlan(
            goal="mixed",
            actions=[_action("good"), _action("bad")],
        )
        results = executor.execute_plan(plan)
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        assert len(successes) == 1
        assert len(failures) == 1

    def test_plan_results_in_order(self, executor):
        order = []
        for name in ("first", "second", "third"):
            n = name  # capture

            def eff(action, _n=n):
                order.append(_n)
                return True

            executor.register_effector(name, eff)

        plan = AdaptationPlan(
            goal="ordered",
            actions=[_action("first"), _action("second"), _action("third")],
        )
        executor.execute_plan(plan)
        assert order == ["first", "second", "third"]
