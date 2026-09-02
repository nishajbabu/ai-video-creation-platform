import pytest

from app.agents.storyboard import StoryboardAgent
from app.schemas.script import Script, ScriptScene
from app.schemas.storyboard import Storyboard


def create_script(
    *,
    scene_count: int = 3,
    duration: int = 30,
) -> Script:
    """
    Create a valid Script for StoryboardAgent tests.
    """

    scene_duration = duration // scene_count
    remainder = duration % scene_count

    scenes = []

    for index in range(1, scene_count + 1):
        current_duration = scene_duration

        if index <= remainder:
            current_duration += 1

        scenes.append(
            ScriptScene(
                scene_id=index,
                purpose=f"Scene {index} purpose",
                duration=current_duration,
                narration=f"Scene {index} narration.",
            )
        )

    return Script(
        scenes=scenes,
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_storyboard_agent_can_be_created_without_llm():
    agent = StoryboardAgent()

    assert agent.llm_service is None
    assert agent.is_llm_enabled() is False


def test_storyboard_agent_can_be_created_with_llm():
    class FakeLLMService:
        pass

    llm_service = FakeLLMService()

    agent = StoryboardAgent(
        llm_service=llm_service,
    )

    assert agent.llm_service is llm_service
    assert agent.is_llm_enabled() is True


# ---------------------------------------------------------------------------
# Deterministic storyboard generation
# ---------------------------------------------------------------------------

def test_storyboard_agent_creates_storyboard():
    agent = StoryboardAgent()

    script = create_script()

    storyboard = agent.create_storyboard(
        script,
    )

    assert isinstance(
        storyboard,
        Storyboard,
    )

    assert len(storyboard.scenes) == 3


def test_storyboard_preserves_scene_count():
    agent = StoryboardAgent()

    script = create_script(
        scene_count=5,
        duration=60,
    )

    storyboard = agent.create_storyboard(
        script,
    )

    assert storyboard.scene_count == 5


def test_storyboard_preserves_scene_ids():
    agent = StoryboardAgent()

    script = create_script(
        scene_count=4,
        duration=40,
    )

    storyboard = agent.create_storyboard(
        script,
    )

    scene_ids = [
        scene.scene_id
        for scene in storyboard.scenes
    ]

    assert scene_ids == [
        1,
        2,
        3,
        4,
    ]


def test_storyboard_preserves_scene_order():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(
            scene_count=4,
            duration=40,
        )
    )

    orders = [
        scene.order
        for scene in storyboard.scenes
    ]

    assert orders == [
        1,
        2,
        3,
        4,
    ]


def test_storyboard_preserves_scene_durations():
    agent = StoryboardAgent()

    script = create_script(
        scene_count=3,
        duration=31,
    )

    storyboard = agent.create_storyboard(
        script,
    )

    script_durations = [
        scene.duration
        for scene in script.scenes
    ]

    storyboard_durations = [
        scene.duration
        for scene in storyboard.scenes
    ]

    assert storyboard_durations == script_durations


def test_storyboard_preserves_purpose_and_narration():
    agent = StoryboardAgent()

    script = create_script(
        scene_count=3,
        duration=30,
    )

    storyboard = agent.create_storyboard(
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

        assert (
            storyboard_scene.narration
            == script_scene.narration
        )


# ---------------------------------------------------------------------------
# Visual generation
# ---------------------------------------------------------------------------

def test_storyboard_generates_visual_description():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(),
    )

    for scene in storyboard.scenes:
        assert scene.visual_description
        assert "scene purpose" in (
            scene.visual_description
        )


def test_storyboard_generates_visual_prompt():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(),
    )

    for scene in storyboard.scenes:
        assert scene.visual_prompt
        assert "visual" in (
            scene.visual_prompt.lower()
        )


def test_storyboard_uses_image_visual_type_by_default():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(),
    )

    for scene in storyboard.scenes:
        assert scene.visual_type == "image"


# ---------------------------------------------------------------------------
# Asset requirements
# ---------------------------------------------------------------------------

def test_storyboard_creates_asset_requirements():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(),
    )

    for scene in storyboard.scenes:
        assert len(
            scene.asset_requirements
        ) == 1

        requirement = (
            scene.asset_requirements[0]
        )

        assert requirement.asset_type == "image"
        assert requirement.description
        assert requirement.source == "ai_or_library"


# ---------------------------------------------------------------------------
# Audio requirements
# ---------------------------------------------------------------------------

def test_storyboard_creates_audio_requirements():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(),
    )

    for scene in storyboard.scenes:
        assert scene.audio_requirements.required is True
        assert (
            scene.audio_requirements.voice_style
            == "clear and professional"
        )
        assert (
            scene.audio_requirements.background_music
            is False
        )


# ---------------------------------------------------------------------------
# Transitions
# ---------------------------------------------------------------------------

def test_storyboard_first_scene_uses_fade():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(
            scene_count=3,
            duration=30,
        )
    )

    assert storyboard.scenes[0].transition == "fade"


