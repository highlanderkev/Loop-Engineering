# Loop Engineering

A Python implementation of the Self-Adaptive Systems (SAS) MAPE-K framework, aligned with the *Technical Roadmap: Engineering Advanced Adaptation Loops for Self-Adaptive Systems*.

## Overview

The package provides a composable, test-driven reference implementation of the four-phase MAPE-K control loop:

| Component | Responsibility |
| :--- | :--- |
| **Monitor** | Deploy adaptive sensors; throttle telemetry via anomaly thresholds |
| **Analyze** | Reactive anomaly detection; proactive linear forecasting (Phase 3 will add ML/RL) |
| **Plan** | Rules-based and utility-based adaptation plan generation |
| **Execute** | Invoke registered effectors; isolate the adaptation logic from managed resources |
| **Knowledge** | Shared repository for monitoring records, architectural models, and policies |

The taxonomy module encodes the full **5W+1H** framework from the roadmap:

| Dimension | Enum | Notes |
| :--- | :--- | :--- |
| *When* | `AdaptationTiming` | `REACTIVE` / `PROACTIVE` |
| *Why* | `TriggerSource` | Technical resources, context, user preferences |
| *Where* | `AdaptationLevel` | Application, system software, communication |
| *What* | `AdaptationTechnique` | Parameter, structural, contextual |
| *How* | `DecisionMetric` | Model-based, rules, goal-based, utility-based |
| *Who* | N/A | Always the autonomous adaptation logic |

## Roadmap alignment

| Phase | Description | Status |
| :--- | :--- | :--- |
| 1 – Modeling & Simulation | MAPE-K loop with digital-twin-ready sensor abstraction | ✅ Implemented |
| 2 – Logic Decoupling | External AL via registered effectors and a shared KnowledgeBase | ✅ Implemented |
| 3 – Proactive Integration | ML/RL-based forecasting (replaces linear trend) | 🔜 Planned |
| 4 – Context Actuation | Environmental actuators in planning logic | 🔜 Planned |

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
pip install -e ".[dev]"
```

### Quick example

```python
from loop_engineering import (
    MAPEKLoop,
    Sensor,
    Policy,
    TriggerSource,
)

loop = MAPEKLoop()

# Register a CPU sensor with an 80 % threshold
loop.monitor.register_sensor(
    Sensor(name="cpu_usage", source=TriggerSource.TECHNICAL_RESOURCES,
           threshold=80.0, sampler=lambda: 92.0)
)

# Declare a remediation policy
loop.knowledge_base.add_policy(
    Policy(name="throttle_cpu", condition="cpu_usage", action="scale_out")
)

# Bind an effector that carries out the action
loop.executor.register_effector("scale_out", lambda action: True)

result = loop.run_cycle(anomaly_thresholds={"cpu_usage": 80.0})
print(result.anomalies_detected)   # 1
print(result.actions_succeeded)    # 1
```

### Long-running agents with LangGraph

```python
from loop_engineering import LangGraphMAPEKAgent

agent = LangGraphMAPEKAgent()

# Run two persisted cycles on the same thread
first = agent.run(thread_id="sas-agent-1", cycles=1)
second = agent.run(thread_id="sas-agent-1", cycles=1)

print(first.cycles_completed)   # 1
print(second.cycles_completed)  # 2
```

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check src tests
```

## Project Structure

```
Loop-Engineering/
├── src/
│   └── loop_engineering/
│       ├── __init__.py      # public API exports
│       ├── taxonomy.py      # 5W+1H SAS taxonomy (enums & AdaptationContext)
│       ├── knowledge.py     # KnowledgeBase – monitoring records, models, policies
│       ├── monitor.py       # Monitor – sensor registration & sampling
│       ├── analyze.py       # Analyzer – reactive detection & proactive forecast
│       ├── plan.py          # Planner – rules-based & utility-based planning
│       ├── execute.py       # Executor – effector registry & plan execution
│       ├── mape_k.py        # MAPEKLoop – full MAPE-K orchestrator
│       ├── langgraph_agent.py # LangGraph long-running orchestration
│       └── core.py          # legacy scaffold helpers
├── tests/
│   ├── test_taxonomy.py
│   ├── test_knowledge.py
│   ├── test_monitor.py
│   ├── test_analyze.py
│   ├── test_plan.py
│   ├── test_execute.py
│   ├── test_mape_k.py
│   └── test_core.py
├── Technical Roadmap_ Engineering Advanced Adaptation Loops …md
├── pyproject.toml
└── README.md
```

## License

MIT