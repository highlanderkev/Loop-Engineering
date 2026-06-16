"""MAPE-K loop orchestrator.

Based on Section 2 of the technical roadmap:
    "A fundamental requirement for scalability is the separation of the
    Adaptation Logic (AL) from the Managed Resources (MR)."

:class:`MAPEKLoop` wires the four MAPE components together around a shared
:class:`~loop_engineering.knowledge.KnowledgeBase` and exposes a single
:meth:`MAPEKLoop.run_cycle` method that executes one complete feedback loop.

The degree of decentralisation can be set at construction time; the class
itself is the reference implementation for a **Centralized** or
**Hybrid** deployment.  Fully-decentralised deployments compose multiple
:class:`MAPEKLoop` instances—one per managed sub-system.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from loop_engineering.analyze import AnalysisResult, Analyzer
from loop_engineering.execute import EffectorResult, Executor
from loop_engineering.knowledge import KnowledgeBase
from loop_engineering.monitor import Monitor
from loop_engineering.plan import AdaptationPlan, Planner
from loop_engineering.taxonomy import DecentralizationDegree, TriggerSource


@dataclass
class LoopResult:
    """Summary of one complete MAPE-K cycle.

    Attributes:
        monitoring_count:  Number of sensor samples collected.
        analysis_results:  One :class:`AnalysisResult` per analysed metric.
        plans:             One :class:`AdaptationPlan` per analysis result.
        execution_results: All :class:`EffectorResult` objects from the Execute stage.
    """

    monitoring_count: int
    analysis_results: list[AnalysisResult] = field(default_factory=list)
    plans: list[AdaptationPlan] = field(default_factory=list)
    execution_results: list[EffectorResult] = field(default_factory=list)

    @property
    def anomalies_detected(self) -> int:
        """Number of analysis results that flagged an anomaly."""
        return sum(1 for ar in self.analysis_results if ar.anomaly_detected)

    @property
    def actions_succeeded(self) -> int:
        """Number of effector invocations that reported success."""
        return sum(1 for er in self.execution_results if er.success)

    @property
    def actions_failed(self) -> int:
        """Number of effector invocations that reported failure."""
        return sum(1 for er in self.execution_results if not er.success)


class MAPEKLoop:
    """Monitor → Analyse → Plan → Execute feedback loop with shared Knowledge.

    Example::

        from loop_engineering.mape_k import MAPEKLoop
        from loop_engineering.monitor import Sensor
        from loop_engineering.knowledge import Policy
        from loop_engineering.taxonomy import TriggerSource

        loop = MAPEKLoop()

        # Register a CPU sensor
        loop.monitor.register_sensor(
            Sensor(name="cpu_usage", source=TriggerSource.TECHNICAL_RESOURCES,
                   threshold=80.0, sampler=lambda: 92.0)
        )

        # Register a remediation policy
        loop.knowledge_base.add_policy(
            Policy(name="throttle_cpu", condition="cpu_usage", action="scale_out")
        )

        # Register an effector
        loop.executor.register_effector("scale_out", lambda action: True)

        result = loop.run_cycle(anomaly_thresholds={"cpu_usage": 80.0})
        assert result.anomalies_detected == 1
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        decentralization: DecentralizationDegree = DecentralizationDegree.CENTRALIZED,
    ) -> None:
        self.knowledge_base: KnowledgeBase = knowledge_base or KnowledgeBase()
        self.decentralization: DecentralizationDegree = decentralization
        self.monitor: Monitor = Monitor(self.knowledge_base)
        self.analyzer: Analyzer = Analyzer(self.knowledge_base)
        self.planner: Planner = Planner(self.knowledge_base)
        self.executor: Executor = Executor(self.knowledge_base)

    def run_cycle(
        self,
        anomaly_thresholds: dict[str, float] | None = None,
        trigger: TriggerSource = TriggerSource.TECHNICAL_RESOURCES,
    ) -> LoopResult:
        """Execute one complete MAPE-K cycle.

        Args:
            anomaly_thresholds: Mapping of ``metric_name → threshold`` for the
                                 Analyse stage's reactive anomaly detection.
                                 When *None*, no reactive analysis is performed.
            trigger:            The :class:`~loop_engineering.taxonomy.TriggerSource`
                                 attributed to any detected anomalies.

        Returns:
            A :class:`LoopResult` summarising all stage outputs.
        """
        thresholds = anomaly_thresholds or {}

        # ── Monitor ───────────────────────────────────────────────────
        records = self.monitor.sample_all()

        # ── Analyse ───────────────────────────────────────────────────
        analysis_results: list[AnalysisResult] = []
        for metric_name, threshold in thresholds.items():
            result = self.analyzer.detect_anomaly(metric_name, threshold, trigger)
            analysis_results.append(result)

        # ── Plan ──────────────────────────────────────────────────────
        plans: list[AdaptationPlan] = [
            self.planner.plan(ar) for ar in analysis_results
        ]

        # ── Execute ───────────────────────────────────────────────────
        execution_results: list[EffectorResult] = []
        for plan in plans:
            execution_results.extend(self.executor.execute_plan(plan))

        return LoopResult(
            monitoring_count=len(records),
            analysis_results=analysis_results,
            plans=plans,
            execution_results=execution_results,
        )
