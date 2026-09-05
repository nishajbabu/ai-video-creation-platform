"""
Script Agent.

The Script Agent converts a structured VideoPlan into a complete,
scene-by-scene Script.

Workflow position:

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
"""

from typing import Any, Dict, Optional

from app.schemas.plan import VideoPlan
from app.schemas.script import Script, ScriptScene


class ScriptAgent:
    """
    Generates a structured script from a VideoPlan.

    The agent can operate in two modes:

    1. Deterministic mode
       Used when no LLM service is configured.

    2. LLM mode
       Used when an LLM service is injected.

    Provider-specific behavior remains outside this agent.
    """

    def __init__(
        self,
        llm_service: Optional[Any] = None,
    ):
        """
        Initialize the Script Agent.

        Args:
            llm_service:
                Optional LLM service used for structured script
                generation.
        """

        self.llm_service = llm_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_script(
        self,
        plan: VideoPlan,
    ) -> Script:
        """
        Create a complete script from a VideoPlan.

        If an LLM service is configured, structured LLM generation
        is used. Otherwise, a deterministic script is produced.
        """

        if self.llm_service is not None:
            return self._create_llm_script(
                plan,
            )

        return self._create_default_script(
            plan,
        )

    # ------------------------------------------------------------------
    # Deterministic script generation
    # ------------------------------------------------------------------

    def _create_default_script(
        self,
        plan: VideoPlan,
    ) -> Script:
        """
        Create a deterministic scene-by-scene script.

        This implementation provides a reliable baseline before
        LLM-backed script generation is connected.
        """

        scene_durations = self._allocate_scene_durations(
            duration=plan.duration,
            scene_count=plan.scene_count,
        )

        scenes = []

        for index, duration in enumerate(
            scene_durations,
            start=1,
        ):
            purpose = self._build_scene_purpose(
                scene_number=index,
                scene_count=plan.scene_count,
                plan=plan,
            )

            narration = self._build_scene_narration(
                scene_number=index,
                scene_count=plan.scene_count,
                plan=plan,
            )

            scenes.append(
                ScriptScene(
                    scene_id=index,
                    purpose=purpose,
                    duration=duration,
                    narration=narration,
                )
            )

        return Script(
            scenes=scenes,
        )

    # ------------------------------------------------------------------
    # Scene purpose
    # ------------------------------------------------------------------

    def _build_scene_purpose(
        self,
        *,
        scene_number: int,
        scene_count: int,
        plan: VideoPlan,
    ) -> str:
        """
        Determine the purpose of one script scene.
        """

        if scene_number == 1:
            return "Introduce the main subject and establish context."

        if scene_number == scene_count:
            return "Conclude the video and reinforce the main message."

        requirements = plan.content_requirements

        requirement_index = scene_number - 2

        if (
            requirements
            and requirement_index < len(requirements)
        ):
            return requirements[requirement_index]

        return (
            "Develop the main topic and communicate "
            "useful information to the audience."
        )

    # ------------------------------------------------------------------
    # Scene narration
    # ------------------------------------------------------------------

    def _build_scene_narration(
        self,
        *,
        scene_number: int,
        scene_count: int,
        plan: VideoPlan,
    ) -> str:
        """
        Create baseline narration for one scene.

        This deterministic narration is intentionally simple.
        LLM-backed generation will produce richer narration later.
        """

        if scene_number == 1:
            return (
                f"Welcome. In this video, we will explore "
                f"{plan.objective}"
            )

        if scene_number == scene_count:
            return (
                "Thank you for watching. "
                "We hope this overview provided a clear "
                "understanding of the topic."
            )

        requirements = plan.content_requirements

        requirement_index = scene_number - 2

        if (
            requirements
            and requirement_index < len(requirements)
        ):
            requirement = requirements[
                requirement_index
            ]

            return (
                f"Let's explore this important point: "
                f"{requirement}"
            )

        return (
            "Let's continue by examining another important "
            "part of the topic."
        )

    # ------------------------------------------------------------------
    # Duration allocation
    # ------------------------------------------------------------------

    @staticmethod
    def _allocate_scene_durations(
        *,
        duration: int,
        scene_count: int,
    ) -> list[int]:
        """
        Divide the target video duration across scenes.

        Every scene receives at least one second.

        Any remainder is distributed across the first scenes so
        that the total duration exactly matches the requested
        duration.
        """

        if scene_count <= 0:
            raise ValueError(
                "scene_count must be greater than zero"
            )

        if duration < scene_count:
            raise ValueError(
                "duration must be at least equal to scene_count"
            )

        base_duration = duration // scene_count

        remainder = duration % scene_count

        durations = []

        for index in range(scene_count):
            extra_second = (
                1
                if index < remainder
                else 0
            )

            durations.append(
                base_duration + extra_second
            )

        return durations

    # ------------------------------------------------------------------
    # LLM-backed generation
    # ------------------------------------------------------------------

    def _create_llm_script(
        self,
        plan: VideoPlan,
    ) -> Script:
        """
        Generate a structured script through the configured
        LLM service.
        """

        response_schema: Dict[str, Any] = (
            Script.model_json_schema()
        )

        result = self.llm_service.generate_structured(
            prompt=self._build_script_prompt(
                plan,
            ),
            response_schema=response_schema,
        )

        return Script.model_validate(
            result,
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_script_prompt(
        self,
        plan: VideoPlan,
    ) -> str:
        """
        Build the structured script-generation prompt.
        """

        requirements = "\n".join(
            f"- {requirement}"
            for requirement in plan.content_requirements
        )

        if not requirements:
            requirements = "- No additional content requirements."

        notes = "\n".join(
            f"- {note}"
            for note in plan.generation_notes
        )

        if not notes:
            notes = "- No additional generation notes."

        return (
            "Create a complete scene-by-scene video script "
            "from the following production plan.\n\n"
            f"Objective:\n{plan.objective}\n\n"
            f"Target audience:\n"
            f"{plan.target_audience or 'Not specified'}\n\n"
            f"Tone:\n"
            f"{plan.tone or 'Not specified'}\n\n"
            f"Style:\n"
            f"{plan.style or 'Not specified'}\n\n"
            f"Target duration:\n"
            f"{plan.duration} seconds\n\n"
            f"Number of scenes:\n"
            f"{plan.scene_count}\n\n"
            f"Content requirements:\n"
            f"{requirements}\n\n"
            f"Generation notes:\n"
            f"{notes}\n\n"
            "Return a structured Script containing exactly "
            "the planned number of scenes. "
            "Each scene must include a unique scene_id, "
            "a clear purpose, a duration, and narration."
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_llm_enabled(self) -> bool:
        """
        Return whether LLM-backed script generation is configured.
        """

        return self.llm_service is not None