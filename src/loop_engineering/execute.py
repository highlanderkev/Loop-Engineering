"""Execute component of the MAPE-K loop.

Based on Section 2 of the technical roadmap:
    "Control effectors to manifest changes across the identified system
    levels (Application, System Software, etc.) through precise intercession."

Effectors are registered callables so that the Execute stage remains
decoupled from the underlying managed resources.  This mirrors the
External Adaptation Logic (AL) principle from Section 3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from loop_engineering.knowledge import KnowledgeBase
from loop_engineering.plan import AdaptationAction, AdaptationPlan


@dataclass
class EffectorResult:
    """Outcome of invoking a single effector.

    Attributes:
        action_name: Name of the action that was attempted.
        success:     Whether the effector reported success.
        details:     Human-readable explanation of the outcome.
    """

    action_name: str
    success: bool
    details: str = ""


class Executor:
    """Invokes registered effectors to realise adaptation plans.

    Effectors are plain callables that accept an :class:`AdaptationAction`
    and return a boolean indicating success.  Registering effectors at
    runtime (rather than hard-coding them) implements the *intercession*
    side of self-reflection described in Section 3 of the roadmap.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        self._kb = knowledge_base
        self._effectors: dict[str, Callable[[AdaptationAction], bool]] = {}

    # ------------------------------------------------------------------
    # Effector registry
    # ------------------------------------------------------------------

    def register_effector(
        self,
        name: str,
        effector: Callable[[AdaptationAction], bool],
    ) -> None:
        """Bind *name* to *effector* so the Executor can invoke it."""
        self._effectors[name] = effector

    def unregister_effector(self, name: str) -> bool:
        """Remove the effector bound to *name*.  Returns *True* if found."""
        return self._effectors.pop(name, None) is not None

    def list_effectors(self) -> list[str]:
        """Return the names of all registered effectors."""
        return list(self._effectors.keys())

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute_action(self, action: AdaptationAction) -> EffectorResult:
        """Invoke the effector for *action* and capture the outcome.

        Returns an unsuccessful :class:`EffectorResult` when no effector is
        registered for the action name, or when the effector raises an
        exception, so that the Execute stage never propagates exceptions into
        the MAPE-K loop.
        """
        effector = self._effectors.get(action.name)
        if effector is None:
            return EffectorResult(
                action_name=action.name,
                success=False,
                details=f"No effector registered for action '{action.name}'.",
            )
        try:
            success = effector(action)
            return EffectorResult(
                action_name=action.name,
                success=success,
                details=(
                    "Effector completed successfully."
                    if success
                    else "Effector reported failure."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return EffectorResult(
                action_name=action.name,
                success=False,
                details=f"Effector raised an exception: {exc}",
            )

    def execute_plan(self, plan: AdaptationPlan) -> list[EffectorResult]:
        """Execute every action in *plan* in order.

        Args:
            plan: The :class:`~loop_engineering.plan.AdaptationPlan` to realise.

        Returns:
            One :class:`EffectorResult` per action.
        """
        return [self.execute_action(action) for action in plan.actions]