def test_storyboard_middle_scene_uses_crossfade():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(
            scene_count=3,
            duration=30,
        )
    )

    assert (
        storyboard.scenes[1].transition
        == "crossfade"
    )


def test_storyboard_last_scene_has_no_transition():
    agent = StoryboardAgent()

    storyboard = agent.create_storyboard(
        create_script(
            scene_count=3,
            duration=30,
        )
    )

    assert storyboard.scenes[-1].transition is None


# ---------------------------------------------------------------------------
# Duration and scene count properties
# ---------------------------------------------------------------------------

def test_storyboard_total_duration_matches_script():
    agent = StoryboardAgent()

    script = create_script(
        scene_count=5,
        duration=60,
    )

    storyboard = agent.create_storyboard(
        script,
    )

    assert (
        storyboard.total_duration
        == script.total_duration
    )


def test_storyboard_scene_count_matches_script():
    agent = StoryboardAgent()

    script = create_script(
        scene_count=6,
        duration=60,
    )

    storyboard = agent.create_storyboard(
        script,
    )

    assert (
        storyboard.scene_count
        == len(script.scenes)
    )


# ---------------------------------------------------------------------------
# Helper methods
# ---------------------------------------------------------------------------

def test_visual_description_helper():
    description = (
        StoryboardAgent._build_visual_description(
            "Introduce the product"
        )
    )

    assert "Introduce the product" in description


def test_visual_prompt_helper():
    prompt = StoryboardAgent._build_visual_prompt(
        "Explain the product",
        "Our product improves productivity.",
    )

    assert "Explain the product" in prompt
    assert (
        "Our product improves productivity."
        in prompt
    )


def test_asset_requirement_helper():
    requirement = (
        StoryboardAgent._build_default_asset_requirement(
            "Show the product"
        )
    )

    assert requirement.asset_type == "image"
    assert requirement.source == "ai_or_library"
    assert "Show the product" in requirement.description


@pytest.mark.parametrize(
    "scene_id, scene_count, expected",
    [
        (1, 3, "fade"),
        (2, 3, "crossfade"),
        (3, 3, None),
        (1, 1, None),
    ],
)
def test_transition_generation(
    scene_id,
    scene_count,
    expected,
):
    transition = StoryboardAgent._build_transition(
        scene_id,
        scene_count,
    )

    assert transition == expected


# ---------------------------------------------------------------------------
# LLM-backed generation
# ---------------------------------------------------------------------------

def test_storyboard_agent_uses_llm_when_configured():
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
                        "order": 1,
                        "duration": 30,
                        "purpose": "Introduce the product.",
                        "narration": "Welcome to our product.",
                        "visual_description": (
                            "A professional product hero shot."
                        ),
                        "visual_prompt": (
                            "Create a cinematic product hero shot."
                        ),
                        "visual_type": "image",
                        "asset_requirements": [],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": "professional",
                            "background_music": False,
                        },
                        "transition": None,
                        "status": "planned",
                    },
                ],
            }

    llm_service = FakeLLMService()

    agent = StoryboardAgent(
        llm_service=llm_service,
    )

    script = create_script(
        scene_count=1,
        duration=30,
    )

    storyboard = agent.create_storyboard(
        script,
    )

    assert isinstance(
        storyboard,
        Storyboard,
    )

    assert len(
        storyboard.scenes
    ) == 1

    assert (
        storyboard.scenes[0].scene_id
        == 1
    )

    assert (
        storyboard.scenes[0].duration
        == 30
    )

    assert (
        llm_service.received_prompt
        is not None
    )

    assert (
        llm_service.received_schema
        is not None
    )


def test_storyboard_agent_validates_llm_result():
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
                        "order": 1,
                        "duration": 20,
                        "purpose": "Introduce the topic.",
                        "narration": "Welcome.",
                        "visual_description": (
                            "A professional introduction."
                        ),
                        "visual_prompt": (
                            "Create a professional introduction."
                        ),
                        "visual_type": "image",
                        "asset_requirements": [],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": "clear",
                            "background_music": False,
                        },
                        "transition": None,
                        "status": "planned",
                    },
                    {
                        "scene_id": 2,
                        "order": 2,
                        "duration": 20,
                        "purpose": "Explain the topic.",
                        "narration": "Here is the explanation.",
                        "visual_description": (
                            "An explanatory visual."
                        ),
                        "visual_prompt": (
                            "Create an explanatory visual."
                        ),
                        "visual_type": "image",
                        "asset_requirements": [],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": "clear",
                            "background_music": False,
                        },
                        "transition": "crossfade",
                        "status": "planned",
                    },
                ],
            }

    agent = StoryboardAgent(
        llm_service=FakeLLMService(),
    )

    storyboard = agent.create_storyboard(
        create_script(
            scene_count=2,
            duration=40,
        )
    )

    assert storyboard.scene_count == 2
    assert storyboard.total_duration == 40
    assert storyboard.scenes[0].order == 1
    assert storyboard.scenes[1].order == 2