"""Tests for LangGraph-backed long-running agent orchestration."""

import pytest

from loop_engineering.knowledge import Policy
from loop_engineering.langgraph_agent import LangGraphMAPEKAgent
from loop_engineering.mape_k import MAPEKLoop
from loop_engineering.monitor import Sensor
from loop_engineering.taxonomy import TriggerSource


@pytest.fixture()
def configured_loop() -> MAPEKLoop:
    loop = MAPEKLoop()
    loop.monitor.register_sensor(
        Sensor("cpu", TriggerSource.TECHNICAL_RESOURCES, sampler=lambda: 95.0)
    )
    loop.knowledge_base.add_policy(
        Policy(name="throttle", condition="cpu", action="scale_out")
    )
    loop.executor.register_effector("scale_out", lambda action: True)
    return loop


def test_run_persists_cycles_by_thread(configured_loop):
    agent = LangGraphMAPEKAgent(loop=configured_loop)

    first = agent.run(
        thread_id="thread-a",
        cycles=1,
        anomaly_thresholds={"cpu": 80.0},
    )
    second = agent.run(
        thread_id="thread-a",
        cycles=2,
        anomaly_thresholds={"cpu": 80.0},
    )

    assert first.cycles_completed == 1
    assert second.cycles_completed == 3
    assert len(second.history) == 3
    assert second.latest_result is not None
    assert second.latest_result.actions_succeeded == 1


def test_run_isolated_between_threads(configured_loop):
    agent = LangGraphMAPEKAgent(loop=configured_loop)

    one = agent.run(thread_id="thread-1", cycles=1, anomaly_thresholds={"cpu": 80.0})
    two = agent.run(thread_id="thread-2", cycles=1, anomaly_thresholds={"cpu": 80.0})

    assert one.cycles_completed == 1
    assert two.cycles_completed == 1


def test_run_rejects_invalid_cycle_count():
    agent = LangGraphMAPEKAgent()
    with pytest.raises(ValueError, match="cycles must be >= 1"):
        agent.run(thread_id="thread-a", cycles=0)
