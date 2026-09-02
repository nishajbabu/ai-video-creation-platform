import pytest

from app.agents.planner import PlannerAgent
from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest


def create_video_request(
    *,
    duration: int = 60,
    style: str = "professional",
    target_audience: str = "Potential customers",
    tone: str = "confident",
) -> VideoRequest:
    """
    Create a valid VideoRequest for PlannerAgent tests.
    """

    return VideoRequest(
        prompt="Create a professional AI product introduction video.",
        duration=duration,
        style=style,
        target_audience=target_audience,
        tone=tone,
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_planner_can_be_created_without_llm():
    planner = PlannerAgent()

    assert planner.llm_service is None
    assert planner.is_llm_enabled() is False


def test_planner_can_be_created_with_llm():
    class FakeLLMService:
        pass

    llm_service = FakeLLMService()

    planner = PlannerAgent(
        llm_service=llm_service,
    )

    assert planner.llm_service is llm_service
    assert planner.is_llm_enabled() is True


# ---------------------------------------------------------------------------
# Deterministic planning
# ---------------------------------------------------------------------------

def test_planner_creates_default_plan():
    planner = PlannerAgent()

    request = create_video_request()

    plan = planner.create_plan(
        request,
    )

    assert isinstance(
        plan,
        VideoPlan,
    )

    assert plan.objective
    assert plan.target_audience == "Potential customers"
    assert plan.tone == "confident"
    assert plan.style == "professional"
    assert plan.duration == 60
    assert plan.scene_count == 5


def test_planner_generates_content_requirements():
    planner = PlannerAgent()

    request = create_video_request()

    plan = planner.create_plan(
        request,
    )

    assert len(
        plan.content_requirements
    ) == 4

    assert any(
        "Introduce" in requirement
        for requirement in plan.content_requirements
    )

    assert any(
        "features" in requirement
        or "benefits" in requirement
        for requirement in plan.content_requirements
    )


def test_planner_generates_generation_notes():
    planner = PlannerAgent()

    request = create_video_request(
        duration=60,
        tone="confident",
    )

    plan = planner.create_plan(
        request,
    )

    assert len(
        plan.generation_notes
    ) >= 2

    assert any(
        "confident" in note
        for note in plan.generation_notes
    )

    assert any(
        "60 seconds" in note
        for note in plan.generation_notes
    )


def test_planner_mentions_supporting_files():
    planner = PlannerAgent()

    request = VideoRequest(
        prompt="Create a product video.",
        duration=60,
        style="professional",
        target_audience="Customers",
        tone="confident",
        supporting_files=[
            "logo.png",
            "product.pdf",
        ],
    )

    plan = planner.create_plan(
        request,
    )

    assert any(
        "supporting assets" in note
        for note in plan.generation_notes
    )


# ---------------------------------------------------------------------------
# Scene estimation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "duration, expected_scene_count",
    [
        (10, 3),
        (30, 3),
        (31, 5),
        (60, 5),
        (61, 8),
        (120, 8),
        (121, 10),
        (150, 10),
        (300, 20),
    ],
)
def test_planner_estimates_scene_count(
    duration,
    expected_scene_count,
):
    planner = PlannerAgent()

    assert (
        planner._estimate_scene_count(
            duration,
        )
        == expected_scene_count
    )


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

def test_planner_uses_default_style():
    planner = PlannerAgent()

    request = create_video_request(
        style="",
    )

    plan = planner.create_plan(
        request,
    )

    assert plan.style == "professional"


def test_planner_uses_default_tone():
    planner = PlannerAgent()

    request = create_video_request(
        tone="",
    )

    plan = planner.create_plan(
        request,
    )

    assert plan.tone == "professional"


def test_planner_uses_default_audience():
    planner = PlannerAgent()

    request = create_video_request(
        target_audience="",
    )

    plan = planner.create_plan(
        request,
    )

    assert plan.target_audience == "General audience"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def test_planner_builds_prompt():
    planner = PlannerAgent()

    request = create_video_request()

    prompt = planner._build_planning_prompt(
        request,
    )

    assert "Create a structured production plan" in prompt
    assert request.prompt in prompt
    assert "60 seconds" in prompt
    assert "professional" in prompt
    assert "Potential customers" in prompt
    assert "confident" in prompt
    assert "Supporting files: none" in prompt


def test_planner_prompt_includes_supporting_files():
    planner = PlannerAgent()

    request = VideoRequest(
        prompt="Create a product video.",
        duration=45,
        style="modern",
        target_audience="Developers",
        tone="technical",
        supporting_files=[
            "logo.png",
            "demo.mp4",
        ],
    )

    prompt = planner._build_planning_prompt(
        request,
    )

    assert "logo.png" in prompt
    assert "demo.mp4" in prompt


# ---------------------------------------------------------------------------
# LLM-backed planning
# ---------------------------------------------------------------------------

def test_planner_uses_llm_when_configured():
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
                "objective": "Create an AI product video.",
                "target_audience": "Potential customers",
                "tone": "confident",
                "style": "professional",
                "duration": 60,
                "scene_count": 5,
                "content_requirements": [
                    "Introduce the product.",
                    "Explain the benefits.",
                ],
                "generation_notes": [
                    "Use a confident tone.",
                ],
            }

    llm_service = FakeLLMService()

    planner = PlannerAgent(
        llm_service=llm_service,
    )

    request = create_video_request()

    plan = planner.create_plan(
        request,
    )

    assert isinstance(
        plan,
        VideoPlan,
    )

    assert (
        plan.objective
        == "Create an AI product video."
    )

    assert (
        plan.scene_count
        == 5
    )

    assert llm_service.received_prompt is not None
    assert llm_service.received_schema is not None


def test_planner_validates_llm_result():
    class FakeLLMService:
        def generate_structured(
            self,
            *,
            prompt,
            response_schema,
        ):
            return {
                "objective": "AI product video",
                "target_audience": "Customers",
                "tone": "professional",
                "style": "modern",
                "duration": 30,
                "scene_count": 3,
                "content_requirements": [
                    "Introduce the product.",
                ],
                "generation_notes": [
                    "Keep the video concise.",
                ],
            }

    planner = PlannerAgent(
        llm_service=FakeLLMService(),
    )

    plan = planner.create_plan(
        create_video_request(
            duration=30,
        ),
    )

    assert plan.duration == 30
    assert plan.scene_count == 3
    assert plan.target_audience == "Customers"