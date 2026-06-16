"""SAS Taxonomy: the 5W+1H framework for Self-Adaptive Systems.

Based on Section 1 of the technical roadmap:
    When   → AdaptationTiming   (reactive or proactive)
    Why    → TriggerSource      (technical resources, context, user preferences)
    Where  → AdaptationLevel    (application, system software, communication)
    What   → AdaptationTechnique(parameter, structural, contextual)
    How    → DecisionMetric     (model-based, rules, goal-based, utility-based)
    Who    → N/A                (SAS is inherently automatic; no human actor)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TriggerSource(Enum):
    """Why the system must change (causal dimension)."""

    TECHNICAL_RESOURCES = auto()  # hardware defects, software faults, network drops
    CONTEXT = auto()              # environmental changes (noise, light, signal)
    USER_PREFERENCES = auto()     # manual updates or shifting user-group composition


class AdaptationTiming(Enum):
    """When the system changes (temporal dimension)."""

    REACTIVE = auto()   # event-driven; responds after a threshold is breached
    PROACTIVE = auto()  # predictive; acts before the application can no longer execute


class AdaptationLevel(Enum):
    """Where in the stack the adaptation is applied."""

    APPLICATION = auto()      # application-level logic
    SYSTEM_SOFTWARE = auto()  # OS or middleware
    COMMUNICATION = auto()    # network infrastructure or communication patterns


class AdaptationTechnique(Enum):
    """What kind of structural change is performed."""

    PARAMETER = auto()   # adjusts variables within existing logic; low overhead
    STRUCTURAL = auto()  # compositional changes (add/remove components)
    CONTEXTUAL = auto()  # targets the environment itself; highest impact


class DecisionMetric(Enum):
    """How the Plan stage selects an adaptation strategy."""

    MODEL_BASED = auto()    # architectural/feature/behavioral models at runtime
    RULES = auto()          # predefined logic or policies (often design-time)
    GOAL_BASED = auto()     # KAOS or FLAGS models; allows goal relaxation
    UTILITY_BASED = auto()  # maximises value vs. cost under uncertainty


class DecentralizationDegree(Enum):
    """Degree of decentralisation for the MAPE-K deployment."""

    CENTRALIZED = auto()          # single AL manages all; global optimum but SPOF
    FULLY_DECENTRALIZED = auto()  # every sub-system owns a MAPE loop
    HYBRID = auto()               # monitoring/execution distributed; planning central


@dataclass(frozen=True)
class AdaptationContext:
    """Captures the full 5W+1H context for a single adaptation decision.

    The *who* dimension is always the autonomous adaptation logic itself and
    is therefore omitted from this structure per the roadmap's N/A classification.
    """

    when: AdaptationTiming
    why: TriggerSource
    where: AdaptationLevel
    what: AdaptationTechnique
    how: DecisionMetric
