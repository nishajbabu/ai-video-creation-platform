"""
Workflow orchestrator.

The Orchestrator coordinates the complete video-generation
planning workflow:

    VideoRequest
        ↓
    PlannerAgent
        ↓
    VideoPlan
        ↓
    ScriptAgent
        ↓
    Script
        ↓
    StoryboardAgent
        ↓
    Storyboard

The Orchestrator is responsible for coordination only.
Individual agents remain responsible for their own generation logic.

WorkflowState is used to track intermediate results and the current
workflow stage.

An optional LLMService can be injected into the orchestrator.
When provided, the same shared LLM service is passed to all three
generation agents.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from app.agents.planner import PlannerAgent
from app.agents.script import ScriptAgent
from app.agents.storyboard import StoryboardAgent
from app.llm.service import LLMService
from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest
from app.schemas.script import Script
from app.schemas.storyboard import Storyboard
from app.state.workflow_state import WorkflowState


# ---------------------------------------------------------------------------
# Workflow result
# ---------------------------------------------------------------------------

@dataclass
class WorkflowResult:
    """
    Result produced by the complete generation workflow.

    workflow_id uniquely identifies one execution of the workflow.
    """

    workflow_id: str
    status: str
    request: VideoRequest
    plan: Optional[VideoPlan] = None
    script: Optional[Script] = None
    storyboard: Optional[Storyboard] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Coordinate Planner, Script, and Storyboard agents.

    The orchestrator owns the workflow state while individual agents
    remain responsible for their own generation logic.

    An optional shared LLMService can be supplied. When supplied,
    it is injected into all generation agents.
    """

    def __init__(
        self,
        planner: Optional[PlannerAgent] = None,
        script_agent: Optional[ScriptAgent] = None,
        storyboard_agent: Optional[StoryboardAgent] = None,
        llm_service: Optional[LLMService] = None,
    ):
        """
        Initialize the workflow orchestrator.

        Agents can be injected directly for testing.

        When an LLMService is supplied, it is shared by the
        Planner, Script, and Storyboard agents.

        When no LLMService is supplied, the agents operate in
        their existing deterministic mode.
        """

        self.llm_service = llm_service

        self.planner = (
            planner
            or PlannerAgent(
                llm_service=llm_service,
            )
        )

        self.script_agent = (
            script_agent
            or ScriptAgent(
                llm_service=llm_service,
            )
        )

        self.storyboard_agent = (
            storyboard_agent
            or StoryboardAgent(
                llm_service=llm_service,
            )
        )

        # The most recently executed workflow state.
        self.workflow_state: Optional[WorkflowState] = None

    # ------------------------------------------------------------------
    # Public workflow
    # ------------------------------------------------------------------

    def run(
        self,
        request: VideoRequest,
    ) -> dict:
        """
        Execute the complete video-generation planning workflow.

        Workflow:

            request
                ↓
            planner
                ↓
            plan
                ↓
            script
                ↓
            storyboard
                ↓
            completed

        WorkflowState is updated after every successful stage.

        If any stage fails:

            1. The workflow state is marked as failed.
            2. The original exception is re-raised.

        This preserves the existing error-handling behavior while
        allowing callers and tests to inspect the workflow state.
        """

        # One unique ID is created for this complete workflow execution.
        workflow_id = self._create_workflow_id()

        state = WorkflowState(
            workflow_id=workflow_id,
            request=request,
        )

        self.workflow_state = state

        try:
            # ----------------------------------------------------------
            # Planning
            # ----------------------------------------------------------

            state.start_planning()

            plan = self.planner.create_plan(
                request,
            )

            state.set_plan(
                plan,
            )

            # ----------------------------------------------------------
            # Script generation
            # ----------------------------------------------------------

            state.start_scripting()

            script = self.script_agent.create_script(
                plan,
            )

            state.set_script(
                script,
            )

            # ----------------------------------------------------------
            # Storyboard generation
            # ----------------------------------------------------------

            state.start_storyboarding()

            storyboard = (
                self.storyboard_agent.create_storyboard(
                    script,
                )
            )

            state.set_storyboard(
                storyboard,
            )

            # ----------------------------------------------------------
            # Completion
            # ----------------------------------------------------------

            state.complete()

            result = WorkflowResult(
                workflow_id=workflow_id,
                status="completed",
                request=request,
                plan=plan,
                script=script,
                storyboard=storyboard,
            )

            return self._serialize_result(
                result,
            )

        except Exception as exc:
            # Preserve the original exception while recording
            # the failure inside WorkflowState.
            state.fail(
                str(exc),
            )

            raise

    # ------------------------------------------------------------------
    # Workflow stages
    # ------------------------------------------------------------------

    def create_plan(
        self,
        request: VideoRequest,
    ) -> VideoPlan:
        """
        Execute only the planning stage.
        """

        return self.planner.create_plan(
            request,
        )

    def create_script(
        self,
        plan: VideoPlan,
    ) -> Script:
        """
        Execute only the script stage.
        """

        return self.script_agent.create_script(
            plan,
        )

    def create_storyboard(
        self,
        script: Script,
    ) -> Storyboard:
        """
        Execute only the storyboard stage.
        """

        return (
            self.storyboard_agent.create_storyboard(
                script,
            )
        )

    # ------------------------------------------------------------------
    # Workflow state
    # ------------------------------------------------------------------

    def get_workflow_state(
        self,
    ) -> Optional[WorkflowState]:
        """
        Return the most recently executed workflow state.

        Returns:
            WorkflowState when run() has been executed.

            None when no workflow has been started yet.
        """

        return self.workflow_state

    # ------------------------------------------------------------------
    # Workflow ID
    # ------------------------------------------------------------------

    @staticmethod
    def _create_workflow_id() -> str:
        """
        Create a unique identifier for a workflow execution.
        """

        return f"workflow_{uuid4().hex}"

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return whether all three workflow agents are available.
        """

        return (
            self.planner is not None
            and self.script_agent is not None
            and self.storyboard_agent is not None
        )

    def is_llm_enabled(self) -> bool:
        """
        Return whether a shared LLM service has been configured.
        """

        return self.llm_service is not None

    # ------------------------------------------------------------------
    # Result serialization
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_result(
        result: WorkflowResult,
    ) -> dict:
        """
        Convert the internal WorkflowResult into a dictionary.

        Pydantic models are converted using model_dump().
        """

        return {
            "workflow_id": result.workflow_id,
            "status": result.status,
            "request": result.request.model_dump(),
            "plan": (
                result.plan.model_dump()
                if result.plan is not None
                else None
            ),
            "script": (
                result.script.model_dump()
                if result.script is not None
                else None
            ),
            "storyboard": (
                result.storyboard.model_dump()
                if result.storyboard is not None
                else None
            ),
            "error": result.error,
        }