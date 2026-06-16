"""Knowledge base: the shared repository at the heart of MAPE-K.

Based on Section 2 of the technical roadmap:
    "The Knowledge (K) component is the mandatory shared repository for
    monitoring data, architectural models, and organisational policies."

The KnowledgeBase provides the persistence that allows the Analyze and Plan
stages to make informed decisions based on the system's self-awareness.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MonitoringRecord:
    """A single telemetry observation captured by the Monitor."""

    timestamp: float
    metric_name: str
    value: float | int | str
    source: str = ""


@dataclass
class ArchitecturalModel:
    """A lightweight run-time architectural model of managed resources."""

    name: str
    components: list[str] = field(default_factory=list)
    connections: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Policy:
    """A predefined rule governing adaptation state transitions.

    Attributes:
        name:      Unique policy identifier.
        condition: A string expression evaluated against the metric name and value
                   (e.g. ``"cpu_usage > 80"``).
        action:    Name of the effector action to invoke when the condition holds.
        priority:  Higher-priority policies are evaluated first.
    """

    name: str
    condition: str
    action: str
    priority: int = 0


class KnowledgeBase:
    """Centralised store for monitoring data, architectural models, and policies.

    All MAPE components share a single KnowledgeBase instance so that every
    stage can reason from the same self-aware view of the managed system.
    """

    def __init__(self) -> None:
        self._monitoring_data: list[MonitoringRecord] = []
        self._architectural_models: dict[str, ArchitecturalModel] = {}
        self._policies: list[Policy] = []

    # ------------------------------------------------------------------
    # Monitoring data
    # ------------------------------------------------------------------

    def store_monitoring_record(self, record: MonitoringRecord) -> None:
        """Append a new telemetry record to the store."""
        self._monitoring_data.append(record)

    def get_monitoring_records(
        self, metric_name: str | None = None
    ) -> list[MonitoringRecord]:
        """Return all records, optionally filtered by *metric_name*."""
        if metric_name is None:
            return list(self._monitoring_data)
        return [r for r in self._monitoring_data if r.metric_name == metric_name]

    # ------------------------------------------------------------------
    # Architectural models
    # ------------------------------------------------------------------

    def store_architectural_model(self, model: ArchitecturalModel) -> None:
        """Persist or replace an architectural model by name."""
        self._architectural_models[model.name] = model

    def get_architectural_model(self, name: str) -> ArchitecturalModel | None:
        """Retrieve an architectural model by name, or *None* if absent."""
        return self._architectural_models.get(name)

    def list_architectural_models(self) -> list[str]:
        """Return the names of all stored architectural models."""
        return list(self._architectural_models.keys())

    # ------------------------------------------------------------------
    # Policies
    # ------------------------------------------------------------------

    def add_policy(self, policy: Policy) -> None:
        """Register a policy, maintaining descending priority order."""
        self._policies.append(policy)
        self._policies.sort(key=lambda p: p.priority, reverse=True)

    def get_policies(self) -> list[Policy]:
        """Return all policies ordered by descending priority."""
        return list(self._policies)

    def remove_policy(self, name: str) -> bool:
        """Remove the policy with the given name.  Returns *True* if found."""
        original = len(self._policies)
        self._policies = [p for p in self._policies if p.name != name]
        return len(self._policies) < original
