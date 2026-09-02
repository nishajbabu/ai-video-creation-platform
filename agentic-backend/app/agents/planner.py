"""
Planner agent.

The Planner Agent converts a high-level video request into a
structured VideoPlan.

Workflow position:

    VideoRequest
        ↓
    PlannerAgent
        ↓
    VideoPlan
        ↓
    ScriptAgent
"""

from typing import Any, Dict, Optional

from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest


class PlannerAgent:
    """
    Creates a structured production plan from a VideoRequest.

    The agent is independent of any specific LLM provider.
    An LLM service can be injected when LLM-backed planning
    is required.

    Without an LLM service, the planner uses deterministic
    planning logic so that the component remains testable
    without external API calls.
    """

    def __init__(
        self,
        llm_service: Optional[Any] = None,
    ):
        """
        Initialize the Planner Agent.

        Args:
            llm_service:
                Optional LLM service used to generate the plan.
                When omitted, deterministic planning is used.
        """

        self.llm_service = llm_service

    # ------------------------------------------------------------------
    # Public planning API
    # ------------------------------------------------------------------

    def create_plan(
        self,
        request: VideoRequest,
    ) -> VideoPlan:
        """
        Convert a VideoRequest into a structured VideoPlan.

        If an LLM service is configured, LLM-backed structured
        generation is used.

        Otherwise, a deterministic plan is generated.
        """

        if self.llm_service is not None:
            return self._create_llm_plan(
                request,
            )

        return self._create_default_plan(
            request,
        )

    # ------------------------------------------------------------------
    # Deterministic planning
    # ------------------------------------------------------------------

    def _create_default_plan(
        self,
        request: VideoRequest,
    ) -> VideoPlan:
        """
        Create a deterministic production plan.

        This provides a reliable baseline while the LLM planning
        integration is being implemented.
        """

        style = request.style or "professional"
        audience = (
            request.target_audience
            or "General audience"
        )
        tone = request.tone or "professional"

        objective = (
            f"Create a {style} video "
            f"for {audience}."
        )

        content_requirements = [
            "Introduce the main subject or product.",
            "Explain the primary value or problem being addressed.",
            "Present the key features or benefits.",
            "End with a clear conclusion or call to action.",
        ]

        generation_notes = [
            f"Use a {tone} communication tone.",
            (
                "Target a total duration of approximately "
                f"{request.duration} seconds."
            ),
        ]

        if request.supporting_files:
            generation_notes.append(
                "Incorporate the supplied supporting assets "
                "where appropriate."
            )

        scene_count = self._estimate_scene_count(
            request.duration,
        )

        return VideoPlan(
            objective=objective,
            target_audience=audience,
            tone=tone,
            style=style,
            duration=request.duration,
            scene_count=scene_count,
            content_requirements=content_requirements,
            generation_notes=generation_notes,
        )

    # ------------------------------------------------------------------
    # LLM planning
    # ------------------------------------------------------------------

    def _create_llm_plan(
        self,
        request: VideoRequest,
    ) -> VideoPlan:
        """
        Create a plan through the configured LLM service.

        The LLM service is responsible for communicating with the
        selected provider. The Planner only requests structured
        output and validates the returned data.
        """

        response_schema: Dict[str, Any] = (
            VideoPlan.model_json_schema()
        )

        result = self.llm_service.generate_structured(
            prompt=self._build_planning_prompt(
                request,
            ),
            response_schema=response_schema,
        )

        return VideoPlan.model_validate(
            result,
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_planning_prompt(
        self,
        request: VideoRequest,
    ) -> str:
        """
        Build the planning instruction sent to the LLM service.
        """

        supporting_files = ", ".join(
            request.supporting_files
        )

        if not supporting_files:
            supporting_files = "none"

        style = request.style or "not specified"
        audience = (
            request.target_audience
            or "not specified"
        )
        tone = request.tone or "not specified"

        return (
            "Create a structured production plan for an "
            "AI-generated video.\n\n"
            f"Video request:\n{request.prompt}\n\n"
            f"Duration: {request.duration} seconds\n"
            f"Style: {style}\n"
            f"Target audience: {audience}\n"
            f"Tone: {tone}\n"
            f"Supporting files: {supporting_files}\n\n"
            "Return a production-ready VideoPlan. "
            "Do not write the complete script or storyboard."
        )

    # ------------------------------------------------------------------
    # Scene estimation
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_scene_count(
        duration: int,
    ) -> int:
        """
        Estimate an initial number of scenes from video duration.

        The storyboard stage can later refine the exact scene
        structure.
        """

        if duration <= 30:
            return 3

        if duration <= 60:
            return 5

        if duration <= 120:
            return 8

        return max(
            10,
            min(
                20,
                duration // 15,
            ),
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_llm_enabled(self) -> bool:
        """
        Return whether LLM-backed planning is configured.
        """

        return self.llm_service is not None