"""
Workflow state.

This module defines the state carried through the agentic video
generation workflow.

Workflow:

    VideoRequest
        ↓
    PlannerAgent
        ↓
    ScriptAgent
        ↓
    StoryboardAgent
        ↓
    WorkflowState

The state object stores intermediate outputs and workflow status.
It does not execute agents or contain orchestration logic.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest
from app.schemas.script import Script
from app.schemas.storyboard import Storyboard


# ---------------------------------------------------------------------------
# Workflow status
# ---------------------------------------------------------------------------

WORKFLOW_PENDING = "pending"
WORKFLOW_PLANNING = "planning"
WORKFLOW_SCRIPTING = "scripting"
WORKFLOW_STORYBOARDING = "storyboarding"
WORKFLOW_COMPLETED = "completed"
WORKFLOW_FAILED = "failed"


# ---------------------------------------------------------------------------
# Workflow state
# ---------------------------------------------------------------------------

@dataclass
class WorkflowState:
    """
    Store the current state of one video-generation workflow.

    The state is intentionally independent from FastAPI, databases,
    and LLM providers so it can be used by the orchestrator and
    tested independently.
    """

    workflow_id: str
    request: VideoRequest

    status: str = WORKFLOW_PENDING

    current_stage: Optional[str] = None

    plan: Optional[VideoPlan] = None
    script: Optional[Script] = None
    storyboard: Optional[Storyboard] = None

    error: Optional[str] = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        )
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(
            timezone.utc,
        )
    )

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start_planning(self) -> None:
        """
        Mark the workflow as entering the planning stage.
        """

        self.status = WORKFLOW_PLANNING
        self.current_stage = "planner"
        self.error = None
        self.touch()

    def set_plan(
        self,
        plan: VideoPlan,
    ) -> None:
        """
        Store the generated VideoPlan.
        """

        self.plan = plan
        self.touch()

    def start_scripting(self) -> None:
        """
        Mark the workflow as entering the script stage.
        """

        self.status = WORKFLOW_SCRIPTING
        self.current_stage = "script"
        self.touch()

    def set_script(
        self,
        script: Script,
    ) -> None:
        """
        Store the generated Script.
        """

        self.script = script
        self.touch()

    def start_storyboarding(self) -> None:
        """
        Mark the workflow as entering the storyboard stage.
        """

        self.status = WORKFLOW_STORYBOARDING
        self.current_stage = "storyboard"
        self.touch()

    def set_storyboard(
        self,
        storyboard: Storyboard,
    ) -> None:
        """
        Store the generated Storyboard.
        """

        self.storyboard = storyboard
        self.touch()

    def complete(self) -> None:
        """
        Mark the workflow as successfully completed.
        """

        self.status = WORKFLOW_COMPLETED
        self.current_stage = None
        self.error = None
        self.touch()

    def fail(
        self,
        error: str,
    ) -> None:
        """
        Mark the workflow as failed.
        """

        self.status = WORKFLOW_FAILED
        self.error = str(error)
        self.touch()

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def is_completed(self) -> bool:
        """
        Return True when the workflow completed successfully.
        """

        return self.status == WORKFLOW_COMPLETED

    def is_failed(self) -> bool:
        """
        Return True when the workflow failed.
        """

        return self.status == WORKFLOW_FAILED

    def is_finished(self) -> bool:
        """
        Return True when the workflow reached a terminal state.
        """

        return self.status in {
            WORKFLOW_COMPLETED,
            WORKFLOW_FAILED,
        }

    def touch(self) -> None:
        """
        Update the state's modification timestamp.
        """

        self.updated_at = datetime.now(
            timezone.utc,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Convert workflow state into a JSON-friendly dictionary.
        """

        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "request": self.request.model_dump(),
            "plan": (
                self.plan.model_dump()
                if self.plan is not None
                else None
            ),
            "script": (
                self.script.model_dump()
                if self.script is not None
                else None
            ),
            "storyboard": (
                self.storyboard.model_dump()
                if self.storyboard is not None
                else None
            ),
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }