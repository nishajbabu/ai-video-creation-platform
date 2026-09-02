"""
Storyboard Agent.

The Storyboard Agent converts a generated Script into a structured
Storyboard containing visual, asset, knowledge, and audio requirements.

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
        ↓
    Storyboard
"""

from typing import Any, Dict, Optional

from app.schemas.scene import (
    AssetRequirement,
    AudioRequirement,
    Scene,
)
from app.schemas.script import Script
from app.schemas.storyboard import Storyboard


class StoryboardAgent:
    """
    Creates a structured storyboard from a Script.

    The agent supports two modes:

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
        Initialize the Storyboard Agent.

        Args:
            llm_service:
                Optional LLM service used for structured storyboard
                generation.
        """

        self.llm_service = llm_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_storyboard(
        self,
        script: Script,
    ) -> Storyboard:
        """
        Convert a Script into a complete Storyboard.

        If an LLM service is configured, structured LLM generation
        is used. Otherwise, a deterministic storyboard is created.
        """

        if self.llm_service is not None:
            return self._create_llm_storyboard(
                script,
            )

        return self._create_default_storyboard(
            script,
        )

    # ------------------------------------------------------------------
    # Deterministic storyboard generation
    # ------------------------------------------------------------------

    def _create_default_storyboard(
        self,
        script: Script,
    ) -> Storyboard:
        """
        Create a deterministic storyboard from the script.

        Each ScriptScene becomes exactly one Scene.
        """

        scenes = []

        for script_scene in script.scenes:
            scene = Scene(
                scene_id=script_scene.scene_id,
                order=script_scene.scene_id,
                duration=script_scene.duration,
                purpose=script_scene.purpose,
                narration=script_scene.narration,
                visual_description=(
                    self._build_visual_description(
                        script_scene.purpose,
                    )
                ),
                visual_prompt=(
                    self._build_visual_prompt(
                        script_scene.purpose,
                        script_scene.narration,
                    )
                ),
                visual_type="image",
                text_overlay=None,
                asset_requirements=[
                    self._build_default_asset_requirement(
                        script_scene.purpose,
                    )
                ],
                knowledge_requirements=[],
                audio_requirements=AudioRequirement(
                    required=True,
                    voice_style="clear and professional",
                    background_music=False,
                ),
                transition=self._build_transition(
                    script_scene.scene_id,
                    len(script.scenes),
                ),
                status="planned",
            )

            scenes.append(scene)

        return Storyboard(
            scenes=scenes,
        )

    # ------------------------------------------------------------------
    # Visual description
    # ------------------------------------------------------------------

    @staticmethod
    def _build_visual_description(
        purpose: str,
    ) -> str:
        """
        Build a human-readable visual description.
        """

        return (
            "Show visuals that clearly communicate the following "
            f"scene purpose: {purpose}"
        )

    # ------------------------------------------------------------------
    # Visual prompt
    # ------------------------------------------------------------------

    @staticmethod
    def _build_visual_prompt(
        purpose: str,
        narration: str,
    ) -> str:
        """
        Build a baseline visual-generation prompt.
        """

        return (
            "Create a professional cinematic visual for a video "
            "scene. The scene should communicate this purpose: "
            f"{purpose} "
            "The visual should support the narration: "
            f"{narration}"
        )

    # ------------------------------------------------------------------
    # Asset requirements
    # ------------------------------------------------------------------

    @staticmethod
    def _build_default_asset_requirement(
        purpose: str,
    ) -> AssetRequirement:
        """
        Build a baseline asset requirement for a scene.
        """

        return AssetRequirement(
            asset_type="image",
            description=(
                "A visual asset that supports the scene purpose: "
                f"{purpose}"
            ),
            source="ai_or_library",
        )

    # ------------------------------------------------------------------
    # Transitions
    # ------------------------------------------------------------------

    @staticmethod
    def _build_transition(
        scene_id: int,
        scene_count: int,
    ) -> Optional[str]:
        """
        Determine the transition after a scene.

        The final scene does not require a transition.
        """

        if scene_id >= scene_count:
            return None

        if scene_id == 1:
            return "fade"

        return "crossfade"

    # ------------------------------------------------------------------
    # LLM-backed storyboard generation
    # ------------------------------------------------------------------

    def _create_llm_storyboard(
        self,
        script: Script,
    ) -> Storyboard:
        """
        Generate a storyboard through the configured LLM service.
        """

        response_schema: Dict[str, Any] = (
            Storyboard.model_json_schema()
        )

        result = self.llm_service.generate_structured(
            prompt=self._build_storyboard_prompt(
                script,
            ),
            response_schema=response_schema,
        )

        return Storyboard.model_validate(
            result,
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_storyboard_prompt(
        self,
        script: Script,
    ) -> str:
        """
        Build the structured storyboard-generation prompt.
        """

        scene_sections = []

        for scene in script.scenes:
            scene_sections.append(
                (
                    f"Scene {scene.scene_id}\n"
                    f"Purpose: {scene.purpose}\n"
                    f"Duration: {scene.duration} seconds\n"
                    f"Narration: {scene.narration}"
                )
            )

        script_text = "\n\n".join(
            scene_sections
        )

        return (
            "Create a production-ready storyboard from the "
            "following video script.\n\n"
            f"{script_text}\n\n"
            "For every script scene, create exactly one storyboard "
            "scene.\n"
            "Preserve scene IDs, scene order, duration, purpose, "
            "and narration.\n"
            "Add meaningful visual descriptions, visual-generation "
            "prompts, asset requirements, knowledge requirements, "
            "audio requirements, and transitions where appropriate."
        )

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def is_llm_enabled(self) -> bool:
        """
        Return whether LLM-backed storyboard generation is configured.
        """

        return self.llm_service is not None