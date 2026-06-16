"""Monitor component of the MAPE-K loop.

Based on Section 2 of the technical roadmap:
    "Deploy adaptive monitoring sensors to throttle telemetry based on
    anomaly detection thresholds, balancing the cost of continuous
    observation against resource constraints."
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from loop_engineering.knowledge import KnowledgeBase, MonitoringRecord
from loop_engineering.taxonomy import TriggerSource


@dataclass
class Sensor:
    """A named probe that periodically samples a single metric.

    Attributes:
        name:      Unique sensor identifier, used as the *metric_name* in
                   :class:`~loop_engineering.knowledge.MonitoringRecord`.
        source:    Which :class:`~loop_engineering.taxonomy.TriggerSource`
                   category this sensor belongs to.
        threshold: Optional upper bound for anomaly detection.  When a
                   sampled value exceeds this value, :meth:`Monitor.is_anomaly`
                   returns *True*.
        sampler:   Callable that reads the current metric value.  May be
                   *None* for placeholder sensors registered before their
                   data source is available.
    """

    name: str
    source: TriggerSource
    threshold: float | None = None
    sampler: Callable[[], float | int | str] | None = None


class Monitor:
    """Deploys sensors and records telemetry into the shared KnowledgeBase.

    Throttling is implicit: callers drive the sample cadence and can skip
    sensors whose thresholds have not been breached, keeping observation
    overhead proportional to detected anomalies.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self._kb = knowledge_base
        self._sensors: dict[str, Sensor] = {}

    # ------------------------------------------------------------------
    # Sensor management
    # ------------------------------------------------------------------

    def register_sensor(self, sensor: Sensor) -> None:
        """Add or replace a sensor."""
        self._sensors[sensor.name] = sensor

    def unregister_sensor(self, name: str) -> bool:
        """Remove a sensor by name.  Returns *True* if the sensor existed."""
        return self._sensors.pop(name, None) is not None

    def get_sensor(self, name: str) -> Sensor | None:
        """Return the sensor with *name*, or *None* if not registered."""
        return self._sensors.get(name)

    def list_sensors(self) -> list[str]:
        """Return the names of all registered sensors."""
        return list(self._sensors.keys())

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    def sample(self, sensor_name: str) -> MonitoringRecord | None:
        """Invoke *sensor_name*'s sampler and persist the result.

        Returns *None* when the sensor is not registered or has no sampler.
        """
        sensor = self._sensors.get(sensor_name)
        if sensor is None or sensor.sampler is None:
            return None
        value = sensor.sampler()
        record = MonitoringRecord(
            timestamp=time.time(),
            metric_name=sensor_name,
            value=value,
            source=sensor.source.name,
        )
        self._kb.store_monitoring_record(record)
        return record

    def sample_all(self) -> list[MonitoringRecord]:
        """Sample every registered sensor that has a sampler."""
        records: list[MonitoringRecord] = []
        for name in list(self._sensors):
            rec = self.sample(name)
            if rec is not None:
                records.append(rec)
        return records

    # ------------------------------------------------------------------
    # Threshold-based anomaly gate
    # ------------------------------------------------------------------

    def is_anomaly(self, sensor_name: str, value: float | int | str) -> bool:
        """Return *True* when *value* exceeds the sensor's threshold.

        Returns *False* when the sensor has no threshold or the value cannot
        be compared numerically.
        """
        sensor = self._sensors.get(sensor_name)
        if sensor is None or sensor.threshold is None:
            return False
        try:
            return float(value) > sensor.threshold
        except (TypeError, ValueError):
            return False
