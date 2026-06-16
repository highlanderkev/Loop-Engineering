"""Plan component of the MAPE-K loop.

Based on Section 2 and Section 5 of the technical roadmap:
    "Generate structured adaptation plans—sequences of actions—that resolve
    goal conflicts and prioritise system utility."

Decision metrics supported:
    * Rules/Policies  – apply registered KnowledgeBase policies
    * Utility-based   – select the highest-utility plan from a candidate set
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loop_engineering.analyze import AnalysisResult
from loop_engineering.knowledge import KnowledgeBase
from loop_engineering.taxonomy import (
    AdaptationLevel,
    AdaptationTechnique,
    AdaptationTiming,
    DecisionMetric,
)


@dataclass
class AdaptationAction:
    """A single step within an adaptation plan.

    Attributes:
        name:       Identifier that must match a registered Executor effector.
        level:      Which stack layer is targeted.
        technique:  How the change is applied (parameter / structural / contextual).
        parameters: Arbitrary key-value payload forwarded to the effector.
    """

    name: str
    level: AdaptationLevel
    technique: AdaptationTechnique
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdaptationPlan:
    """An ordered sequence of actions that resolves a detected adaptation need.

    Attributes:
        goal:    Human-readable description of what this plan achieves.
        actions: Ordered list of :class:`AdaptationAction` objects.
        metric:  The :class:`~loop_engineering.taxonomy.DecisionMetric` used to
                 select this plan.
        utility: Estimated utility score (higher is better).  Used by
                 :meth:`Planner.plan_utility_based` for plan selection.
    """

    goal: str
    actions: list[AdaptationAction] = field(default_factory=list)
    metric: DecisionMetric = DecisionMetric.RULES
    utility: float = 0.0


class Planner:
    """Generates :class:`AdaptationPlan` objects from :class:`AnalysisResult` input.

    Two planning modes are provided:

    * **Rules-based** (:meth:`plan`) – applies matching KnowledgeBase policies
      in priority order.
    * **Utility-based** (:meth:`plan_utility_based`) – selects the highest-
      scoring plan from a set of candidates, as required by the utility-based
      decision metric in the roadmap.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self._kb = knowledge_base

    def plan(self, analysis: AnalysisResult) -> AdaptationPlan:
        """Derive a rules-based plan from *analysis*.

        When no anomaly is detected and no proactive forecast is available the
        method returns a no-op plan so that the Execute stage is always given a
        valid object.

        Args:
            analysis: Output from the :class:`~loop_engineering.analyze.Analyzer`.

        Returns:
            An :class:`AdaptationPlan` whose actions are driven by any
            KnowledgeBase policies whose condition string mentions the metric.
        """
        needs_action = analysis.anomaly_detected or (
            analysis.timing == AdaptationTiming.PROACTIVE
            and analysis.predicted_value is not None
        )
        if not needs_action:
            return AdaptationPlan(
                goal="no_action",
                metric=DecisionMetric.RULES,
                utility=0.0,
            )

        actions: list[AdaptationAction] = []
        for policy in self._kb.get_policies():
            if analysis.metric_name in policy.condition:
                actions.append(
                    AdaptationAction(
                        name=policy.action,
                        level=AdaptationLevel.APPLICATION,
                        technique=AdaptationTechnique.PARAMETER,
                        parameters={"policy": policy.name},
                    )
                )

        return AdaptationPlan(
            goal=f"resolve_{analysis.metric_name}",
            actions=actions,
            metric=DecisionMetric.RULES,
            utility=float(len(actions)),
        )

    def plan_utility_based(
        self, candidates: list[AdaptationPlan]
    ) -> AdaptationPlan | None:
        """Select the plan with the highest :attr:`AdaptationPlan.utility`.

        Args:
            candidates: A collection of pre-built plans to compare.

        Returns:
            The highest-utility plan, or *None* when *candidates* is empty.
        """
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.utility)
