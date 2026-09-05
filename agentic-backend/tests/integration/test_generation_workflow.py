import pytest

from app.agents.orchestrator import Orchestrator
from app.schemas.requests import VideoRequest
from app.services.generation_service import GenerationService
from app.state.workflow_state import (
    WORKFLOW_COMPLETED,
    WORKFLOW_FAILED,
)


def create_video_request() -> VideoRequest:
    """
    Create a valid request for end-to-end workflow tests.
    """

    return VideoRequest(
        prompt="Create a professional AI product introduction video.",
        duration=60,
        style="professional",
        target_audience="Potential customers",
        tone="confident",
    )


# ---------------------------------------------------------------------------
# Complete generation workflow
# ---------------------------------------------------------------------------

def test_generation_workflow_runs_from_request_to_storyboard():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    request = create_video_request()

    result = service.start_generation(
        request,
    )

    assert result["status"] == "completed"

    assert result["plan"] is not None
    assert result["script"] is not None
    assert result["storyboard"] is not None


def test_generation_workflow_produces_matching_scene_counts():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    result = service.start_generation(
        create_video_request(),
    )

    plan = result["plan"]
    script = result["script"]
    storyboard = result["storyboard"]

    assert (
        len(script["scenes"])
        == plan["scene_count"]
    )

    assert (
        len(storyboard["scenes"])
        == plan["scene_count"]
    )


def test_generation_workflow_preserves_requested_duration():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    result = service.start_generation(
        create_video_request(),
    )

    assert result["plan"]["duration"] == 60

    script_duration = sum(
        scene["duration"]
        for scene in result["script"]["scenes"]
    )

    storyboard_duration = sum(
        scene["duration"]
        for scene in result["storyboard"]["scenes"]
    )

    assert script_duration == 60
    assert storyboard_duration == 60


# ---------------------------------------------------------------------------
# Workflow state
# ---------------------------------------------------------------------------

def test_generation_workflow_updates_workflow_state():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    service.start_generation(
        create_video_request(),
    )

    state = orchestrator.get_workflow_state()

    assert state is not None
    assert state.status == WORKFLOW_COMPLETED
    assert state.is_completed() is True
    assert state.error is None

    assert state.plan is not None
    assert state.script is not None
    assert state.storyboard is not None


def test_generation_workflow_state_contains_all_outputs():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    service.start_generation(
        create_video_request(),
    )

    state = orchestrator.get_workflow_state()

    assert state.plan is not None
    assert state.script is not None
    assert state.storyboard is not None

    assert (
        state.script.total_duration
        == state.plan.duration
    )

    assert (
        state.storyboard.total_duration
        == state.plan.duration
    )


# ---------------------------------------------------------------------------
# Data flow between stages
# ---------------------------------------------------------------------------

def test_generation_workflow_preserves_scene_ids():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    result = service.start_generation(
        create_video_request(),
    )

    script_ids = [
        scene["scene_id"]
        for scene in result["script"]["scenes"]
    ]

    storyboard_ids = [
        scene["scene_id"]
        for scene in result["storyboard"]["scenes"]
    ]

    assert script_ids == storyboard_ids


def test_generation_workflow_preserves_narration():
    orchestrator = Orchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    result = service.start_generation(
        create_video_request(),
    )

    for script_scene, storyboard_scene in zip(
        result["script"]["scenes"],
        result["storyboard"]["scenes"],
    ):
        assert (
            storyboard_scene["narration"]
            == script_scene["narration"]
        )

        assert (
            storyboard_scene["purpose"]
            == script_scene["purpose"]
        )


# ---------------------------------------------------------------------------
# Failure workflow
# ---------------------------------------------------------------------------

def test_generation_workflow_records_planner_failure():
    class FailingPlanner:
        def create_plan(self, request):
            raise RuntimeError(
                "Planner integration failure."
            )

    orchestrator = Orchestrator(
        planner=FailingPlanner(),
    )

    service = GenerationService(
        orchestrator=orchestrator,
    )

    with pytest.raises(
        RuntimeError,
        match="Planner integration failure.",
    ):
        service.start_generation(
            create_video_request(),
        )

    state = orchestrator.get_workflow_state()

    assert state is not None
    assert state.status == WORKFLOW_FAILED
    assert state.is_failed() is True
    assert (
        state.error
        == "Planner integration failure."
    )


def test_generation_workflow_records_script_failure():
    class WorkingPlanner:
        def create_plan(self, request):
            from app.schemas.plan import VideoPlan

            return VideoPlan(
                objective=(
                    "Create a professional AI product video."
                ),
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=2,
            )

    class FailingScriptAgent:
        def create_script(self, plan):
            raise RuntimeError(
                "Script integration failure."
            )

    orchestrator = Orchestrator(
        planner=WorkingPlanner(),
        script_agent=FailingScriptAgent(),
    )

    service = GenerationService(
        orchestrator=orchestrator,
    )

    with pytest.raises(
        RuntimeError,
        match="Script integration failure.",
    ):
        service.start_generation(
            create_video_request(),
        )

    state = orchestrator.get_workflow_state()

    assert state is not None
    assert state.status == WORKFLOW_FAILED
    assert (
        state.error
        == "Script integration failure."
    )


def test_generation_workflow_records_storyboard_failure():
    class WorkingPlanner:
        def create_plan(self, request):
            from app.schemas.plan import VideoPlan

            return VideoPlan(
                objective=(
                    "Create a professional AI product video."
                ),
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=2,
            )

    class WorkingScriptAgent:
        def create_script(self, plan):
            from app.schemas.script import Script

            return Script(
                scenes=[
                    {
                        "scene_id": 1,
                        "purpose": "Introduce the product.",
                        "duration": 30,
                        "narration": "Welcome.",
                    },
                    {
                        "scene_id": 2,
                        "purpose": "Explain the product.",
                        "duration": 30,
                        "narration": "Here is how it works.",
                    },
                ]
            )

    class FailingStoryboardAgent:
        def create_storyboard(self, script):
            raise RuntimeError(
                "Storyboard integration failure."
            )

    orchestrator = Orchestrator(
        planner=WorkingPlanner(),
        script_agent=WorkingScriptAgent(),
        storyboard_agent=FailingStoryboardAgent(),
    )

    service = GenerationService(
        orchestrator=orchestrator,
    )

    with pytest.raises(
        RuntimeError,
        match="Storyboard integration failure.",
    ):
        service.start_generation(
            create_video_request(),
        )

    state = orchestrator.get_workflow_state()

    assert state is not None
    assert state.status == WORKFLOW_FAILED
    assert (
        state.error
        == "Storyboard integration failure."
    )