"""LangGraph-powered long-running MAPE-K agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from loop_engineering.mape_k import LoopResult, MAPEKLoop
from loop_engineering.taxonomy import TriggerSource


class AgentState(TypedDict, total=False):
    """State persisted by LangGraph for each agent thread."""

anomaly_thresholds: dict[str, float] | None
    trigger: TriggerSource
    target_cycles: int
    cycles_completed: int
    latest_result: LoopResult
    history: list[LoopResult]


@dataclass
class LongRunningAgentResult:
    """Return value for one long-running LangGraph execution."""

    cycles_completed: int
    latest_result: LoopResult | None
    history: list[LoopResult]


class LangGraphMAPEKAgent:
    """Run MAPE-K cycles as a resumable long-running LangGraph workflow."""

    def __init__(
        self,
        loop: MAPEKLoop | None = None,
        checkpointer: InMemorySaver | None = None,
    ) -> None:
        self.loop = loop or MAPEKLoop()
        self.checkpointer = checkpointer or InMemorySaver()

        graph = StateGraph(AgentState)
        graph.add_node("run_cycle", self._run_cycle)
        graph.add_edge(START, "run_cycle")
        graph.add_conditional_edges(
            "run_cycle",
            self._next_step,
            {"run_cycle": "run_cycle", "end": END},
        )
        self._graph = graph.compile(checkpointer=self.checkpointer)

    def _run_cycle(self, state: AgentState) -> AgentState:
        result = self.loop.run_cycle(
            anomaly_thresholds=state.get("anomaly_thresholds"),
            trigger=state.get("trigger", TriggerSource.TECHNICAL_RESOURCES),
        )
        previous_cycles = state.get("cycles_completed", 0)
        history = list(state.get("history", []))
        history.append(result)
        return {
            "cycles_completed": previous_cycles + 1,
            "latest_result": result,
            "history": history,
        }

    @staticmethod
    def _next_step(state: AgentState) -> str:
        if state.get("cycles_completed", 0) < state.get("target_cycles", 1):
            return "run_cycle"
        return "end"

    @staticmethod
    def _thread_config(thread_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": thread_id}}

    def run(
        self,
        thread_id: str,
        cycles: int = 1,
        anomaly_thresholds: dict[str, float] | None = None,
        trigger: TriggerSource = TriggerSource.TECHNICAL_RESOURCES,
    ) -> LongRunningAgentResult:
        """Run *cycles* MAPE-K iterations for *thread_id* and persist progress."""
        if cycles < 1:
            raise ValueError("cycles must be >= 1")

        config = self._thread_config(thread_id)
snapshot = self._graph.get_state(config)
snapshot_values = snapshot.values or {}
current_cycles = int(snapshot_values.get("cycles_completed", 0))
        target_cycles = current_cycles + cycles

        state = self._graph.invoke(
            {
                "anomaly_thresholds": anomaly_thresholds,
                "trigger": trigger,
                "target_cycles": target_cycles,
            },
            config=config,
        )
        return LongRunningAgentResult(
            cycles_completed=state.get("cycles_completed", 0),
            latest_result=state.get("latest_result"),
            history=state.get("history", []),
        )
