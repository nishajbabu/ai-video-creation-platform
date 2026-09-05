from datetime import datetime

from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest
from app.schemas.script import Script
from app.schemas.storyboard import Storyboard
from app.state.workflow_state import (
    WORKFLOW_COMPLETED,
    WORKFLOW_FAILED,
    WORKFLOW_PENDING,
    WORKFLOW_PLANNING,
    WORKFLOW_SCRIPTING,
    WORKFLOW_STORYBOARDING,
    WorkflowState,
)


def create_request() -> VideoRequest:
    return VideoRequest(
        prompt="Create a professional AI product video.",
        duration=60,
        style="professional",
        target_audience="Customers",
        tone="confident",
    )


def create_plan() -> VideoPlan:
    return VideoPlan(
        objective="Create a professional AI product video.",
        target_audience="Customers",
        tone="confident",
        style="professional",
        duration=60,
        scene_count=2,
    )


def create_script() -> Script:
    return Script(
        scenes=[
            {
                "scene_id": 1,
                "purpose": "Introduce the product.",
                "duration": 30,
                "narration": "Welcome to the product.",
            },
            {
                "scene_id": 2,
                "purpose": "Explain the product.",
                "duration": 30,
                "narration": "Here is how it works.",
            },
        ]
    )


def create_storyboard() -> Storyboard:
    return Storyboard(
        scenes=[
            {
                "scene_id": 1,
                "order": 1,
                "duration": 30,
                "purpose": "Introduce the product.",
                "narration": "Welcome to the product.",
                "visual_description": "Product introduction.",
                "visual_prompt": "Create a product introduction.",
            },
            {
                "scene_id": 2,
                "order": 2,
                "duration": 30,
                "purpose": "Explain the product.",
                "narration": "Here is how it works.",
                "visual_description": "Product explanation.",
                "visual_prompt": "Create a product explanation.",
            },
        ]
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_workflow_state_starts_pending():
    state = WorkflowState(
        workflow_id="workflow_001",
        request=create_request(),
    )

    assert state.workflow_id == "workflow_001"
    assert state.status == WORKFLOW_PENDING
    assert state.current_stage is None
    assert state.plan is None
    assert state.script is None
    assert state.storyboard is None
    assert state.error is None


def test_workflow_state_creates_timestamps():
    state = WorkflowState(
        workflow_id="workflow_002",
        request=create_request(),
    )

    assert isinstance(
        state.created_at,
        datetime,
    )

    assert isinstance(
        state.updated_at,
        datetime,
    )


# ---------------------------------------------------------------------------
# Planning state
# ---------------------------------------------------------------------------

def test_start_planning_updates_state():
    state = WorkflowState(
        workflow_id="workflow_003",
        request=create_request(),
    )

    state.start_planning()

    assert state.status == WORKFLOW_PLANNING
    assert state.current_stage == "planner"
    assert state.error is None


def test_set_plan_stores_plan():
    state = WorkflowState(
        workflow_id="workflow_004",
        request=create_request(),
    )

    plan = create_plan()

    state.set_plan(plan)

    assert state.plan is plan


# ---------------------------------------------------------------------------
# Script state
# ---------------------------------------------------------------------------

def test_start_scripting_updates_state():
    state = WorkflowState(
        workflow_id="workflow_005",
        request=create_request(),
    )

    state.start_scripting()

    assert state.status == WORKFLOW_SCRIPTING
    assert state.current_stage == "script"


def test_set_script_stores_script():
    state = WorkflowState(
        workflow_id="workflow_006",
        request=create_request(),
    )

    script = create_script()

    state.set_script(script)

    assert state.script is script


# ---------------------------------------------------------------------------
# Storyboard state
# ---------------------------------------------------------------------------

def test_start_storyboarding_updates_state():
    state = WorkflowState(
        workflow_id="workflow_007",
        request=create_request(),
    )

    state.start_storyboarding()

    assert state.status == WORKFLOW_STORYBOARDING
    assert state.current_stage == "storyboard"


def test_set_storyboard_stores_storyboard():
    state = WorkflowState(
        workflow_id="workflow_008",
        request=create_request(),
    )

    storyboard = create_storyboard()

    state.set_storyboard(storyboard)

    assert state.storyboard is storyboard


# ---------------------------------------------------------------------------
# Completion
# ---------------------------------------------------------------------------

def test_complete_marks_workflow_completed():
    state = WorkflowState(
        workflow_id="workflow_009",
        request=create_request(),
    )

    state.start_planning()
    state.set_plan(create_plan())
    state.start_scripting()
    state.set_script(create_script())
    state.start_storyboarding()
    state.set_storyboard(create_storyboard())
    state.complete()

    assert state.status == WORKFLOW_COMPLETED
    assert state.current_stage is None
    assert state.error is None
    assert state.is_completed() is True
    assert state.is_failed() is False
    assert state.is_finished() is True


# ---------------------------------------------------------------------------
# Failure
# ---------------------------------------------------------------------------

def test_fail_marks_workflow_failed():
    state = WorkflowState(
        workflow_id="workflow_010",
        request=create_request(),
    )

    state.start_planning()
    state.fail("Planning failed.")

    assert state.status == WORKFLOW_FAILED
    assert state.error == "Planning failed."
    assert state.is_failed() is True
    assert state.is_completed() is False
    assert state.is_finished() is True


def test_fail_converts_error_to_string():
    state = WorkflowState(
        workflow_id="workflow_011",
        request=create_request(),
    )

    state.fail(
        RuntimeError("Something went wrong.")
    )

    assert state.error == "Something went wrong."


# ---------------------------------------------------------------------------
# Workflow status helpers
# ---------------------------------------------------------------------------

def test_pending_workflow_is_not_finished():
    state = WorkflowState(
        workflow_id="workflow_012",
        request=create_request(),
    )

    assert state.is_completed() is False
    assert state.is_failed() is False
    assert state.is_finished() is False


# ---------------------------------------------------------------------------
# Timestamp updates
# ---------------------------------------------------------------------------

def test_touch_updates_timestamp():
    state = WorkflowState(
        workflow_id="workflow_013",
        request=create_request(),
    )

    original_timestamp = state.updated_at

    state.touch()

    assert state.updated_at >= original_timestamp


def test_state_operations_update_timestamp():
    state = WorkflowState(
        workflow_id="workflow_014",
        request=create_request(),
    )

    original_timestamp = state.updated_at

    state.start_planning()

    assert state.updated_at >= original_timestamp


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_to_dict_serializes_initial_state():
    state = WorkflowState(
        workflow_id="workflow_015",
        request=create_request(),
    )

    result = state.to_dict()

    assert result["workflow_id"] == "workflow_015"
    assert result["status"] == WORKFLOW_PENDING
    assert result["current_stage"] is None
    assert result["plan"] is None
    assert result["script"] is None
    assert result["storyboard"] is None
    assert result["error"] is None
    assert isinstance(result["request"], dict)
    assert isinstance(result["created_at"], str)
    assert isinstance(result["updated_at"], str)


def test_to_dict_serializes_complete_state():
    state = WorkflowState(
        workflow_id="workflow_016",
        request=create_request(),
    )

    state.start_planning()
    state.set_plan(create_plan())
    state.start_scripting()
    state.set_script(create_script())
    state.start_storyboarding()
    state.set_storyboard(create_storyboard())
    state.complete()

    result = state.to_dict()

    assert result["workflow_id"] == "workflow_016"
    assert result["status"] == WORKFLOW_COMPLETED
    assert result["plan"] is not None
    assert result["script"] is not None
    assert result["storyboard"] is not None
    assert result["error"] is None


def test_to_dict_serializes_failed_state():
    state = WorkflowState(
        workflow_id="workflow_017",
        request=create_request(),
    )

    state.fail("Workflow failed.")

    result = state.to_dict()

    assert result["status"] == WORKFLOW_FAILED
    assert result["error"] == "Workflow failed."