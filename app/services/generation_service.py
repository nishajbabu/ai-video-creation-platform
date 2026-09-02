"""
Video generation service.

This module coordinates the video-generation workflow at the
application-service level.

Responsibilities:
    - Accept validated VideoRequest objects.
    - Connect the workflow to the configured LLM service.
    - Delegate workflow execution to the Orchestrator.
    - Keep API routes independent from agent implementation details.
    - Return a consistent generation result.
"""

from typing import Any, Dict, Optional

from app.schemas.requests import VideoRequest


class GenerationService:
    """
    Application service for starting video-generation workflows.

    Dependency flow:

        API Route
            ↓
        GenerationService
            ↓
        Orchestrator
            ↓
        Planner / Script / Storyboard Agents
            ↓
        LLMService
    """

    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        llm_service: Optional[Any] = None,
    ):
        """
        Initialize the generation service.

        Args:
            orchestrator:
                Optional pre-configured workflow orchestrator.

            llm_service:
                Optional shared LLM service.

        If an orchestrator is supplied, it is used directly.

        If only an LLM service is supplied, the service creates
        an orchestrator configured with that LLM service.

        If neither is supplied, the service remains unconfigured.
        This preserves the lightweight unit-test behavior.
        """

        self.orchestrator = orchestrator

        if (
            self.orchestrator is None
            and llm_service is not None
        ):
            self.orchestrator = (
                self._create_orchestrator(
                    llm_service,
                )
            )

    # ------------------------------------------------------------------
    # Orchestrator creation
    # ------------------------------------------------------------------

    @staticmethod
    def _create_orchestrator(
        llm_service: Any,
    ) -> Any:
        """
        Create an Orchestrator whose agents share the same LLM service.

        The LLM service is injected into PlannerAgent, ScriptAgent,
        and StoryboardAgent.
        """

        from app.agents.orchestrator import Orchestrator
        from app.agents.planner import PlannerAgent
        from app.agents.script import ScriptAgent
        from app.agents.storyboard import StoryboardAgent

        planner = PlannerAgent(
            llm_service=llm_service,
        )

        script_agent = ScriptAgent(
            llm_service=llm_service,
        )

        storyboard_agent = StoryboardAgent(
            llm_service=llm_service,
        )

        return Orchestrator(
            planner=planner,
            script_agent=script_agent,
            storyboard_agent=storyboard_agent,
        )

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def start_generation(
        self,
        request: VideoRequest,
    ) -> Dict[str, Any]:
        """
        Start a video-generation workflow.

        When no orchestrator is configured, the service returns
        a structured acknowledgement.

        When configured, the request is delegated to the
        orchestrator.
        """

        if self.orchestrator is None:
            return {
                "status": "accepted",
                "prompt": request.prompt,
                "duration": request.duration,
                "workflow_started": False,
                "message": (
                    "Generation request accepted. "
                    "Workflow orchestrator is not configured."
                ),
            }

        result = self.orchestrator.run(
            request,
        )

        return self._normalize_result(
            result,
        )

    # ------------------------------------------------------------------
    # Result normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> Dict[str, Any]:
        """
        Normalize an orchestrator result into a dictionary.
        """

        if isinstance(result, dict):
            return result

        if hasattr(result, "model_dump"):
            return result.model_dump()

        if hasattr(result, "dict"):
            return result.dict()

        return {
            "status": "completed",
            "result": result,
        }

    # ------------------------------------------------------------------
    # Workflow status
    # ------------------------------------------------------------------

    def is_configured(self) -> bool:
        """
        Return whether a workflow orchestrator is configured.
        """

        return self.orchestrator is not None