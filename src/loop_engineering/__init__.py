"""Loop Engineering – Self-Adaptive Systems (SAS) MAPE-K framework.

Public API
----------
Taxonomy (5W+1H)::

    from loop_engineering import (
        TriggerSource, AdaptationTiming, AdaptationLevel,
        AdaptationTechnique, DecisionMetric, DecentralizationDegree,
        AdaptationContext,
    )

Knowledge base::

    from loop_engineering import (
        KnowledgeBase, MonitoringRecord, ArchitecturalModel, Policy
    )

MAPE components::

    from loop_engineering import Monitor, Sensor
    from loop_engineering import Analyzer, AnalysisResult
    from loop_engineering import Planner, AdaptationPlan, AdaptationAction
    from loop_engineering import Executor, EffectorResult

Orchestrator::

    from loop_engineering import MAPEKLoop, LoopResult
"""

from importlib.metadata import PackageNotFoundError, version

from loop_engineering.analyze import AnalysisResult, Analyzer
from loop_engineering.execute import EffectorResult, Executor
from loop_engineering.knowledge import (
    ArchitecturalModel,
    KnowledgeBase,
    MonitoringRecord,
    Policy,
)
from loop_engineering.mape_k import LoopResult, MAPEKLoop
from loop_engineering.monitor import Monitor, Sensor
from loop_engineering.plan import AdaptationAction, AdaptationPlan, Planner
from loop_engineering.taxonomy import (
    AdaptationContext,
    AdaptationLevel,
    AdaptationTechnique,
    AdaptationTiming,
    DecentralizationDegree,
    DecisionMetric,
    TriggerSource,
)

try:
    __version__ = version("loop-engineering")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = [
    # taxonomy
    "TriggerSource",
    "AdaptationTiming",
    "AdaptationLevel",
    "AdaptationTechnique",
    "DecisionMetric",
    "DecentralizationDegree",
    "AdaptationContext",
    # knowledge
    "KnowledgeBase",
    "MonitoringRecord",
    "ArchitecturalModel",
    "Policy",
    # monitor
    "Monitor",
    "Sensor",
    # analyze
    "Analyzer",
    "AnalysisResult",
    # plan
    "Planner",
    "AdaptationPlan",
    "AdaptationAction",
    # execute
    "Executor",
    "EffectorResult",
    # mape-k
    "MAPEKLoop",
    "LoopResult",
]
