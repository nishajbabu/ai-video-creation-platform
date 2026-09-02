import pytest

from app.agents.script import ScriptAgent
from app.schemas.plan import VideoPlan
from app.schemas.script import Script


def create_video_plan(
    *,
    duration: int = 60,
    scene_count: int = 5,
) -> VideoPlan:
    """
    Create a valid VideoPlan for ScriptAgent tests.
    """

    return VideoPlan(
        objective="Create a professional AI product introduction.",
        target_audience="Potential customers",
        tone="confident",
        style="professional",
        duration=duration,
        scene_count=scene_count,
        content_requirements=[
            "Introduce the product.",
            "Explain the key features.",
            "Explain the customer benefits.",
            "Present the main value proposition.",
        ],
        generation_notes=[
            "Use a confident tone.",
            "Keep the explanation concise.",
        ],
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_script_agent_can_be_created_without_llm():
    agent = ScriptAgent()

    assert agent.llm_service is None
    assert agent.is_llm_enabled() is False


def test_script_agent_can_be_created_with_llm():
    class FakeLLMService:
        pass

    llm_service = FakeLLMService()

    agent = ScriptAgent(
        llm_service=llm_service,
    )

    assert agent.llm_service is llm_service
    assert agent.is_llm_enabled() is True


# ---------------------------------------------------------------------------
# Deterministic script generation
# ---------------------------------------------------------------------------

def test_script_agent_creates_script():
    agent = ScriptAgent()

    plan = create_video_plan()

    script = agent.create_script(
        plan,
    )

    assert isinstance(
        script,
        Script,
    )

    assert len(script.scenes) == 5


def test_script_agent_creates_unique_scene_ids():
    agent = ScriptAgent()

    script = agent.create_script(
        create_video_plan(
            scene_count=5,
        )
    )

    scene_ids = [
        scene.scene_id
        for scene in script.scenes
    ]

    assert scene_ids == [
        1,
        2,
        3,
        4,
        5,
    ]

    assert len(scene_ids) == len(
        set(scene_ids)
    )


def test_script_agent_preserves_total_duration():
    agent = ScriptAgent()

    plan = create_video_plan(
        duration=60,
        scene_count=5,
    )

    script = agent.create_script(
        plan,
    )

    assert script.total_duration == 60


def test_script_agent_creates_valid_scene_content():
    agent = ScriptAgent()

    script = agent.create_script(
        create_video_plan(),
    )

    for scene in script.scenes:
        assert scene.scene_id >= 1
        assert scene.purpose
        assert scene.duration >= 1
        assert scene.narration


def test_script_agent_first_scene_introduces_topic():
    agent = ScriptAgent()

    plan = create_video_plan()

    script = agent.create_script(
        plan,
    )

    first_scene = script.scenes[0]

    assert "Introduce" in first_scene.purpose
    assert "Welcome" in first_scene.narration


def test_script_agent_last_scene_concludes_video():
    agent = ScriptAgent()

    script = agent.create_script(
        create_video_plan(
            scene_count=5,
        )
    )

    last_scene = script.scenes[-1]

    assert "Conclude" in last_scene.purpose
    assert "Thank you" in last_scene.narration


# ---------------------------------------------------------------------------
# Duration allocation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "duration, scene_count",
    [
        (10, 1),
        (30, 3),
        (60, 5),
        (61, 5),
        (100, 7),
        (120, 8),
    ],
)
def test_script_agent_allocates_scene_durations(
    duration,
    scene_count,
):
    durations = ScriptAgent._allocate_scene_durations(
        duration=duration,
        scene_count=scene_count,
    )

    assert len(durations) == scene_count
    assert sum(durations) == duration

    assert all(
        scene_duration >= 1
        for scene_duration in durations
    )


def test_script_agent_distributes_remainder():
    durations = ScriptAgent._allocate_scene_durations(
        duration=11,
        scene_count=3,
    )

    assert durations == [
        4,
        4,
        3,
    ]

    assert sum(durations) == 11


