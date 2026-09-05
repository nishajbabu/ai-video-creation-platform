"""
Unit tests for the Planner, Script, and Storyboard agents.

These tests verify the responsibilities of each agent independently
from the full API/workflow integration.

Agent flow:

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

import pytest

from app.agents.planner import PlannerAgent
from app.agents.script import ScriptAgent
from app.agents.storyboard import StoryboardAgent
from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest
from app.schemas.script import Script
from app.schemas.storyboard import Storyboard


# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------


def create_video_request(
    *,
    duration: int = 60,
    style: str = "professional",
    target_audience: str = "Potential customers",
    tone: str = "confident",
) -> VideoRequest:
    """
    Create a valid VideoRequest for agent tests.
    """

    return VideoRequest(
        prompt=(
            "Create a professional AI product introduction "
            "video explaining the main product benefits."
        ),
        duration=duration,
        style=style,
        target_audience=target_audience,
        tone=tone,
    )


def create_video_plan(
    *,
    duration: int = 60,
    scene_count: int = 5,
) -> VideoPlan:
    """
    Create a valid VideoPlan for ScriptAgent tests.
    """

    return VideoPlan(
        objective=(
            "Create a professional AI product introduction video."
        ),
        target_audience="Potential customers",
        tone="confident",
        style="professional",
        duration=duration,
        scene_count=scene_count,
        content_requirements=[
            "Introduce the product.",
            "Explain the main problem.",
            "Present the key benefits.",
            "End with a clear call to action.",
        ],
        generation_notes=[
            "Keep the communication clear and professional.",
        ],
    )


# ===========================================================================
# PlannerAgent
# ===========================================================================


class TestPlannerAgent:
    """
    Tests for PlannerAgent.
    """

    def test_create_plan_returns_video_plan(self):
        """
        PlannerAgent should convert a valid request into VideoPlan.
        """

        agent = PlannerAgent()

        result = agent.create_plan(
            create_video_request(),
        )

        assert isinstance(
            result,
            VideoPlan,
        )

    def test_create_plan_preserves_requested_duration(self):
        """
        PlannerAgent should preserve the requested video duration.
        """

        request = create_video_request(
            duration=90,
        )

        result = PlannerAgent().create_plan(
            request,
        )

        assert result.duration == 90

    def test_create_plan_preserves_style(self):
        """
        PlannerAgent should preserve the requested style.
        """

        request = create_video_request(
            style="cinematic",
        )

        result = PlannerAgent().create_plan(
            request,
        )

        assert result.style == "cinematic"

    def test_create_plan_preserves_target_audience(self):
        """
        PlannerAgent should preserve the requested target audience.
        """

        request = create_video_request(
            target_audience="Software developers",
        )

        result = PlannerAgent().create_plan(
            request,
        )

        assert result.target_audience == "Software developers"

    def test_create_plan_preserves_tone(self):
        """
        PlannerAgent should preserve the requested tone.
        """

        request = create_video_request(
            tone="educational",
        )

        result = PlannerAgent().create_plan(
            request,
        )

        assert result.tone == "educational"

    def test_create_plan_generates_positive_scene_count(self):
        """
        PlannerAgent should always produce at least one scene.
        """

        result = PlannerAgent().create_plan(
            create_video_request(),
        )

        assert result.scene_count >= 1

    def test_create_plan_scene_count_matches_duration_rules(self):
        """
        Verify the deterministic scene-count estimation rules.
        """

        agent = PlannerAgent()

        short_plan = agent.create_plan(
            create_video_request(
                duration=30,
            ),
        )

        medium_plan = agent.create_plan(
            create_video_request(
                duration=60,
            ),
        )

        long_plan = agent.create_plan(
            create_video_request(
                duration=120,
            ),
        )

        assert short_plan.scene_count == 3
        assert medium_plan.scene_count == 5
        assert long_plan.scene_count == 8

    def test_create_plan_adds_default_values_when_optional_fields_missing(
        self,
    ):
        """
        PlannerAgent should provide sensible defaults for omitted
        optional request fields.
        """

        request = VideoRequest(
            prompt=(
                "Create an educational video about artificial "
                "intelligence."
            ),
            duration=60,
        )

        result = PlannerAgent().create_plan(
            request,
        )

        assert result.style == "professional"
        assert result.target_audience == "General audience"
        assert result.tone == "professional"

    def test_create_plan_includes_content_requirements(self):
        """
        PlannerAgent should provide downstream content requirements.
        """

        result = PlannerAgent().create_plan(
            create_video_request(),
        )

        assert len(
            result.content_requirements,
        ) > 0

    def test_create_plan_includes_generation_notes(self):
        """
        PlannerAgent should provide downstream generation notes.
        """

        result = PlannerAgent().create_plan(
            create_video_request(),
        )

        assert len(
            result.generation_notes,
        ) > 0

    def test_create_plan_records_supporting_files_in_generation_notes(
        self,
    ):
        """
        Supporting files should be acknowledged by the generated plan.
        """

        request = VideoRequest(
            prompt=(
                "Create a product video using the supplied "
                "reference material."
            ),
            duration=60,
            supporting_files=[
                "product_document.pdf",
            ],
        )

        result = PlannerAgent().create_plan(
            request,
        )

        assert any(
            "supporting assets" in note.lower()
            for note in result.generation_notes
        )

    def test_planner_is_llm_disabled_by_default(self):
        """
        PlannerAgent should use deterministic mode when no LLM is supplied.
        """

        agent = PlannerAgent()

        assert agent.is_llm_enabled() is False


# ===========================================================================
# ScriptAgent
# ===========================================================================


class TestScriptAgent:
    """
    Tests for ScriptAgent.
    """

    def test_create_script_returns_script(self):
        """
        ScriptAgent should convert a VideoPlan into Script.
        """

        result = ScriptAgent().create_script(
            create_video_plan(),
        )

        assert isinstance(
            result,
            Script,
        )

    def test_create_script_creates_expected_number_of_scenes(self):
        """
        ScriptAgent should create exactly plan.scene_count scenes.
        """

        plan = create_video_plan(
            scene_count=5,
        )

        result = ScriptAgent().create_script(
            plan,
        )

        assert len(
            result.scenes,
        ) == plan.scene_count

    def test_create_script_preserves_scene_ids(self):
        """
        Scene IDs should be sequential and stable.
        """

        result = ScriptAgent().create_script(
            create_video_plan(
                scene_count=5,
            ),
        )

        scene_ids = [
            scene.scene_id
            for scene in result.scenes
        ]

        assert scene_ids == [1, 2, 3, 4, 5]

    def test_create_script_preserves_total_duration(self):
        """
        Script scene durations must add up exactly to plan.duration.
        """

        plan = create_video_plan(
            duration=60,
            scene_count=5,
        )

        result = ScriptAgent().create_script(
            plan,
        )

        assert result.total_duration == plan.duration

    def test_create_script_assigns_positive_scene_durations(self):
        """
        Every generated scene must have a positive duration.
        """

        result = ScriptAgent().create_script(
            create_video_plan(),
        )

        assert all(
            scene.duration > 0
            for scene in result.scenes
        )

    def test_create_script_generates_non_empty_purpose(self):
        """
        Every ScriptScene should have a meaningful purpose.
        """

        result = ScriptAgent().create_script(
            create_video_plan(),
        )

        assert all(
            scene.purpose.strip()
            for scene in result.scenes
        )

    def test_create_script_generates_non_empty_narration(self):
        """
        Every ScriptScene should contain narration.
        """

        result = ScriptAgent().create_script(
            create_video_plan(),
        )

        assert all(
            scene.narration.strip()
            for scene in result.scenes
        )

    def test_create_script_first_scene_introduces_subject(self):
        """
        The first scene should establish the video context.
        """

        result = ScriptAgent().create_script(
            create_video_plan(),
        )

        assert (
            "introduce"
            in result.scenes[0].purpose.lower()
        )

    def test_create_script_last_scene_concludes_video(self):
        """
        The final scene should provide a conclusion.
        """

        result = ScriptAgent().create_script(
            create_video_plan(),
        )

        last_scene = result.scenes[-1]

        assert (
            "conclude"
            in last_scene.purpose.lower()
        )

    def test_allocate_scene_durations_exactly_matches_duration(self):
        """
        Duration allocation must preserve the exact target duration.
        """

        durations = ScriptAgent._allocate_scene_durations(
            duration=61,
            scene_count=5,
        )

        assert len(durations) == 5
        assert sum(durations) == 61
        assert all(
            duration >= 1
            for duration in durations
        )

    def test_allocate_scene_durations_rejects_invalid_scene_count(self):
        """
        Scene count must be greater than zero.
        """

        with pytest.raises(
            ValueError,
            match="scene_count must be greater than zero",
        ):
            ScriptAgent._allocate_scene_durations(
                duration=60,
                scene_count=0,
            )

    def test_allocate_scene_durations_rejects_too_many_scenes(
        self,
    ):
        """
        A duration smaller than the number of scenes is invalid.
        """

        with pytest.raises(
            ValueError,
            match="duration must be at least equal to scene_count",
        ):
            ScriptAgent._allocate_scene_durations(
                duration=2,
                scene_count=5,
            )

    def test_script_agent_is_llm_disabled_by_default(self):
        """
        ScriptAgent should use deterministic mode when no LLM is supplied.
        """

        agent = ScriptAgent()

        assert agent.is_llm_enabled() is False


# ===========================================================================
# StoryboardAgent
# ===========================================================================


class TestStoryboardAgent:
    """
    Tests for StoryboardAgent.
    """

    def test_create_storyboard_returns_storyboard(self):
        """
        StoryboardAgent should convert a Script into Storyboard.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        result = StoryboardAgent().create_storyboard(
            script,
        )

        assert isinstance(
            result,
            Storyboard,
        )

    def test_create_storyboard_creates_one_scene_per_script_scene(
        self,
    ):
        """
        Every ScriptScene should become exactly one storyboard Scene.
        """

        script = ScriptAgent().create_script(
            create_video_plan(
                scene_count=5,
            ),
        )

        result = StoryboardAgent().create_storyboard(
            script,
        )

        assert len(
            result.scenes,
        ) == len(
            script.scenes,
        )

    def test_create_storyboard_preserves_scene_ids(self):
        """
        Storyboard scene IDs should match Script scene IDs.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        script_ids = [
            scene.scene_id
            for scene in script.scenes
        ]

        storyboard_ids = [
            scene.scene_id
            for scene in storyboard.scenes
        ]

        assert storyboard_ids == script_ids

    def test_create_storyboard_preserves_scene_order(self):
        """
        Storyboard scenes should remain in script order.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        orders = [
            scene.order
            for scene in storyboard.scenes
        ]

        assert orders == sorted(orders)

    def test_create_storyboard_preserves_duration(self):
        """
        Storyboard duration must match the Script duration.
        """

        script = ScriptAgent().create_script(
            create_video_plan(
                duration=60,
            ),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert storyboard.total_duration == script.total_duration

    def test_create_storyboard_preserves_narration(self):
        """
        Storyboard narration should match Script narration.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        for script_scene, storyboard_scene in zip(
            script.scenes,
            storyboard.scenes,
        ):
            assert (
                storyboard_scene.narration
                == script_scene.narration
            )

    def test_create_storyboard_preserves_purpose(self):
        """
        Storyboard purpose should match Script purpose.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        for script_scene, storyboard_scene in zip(
            script.scenes,
            storyboard.scenes,
        ):
            assert (
                storyboard_scene.purpose
                == script_scene.purpose
            )

    def test_create_storyboard_generates_visual_description(self):
        """
        Every storyboard scene should have a visual description.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert all(
            scene.visual_description.strip()
            for scene in storyboard.scenes
        )

    def test_create_storyboard_generates_visual_prompt(self):
        """
        Every storyboard scene should have a visual-generation prompt.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert all(
            scene.visual_prompt.strip()
            for scene in storyboard.scenes
        )

    def test_create_storyboard_creates_asset_requirements(self):
        """
        Every storyboard scene should define asset requirements.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert all(
            len(scene.asset_requirements) >= 1
            for scene in storyboard.scenes
        )

    def test_create_storyboard_requires_audio_by_default(self):
        """
        Generated scenes should contain audio requirements.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert all(
            scene.audio_requirements.required
            for scene in storyboard.scenes
        )

    def test_create_storyboard_final_scene_has_no_transition(self):
        """
        The final scene should not require a transition.
        """

        script = ScriptAgent().create_script(
            create_video_plan(),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert storyboard.scenes[-1].transition is None

    def test_create_storyboard_first_scene_uses_fade_transition(
        self,
    ):
        """
        The first scene should use a fade transition.
        """

        script = ScriptAgent().create_script(
            create_video_plan(
                scene_count=3,
            ),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        assert storyboard.scenes[0].transition == "fade"

    def test_create_storyboard_middle_scenes_use_crossfade(
        self,
    ):
        """
        Middle scenes should use crossfade transitions.
        """

        script = ScriptAgent().create_script(
            create_video_plan(
                scene_count=4,
            ),
        )

        storyboard = StoryboardAgent().create_storyboard(
            script,
        )

        middle_scenes = storyboard.scenes[1:-1]

        assert all(
            scene.transition == "crossfade"
            for scene in middle_scenes
        )

    def test_storyboard_agent_is_llm_disabled_by_default(self):
        """
        StoryboardAgent should use deterministic mode when no LLM
        is supplied.
        """

        agent = StoryboardAgent()

        assert agent.is_llm_enabled() is False


# ===========================================================================
# Cross-agent contract tests
# ===========================================================================


def test_planner_script_storyboard_pipeline_preserves_duration():
    """
    Verify the complete agent chain preserves the requested duration.
    """

    request = create_video_request(
        duration=90,
    )

    planner = PlannerAgent()
    script_agent = ScriptAgent()
    storyboard_agent = StoryboardAgent()

    plan = planner.create_plan(
        request,
    )

    script = script_agent.create_script(
        plan,
    )

    storyboard = storyboard_agent.create_storyboard(
        script,
    )

    assert plan.duration == 90
    assert script.total_duration == 90
    assert storyboard.total_duration == 90


def test_planner_script_storyboard_pipeline_preserves_scene_count():
    """
    Verify the complete agent chain preserves the planned scene count.
    """

    request = create_video_request(
        duration=60,
    )

    plan = PlannerAgent().create_plan(
        request,
    )

    script = ScriptAgent().create_script(
        plan,
    )

    storyboard = StoryboardAgent().create_storyboard(
        script,
    )

    assert len(plan.content_requirements) > 0
    assert len(script.scenes) == plan.scene_count
    assert len(storyboard.scenes) == plan.scene_count


def test_planner_script_storyboard_pipeline_preserves_scene_identity():
    """
    Verify scene IDs remain stable across all three agents.
    """

    request = create_video_request()

    plan = PlannerAgent().create_plan(
        request,
    )

    script = ScriptAgent().create_script(
        plan,
    )

    storyboard = StoryboardAgent().create_storyboard(
        script,
    )

    script_ids = [
        scene.scene_id
        for scene in script.scenes
    ]

    storyboard_ids = [
        scene.scene_id
        for scene in storyboard.scenes
    ]

    assert script_ids == storyboard_ids