import pytest
from pydantic import ValidationError

from app.schemas import (
    APIResponse,
    AssetRequirement,
    AudioRequirement,
    ErrorDetail,
    ErrorResponse,
    Scene,
    Script,
    ScriptScene,
    Storyboard,
    VideoPlan,
    VideoRequest,
)


# ---------------------------------------------------------------------------
# VideoRequest tests
# ---------------------------------------------------------------------------

def test_video_request_valid():
    request = VideoRequest(
        prompt="Create a professional product introduction video.",
        duration=60,
        style="professional",
        target_audience="Potential customers",
        tone="confident",
    )

    assert request.prompt == (
        "Create a professional product introduction video."
    )
    assert request.duration == 60
    assert request.style == "professional"


def test_video_request_rejects_short_prompt():
    with pytest.raises(ValidationError):
        VideoRequest(
            prompt="hello",
            duration=60,
        )


def test_video_request_rejects_invalid_duration():
    with pytest.raises(ValidationError):
        VideoRequest(
            prompt="Create a professional product introduction video.",
            duration=700,
        )


def test_video_request_supporting_files_default_to_empty_list():
    request = VideoRequest(
        prompt="Create a professional product introduction video.",
        duration=60,
    )

    assert request.supporting_files == []


# ---------------------------------------------------------------------------
# VideoPlan tests
# ---------------------------------------------------------------------------

def test_video_plan_valid():
    plan = VideoPlan(
        objective="Introduce the AI chatbot to potential customers.",
        target_audience="Potential customers",
        tone="professional",
        style="modern",
        duration=60,
        scene_count=5,
        content_requirements=[
            "Customer problem",
            "AI solution",
            "Key features",
        ],
        generation_notes=[
            "Keep the explanation concise",
        ],
    )

    assert plan.duration == 60
    assert plan.scene_count == 5
    assert len(plan.content_requirements) == 3


def test_video_plan_rejects_invalid_scene_count():
    with pytest.raises(ValidationError):
        VideoPlan(
            objective="Introduce the AI chatbot to potential customers.",
            duration=60,
            scene_count=0,
        )


def test_video_plan_rejects_blank_objective():
    with pytest.raises(ValidationError):
        VideoPlan(
            objective="   ",
            duration=60,
            scene_count=5,
        )


# ---------------------------------------------------------------------------
# Script tests
# ---------------------------------------------------------------------------

def create_script_scene(
    scene_id: int,
    duration: int,
    purpose: str = "Introduce the product",
    narration: str = "Welcome to our AI product.",
) -> ScriptScene:
    return ScriptScene(
        scene_id=scene_id,
        purpose=purpose,
        duration=duration,
        narration=narration,
    )


def test_script_valid():
    script = Script(
        scenes=[
            create_script_scene(1, 10),
            create_script_scene(
                2,
                15,
                purpose="Explain the solution",
                narration="Our AI solution automates customer support.",
            ),
        ]
    )

    assert len(script.scenes) == 2
    assert script.total_duration == 25


def test_script_rejects_duplicate_scene_ids():
    with pytest.raises(ValidationError):
        Script(
            scenes=[
                create_script_scene(1, 10),
                create_script_scene(1, 15),
            ]
        )


def test_script_rejects_blank_narration():
    with pytest.raises(ValidationError):
        Script(
            scenes=[
                create_script_scene(
                    1,
                    10,
                    narration="   ",
                )
            ]
        )


# ---------------------------------------------------------------------------
# Scene tests
# ---------------------------------------------------------------------------

def create_scene(
    scene_id: int,
    order: int,
    duration: int = 10,
) -> Scene:
    return Scene(
        scene_id=scene_id,
        order=order,
        duration=duration,
        purpose="Introduce the product",
        narration="Welcome to our AI product.",
        visual_description="A modern AI product interface.",
        visual_prompt=(
            "Modern professional AI SaaS interface, "
            "clean product presentation."
        ),
        visual_type="image",
    )


def test_scene_valid():
    scene = create_scene(1, 1)

    assert scene.scene_id == 1
    assert scene.order == 1
    assert scene.duration == 10
    assert scene.status == "planned"
    assert scene.visual_type == "image"


def test_scene_supports_asset_requirements():
    scene = create_scene(1, 1)

    scene.asset_requirements = [
        AssetRequirement(
            asset_type="logo",
            description="Company logo",
            source="user_upload",
        )
    ]

    assert len(scene.asset_requirements) == 1
    assert scene.asset_requirements[0].asset_type == "logo"


def test_scene_supports_audio_requirements():
    scene = create_scene(1, 1)

    scene.audio_requirements = AudioRequirement(
        required=True,
        voice_style="Professional male voice",
        background_music=True,
    )

    assert scene.audio_requirements.required is True
    assert scene.audio_requirements.background_music is True


def test_scene_rejects_invalid_visual_type():
    with pytest.raises(ValidationError):
        Scene(
            scene_id=1,
            order=1,
            duration=10,
            purpose="Introduce the product",
            narration="Welcome to our product.",
            visual_description="Product interface.",
            visual_prompt="Modern product interface.",
            visual_type="banana",
        )


# ---------------------------------------------------------------------------
# Storyboard tests
# ---------------------------------------------------------------------------

def test_storyboard_valid():
    storyboard = Storyboard(
        scenes=[
            create_scene(1, 1, 10),
            create_scene(2, 2, 15),
            create_scene(3, 3, 20),
        ]
    )

    assert storyboard.scene_count == 3
    assert storyboard.total_duration == 45


def test_storyboard_rejects_duplicate_scene_ids():
    with pytest.raises(ValidationError):
        Storyboard(
            scenes=[
                create_scene(1, 1),
                create_scene(1, 2),
            ]
        )


def test_storyboard_rejects_duplicate_order_values():
    with pytest.raises(ValidationError):
        Storyboard(
            scenes=[
                create_scene(1, 1),
                create_scene(2, 1),
            ]
        )


def test_storyboard_rejects_unsorted_scenes():
    with pytest.raises(ValidationError):
        Storyboard(
            scenes=[
                create_scene(2, 2),
                create_scene(1, 1),
            ]
        )


# ---------------------------------------------------------------------------
# API response tests
# ---------------------------------------------------------------------------

def test_api_response_success():
    response = APIResponse(
        success=True,
        message="Video generation started.",
        data={
            "video_id": "video_123",
            "status": "queued",
        },
    )

    assert response.success is True
    assert response.data["video_id"] == "video_123"
    assert response.error is None


def test_api_response_failure():
    response = APIResponse(
        success=False,
        message="Video generation failed.",
        error="LLM provider unavailable.",
    )

    assert response.success is False
    assert response.data is None
    assert response.error == "LLM provider unavailable."


# ---------------------------------------------------------------------------
# Error response tests
# ---------------------------------------------------------------------------

def test_error_detail():
    error = ErrorDetail(
        code="INVALID_DURATION",
        message="Duration must be between 10 and 600 seconds.",
        field="duration",
    )

    assert error.code == "INVALID_DURATION"
    assert error.field == "duration"


def test_error_response():
    response = ErrorResponse(
        message="Invalid video request.",
        errors=[
            ErrorDetail(
                code="INVALID_DURATION",
                message="Duration must be between 10 and 600 seconds.",
                field="duration",
            )
        ],
    )

    assert response.success is False
    assert len(response.errors) == 1
    assert response.errors[0].code == "INVALID_DURATION"