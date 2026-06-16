"""Analyze component of the MAPE-K loop.

Based on Section 2 of the technical roadmap:
    "Implement algorithms capable of reactive anomaly detection (identifying
    historical drops in performance) and proactive forecasting (predicting
    future states based on current trajectories)."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from loop_engineering.knowledge import KnowledgeBase
from loop_engineering.taxonomy import AdaptationTiming, TriggerSource


@dataclass
class AnalysisResult:
    """The output produced by one Analyzer pass over a single metric.

    Attributes:
        metric_name:     Name of the monitored metric.
        timing:          Whether this is a reactive or proactive analysis.
        trigger:         Which trigger source caused the anomaly, or *None*.
        anomaly_detected: *True* when a threshold violation was found.
        predicted_value: Extrapolated next value (proactive mode only).
        confidence:      Confidence in the prediction (0.0–1.0).
        details:         Human-readable explanation of the result.
    """

    metric_name: str
    timing: AdaptationTiming
    trigger: TriggerSource | None
    anomaly_detected: bool
    predicted_value: float | None = None
    confidence: float = 1.0
    details: str = ""
    raw_values: list[float] = field(default_factory=list)


class Analyzer:
    """Implements reactive anomaly detection and proactive linear forecasting.

    Both modes read exclusively from the shared KnowledgeBase so that the
    Analyze stage remains decoupled from the Monitor implementation.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self._kb = knowledge_base

    # ------------------------------------------------------------------
    # Reactive analysis
    # ------------------------------------------------------------------

    def detect_anomaly(
        self,
        metric_name: str,
        threshold: float,
        trigger: TriggerSource = TriggerSource.TECHNICAL_RESOURCES,
    ) -> AnalysisResult:
        """Reactive: flag the latest observation if it exceeds *threshold*.

        Args:
            metric_name: Metric to inspect.
            threshold:   Upper bound beyond which an anomaly is declared.
            trigger:     Which :class:`~loop_engineering.taxonomy.TriggerSource`
                         to attribute the anomaly to.

        Returns:
            An :class:`AnalysisResult` with *timing* set to
            :attr:`~loop_engineering.taxonomy.AdaptationTiming.REACTIVE`.
        """
        records = self._kb.get_monitoring_records(metric_name)
        if not records:
            return AnalysisResult(
                metric_name=metric_name,
                timing=AdaptationTiming.REACTIVE,
                trigger=None,
                anomaly_detected=False,
                details="No monitoring data available.",
            )
        try:
            raw_values = [float(r.value) for r in records]
        except (TypeError, ValueError) as exc:
            return AnalysisResult(
                metric_name=metric_name,
                timing=AdaptationTiming.REACTIVE,
                trigger=None,
                anomaly_detected=False,
                details=f"Non-numeric monitoring value for '{metric_name}': {exc}",
            )
        latest_value = raw_values[-1]
        anomaly = latest_value > threshold
        return AnalysisResult(
            metric_name=metric_name,
            timing=AdaptationTiming.REACTIVE,
            trigger=trigger if anomaly else None,
            anomaly_detected=anomaly,
            raw_values=raw_values,
            details=(
                f"Latest value {latest_value} {'>' if anomaly else '<='} "
                f"threshold {threshold}."
            ),
        )

    # ------------------------------------------------------------------
    # Proactive analysis
    # ------------------------------------------------------------------

    def forecast(
        self,
        metric_name: str,
        window: int = 5,
    ) -> AnalysisResult:
        """Proactive: extrapolate the next value using a linear trend.

        A simple first-order projection is used (``trend = last - first``
        within the window).  More sophisticated ML-based forecasting is
        planned for Phase 3 of the roadmap.

        Args:
            metric_name: Metric to forecast.
            window:      Number of most-recent records to include in the
                         trend calculation.

        Returns:
            An :class:`AnalysisResult` with *timing* set to
            :attr:`~loop_engineering.taxonomy.AdaptationTiming.PROACTIVE`.
        """
        records = self._kb.get_monitoring_records(metric_name)
        try:
            values = [float(r.value) for r in records[-window:]]
        except (TypeError, ValueError) as exc:
            return AnalysisResult(
                metric_name=metric_name,
                timing=AdaptationTiming.PROACTIVE,
                trigger=None,
                anomaly_detected=False,
                predicted_value=None,
                details=f"Non-numeric monitoring value for '{metric_name}': {exc}",
            )
        if len(values) < 2:
            return AnalysisResult(
                metric_name=metric_name,
                timing=AdaptationTiming.PROACTIVE,
                trigger=None,
                anomaly_detected=False,
                details="Insufficient data for forecasting (need ≥ 2 records).",
            )
        trend = values[-1] - values[0]
        predicted = values[-1] + trend
        # Confidence decays with window size to reflect greater uncertainty
        confidence = max(0.0, 1.0 - (len(values) - 2) * 0.05)
        return AnalysisResult(
            metric_name=metric_name,
            timing=AdaptationTiming.PROACTIVE,
            trigger=None,
            anomaly_detected=False,
            predicted_value=predicted,
            confidence=round(confidence, 4),
            raw_values=values,
            details=(
                f"Linear trend over {len(values)} samples: {trend:+.3f}; "
                f"predicted next value: {predicted:.3f}."
            ),
        )