def test_script_agent_rejects_invalid_scene_count():
    with pytest.raises(
        ValueError,
        match="scene_count must be greater than zero",
    ):
        ScriptAgent._allocate_scene_durations(
            duration=60,
            scene_count=0,
        )


def test_script_agent_rejects_duration_smaller_than_scene_count():
    with pytest.raises(
        ValueError,
        match="duration must be at least equal to scene_count",
    ):
        ScriptAgent._allocate_scene_durations(
            duration=2,
            scene_count=5,
        )


# ---------------------------------------------------------------------------
# Content requirements
# ---------------------------------------------------------------------------

def test_script_agent_uses_content_requirements():
    agent = ScriptAgent()

    plan = create_video_plan(
        scene_count=5,
    )

    script = agent.create_script(
        plan,
    )

    middle_scenes = script.scenes[1:-1]

    assert any(
        "Explain the key features."
        in scene.purpose
        for scene in middle_scenes
    )


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def test_script_agent_builds_llm_prompt():
    agent = ScriptAgent()

    plan = create_video_plan()

    prompt = agent._build_script_prompt(
        plan,
    )

    assert "Create a complete scene-by-scene video script" in prompt
    assert plan.objective in prompt
    assert "Potential customers" in prompt
    assert "confident" in prompt
    assert "professional" in prompt
    assert "60 seconds" in prompt
    assert "5" in prompt
    assert "Introduce the product." in prompt
    assert "Use a confident tone." in prompt


def test_script_agent_prompt_handles_empty_requirements():
    agent = ScriptAgent()

    plan = VideoPlan(
        objective="Create a professional product introduction.",
        target_audience="Customers",
        tone="professional",
        style="modern",
        duration=30,
        scene_count=3,
        content_requirements=[],
        generation_notes=[],
    )

    prompt = agent._build_script_prompt(
        plan,
    )

    assert "No additional content requirements." in prompt
    assert "No additional generation notes." in prompt


# ---------------------------------------------------------------------------
# LLM-backed generation
# ---------------------------------------------------------------------------

def test_script_agent_uses_llm_when_configured():
    class FakeLLMService:
        def __init__(self):
            self.received_prompt = None
            self.received_schema = None

        def generate_structured(
            self,
            *,
            prompt,
            response_schema,
        ):
            self.received_prompt = prompt
            self.received_schema = response_schema

            return {
                "scenes": [
                    {
                        "scene_id": 1,
                        "purpose": "Introduce the product.",
                        "duration": 30,
                        "narration": (
                            "Welcome to our AI product."
                        ),
                    },
                    {
                        "scene_id": 2,
                        "purpose": "Explain the product benefits.",
                        "duration": 30,
                        "narration": (
                            "Our product helps teams work "
                            "more efficiently."
                        ),
                    },
                ],
            }

    llm_service = FakeLLMService()

    agent = ScriptAgent(
        llm_service=llm_service,
    )

    plan = create_video_plan(
        duration=60,
        scene_count=2,
    )

    script = agent.create_script(
        plan,
    )

    assert isinstance(
        script,
        Script,
    )

    assert len(script.scenes) == 2
    assert script.total_duration == 60

    assert (
        llm_service.received_prompt
        is not None
    )

    assert (
        llm_service.received_schema
        is not None
    )


def test_script_agent_validates_llm_result():
    class FakeLLMService:
        def generate_structured(
            self,
            *,
            prompt,
            response_schema,
        ):
            return {
                "scenes": [
                    {
                        "scene_id": 1,
                        "purpose": "Introduce the topic.",
                        "duration": 20,
                        "narration": "Welcome to the video.",
                    },
                    {
                        "scene_id": 2,
                        "purpose": "Explain the topic.",
                        "duration": 20,
                        "narration": "Here is the explanation.",
                    },
                ],
            }

    agent = ScriptAgent(
        llm_service=FakeLLMService(),
    )

    script = agent.create_script(
        create_video_plan(
            duration=40,
            scene_count=2,
        )
    )

    assert script.total_duration == 40
    assert script.scenes[0].scene_id == 1
    assert script.scenes[1].scene_id == 2