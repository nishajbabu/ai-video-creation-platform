import pytest

from app.agents.orchestrator import Orchestrator
from app.schemas.plan import VideoPlan
from app.schemas.requests import VideoRequest
from app.schemas.script import Script
from app.schemas.storyboard import Storyboard


def create_video_request() -> VideoRequest:
    """
    Create a valid VideoRequest for orchestrator tests.
    """

    return VideoRequest(
        prompt="Create a professional AI product introduction video.",
        duration=60,
        style="professional",
        target_audience="Potential customers",
        tone="confident",
    )


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def test_orchestrator_can_be_created():
    orchestrator = Orchestrator()

    assert orchestrator.planner is not None
    assert orchestrator.script_agent is not None
    assert orchestrator.storyboard_agent is not None
    assert orchestrator.is_configured() is True


def test_orchestrator_accepts_injected_agents():
    class FakePlanner:
        pass

    class FakeScriptAgent:
        pass

    class FakeStoryboardAgent:
        pass

    planner = FakePlanner()
    script_agent = FakeScriptAgent()
    storyboard_agent = FakeStoryboardAgent()

    orchestrator = Orchestrator(
        planner=planner,
        script_agent=script_agent,
        storyboard_agent=storyboard_agent,
    )

    assert orchestrator.planner is planner
    assert orchestrator.script_agent is script_agent
    assert orchestrator.storyboard_agent is storyboard_agent


# ---------------------------------------------------------------------------
# Individual workflow stages
# ---------------------------------------------------------------------------

def test_orchestrator_delegates_planning():
    class FakePlanner:
        def __init__(self):
            self.received_request = None

        def create_plan(self, request):
            self.received_request = request

            return VideoPlan(
                objective="Create a professional product video.",
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=3,
            )

    planner = FakePlanner()

    orchestrator = Orchestrator(
        planner=planner,
    )

    request = create_video_request()

    result = orchestrator.create_plan(
        request,
    )

    assert planner.received_request is request
    assert isinstance(result, VideoPlan)
    assert result.duration == 60
    assert result.scene_count == 3


def test_orchestrator_delegates_script_generation():
    class FakeScriptAgent:
        def __init__(self):
            self.received_plan = None

        def create_script(self, plan):
            self.received_plan = plan

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

    script_agent = FakeScriptAgent()

    orchestrator = Orchestrator(
        script_agent=script_agent,
    )

    plan = VideoPlan(
        objective="Create a professional product video.",
        target_audience="Customers",
        tone="professional",
        style="modern",
        duration=60,
        scene_count=2,
    )

    result = orchestrator.create_script(
        plan,
    )

    assert script_agent.received_plan is plan
    assert isinstance(result, Script)
    assert result.total_duration == 60


def test_orchestrator_delegates_storyboard_generation():
    class FakeStoryboardAgent:
        def __init__(self):
            self.received_script = None

        def create_storyboard(self, script):
            self.received_script = script

            return Storyboard(
                scenes=[
                    {
                        "scene_id": 1,
                        "order": 1,
                        "duration": 30,
                        "purpose": "Introduce the product.",
                        "narration": "Welcome.",
                        "visual_description": (
                            "Professional product introduction."
                        ),
                        "visual_prompt": (
                            "Create a professional product visual."
                        ),
                    },
                ]
            )

    storyboard_agent = FakeStoryboardAgent()

    orchestrator = Orchestrator(
        storyboard_agent=storyboard_agent,
    )

    script = Script(
        scenes=[
            {
                "scene_id": 1,
                "purpose": "Introduce the product.",
                "duration": 30,
                "narration": "Welcome.",
            },
        ]
    )

    result = orchestrator.create_storyboard(
        script,
    )

    assert storyboard_agent.received_script is script
    assert isinstance(result, Storyboard)
    assert result.scene_count == 1


# ---------------------------------------------------------------------------
# Complete workflow
# ---------------------------------------------------------------------------

def test_orchestrator_runs_complete_workflow():
    execution_order = []

    class FakePlanner:
        def create_plan(self, request):
            execution_order.append("planner")

            return VideoPlan(
                objective="Create a professional product video.",
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=2,
            )

    class FakeScriptAgent:
        def create_script(self, plan):
            execution_order.append("script")

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
                        "purpose": "Conclude the product story.",
                        "duration": 30,
                        "narration": "Thank you.",
                    },
                ]
            )

    class FakeStoryboardAgent:
        def create_storyboard(self, script):
            execution_order.append("storyboard")

            return Storyboard(
                scenes=[
                    {
                        "scene_id": 1,
                        "order": 1,
                        "duration": 30,
                        "purpose": "Introduce the product.",
                        "narration": "Welcome.",
                        "visual_description": (
                            "Product introduction."
                        ),
                        "visual_prompt": (
                            "Professional product visual."
                        ),
                    },
                    {
                        "scene_id": 2,
                        "order": 2,
                        "duration": 30,
                        "purpose": "Conclude the product story.",
                        "narration": "Thank you.",
                        "visual_description": (
                            "Product conclusion."
                        ),
                        "visual_prompt": (
                            "Professional conclusion visual."
                        ),
                    },
                ]
            )

    orchestrator = Orchestrator(
        planner=FakePlanner(),
        script_agent=FakeScriptAgent(),
        storyboard_agent=FakeStoryboardAgent(),
    )

    result = orchestrator.run(
        create_video_request(),
    )

    assert execution_order == [
        "planner",
        "script",
        "storyboard",
    ]

    assert result["status"] == "completed"
    assert result["plan"] is not None
    assert result["script"] is not None
    assert result["storyboard"] is not None


def test_orchestrator_passes_each_stage_output_to_next_stage():
    class FakePlanner:
        def __init__(self):
            self.plan = VideoPlan(
                objective="Create a professional product video.",
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=1,
            )

        def create_plan(self, request):
            return self.plan

    class FakeScriptAgent:
        def __init__(self):
            self.received_plan = None
            self.script = Script(
                scenes=[
                    {
                        "scene_id": 1,
                        "purpose": "Introduce the product.",
                        "duration": 60,
                        "narration": "Welcome.",
                    },
                ]
            )

        def create_script(self, plan):
            self.received_plan = plan
            return self.script

    class FakeStoryboardAgent:
        def __init__(self):
            self.received_script = None

            self.storyboard = Storyboard(
                scenes=[
                    {
                        "scene_id": 1,
                        "order": 1,
                        "duration": 60,
                        "purpose": "Introduce the product.",
                        "narration": "Welcome.",
                        "visual_description": (
                            "Product introduction."
                        ),
                        "visual_prompt": (
                            "Professional product visual."
                        ),
                    },
                ]
            )

        def create_storyboard(self, script):
            self.received_script = script
            return self.storyboard

    planner = FakePlanner()
    script_agent = FakeScriptAgent()
    storyboard_agent = FakeStoryboardAgent()

    orchestrator = Orchestrator(
        planner=planner,
        script_agent=script_agent,
        storyboard_agent=storyboard_agent,
    )

    orchestrator.run(
        create_video_request(),
    )

    assert (
        script_agent.received_plan
        is planner.plan
    )

    assert (
        storyboard_agent.received_script
        is script_agent.script
    )


# ---------------------------------------------------------------------------
# Result serialization
# ---------------------------------------------------------------------------

def test_orchestrator_serializes_complete_result():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        create_video_request(),
    )

    assert result["status"] == "completed"

    assert isinstance(
        result["request"],
        dict,
    )

    assert isinstance(
        result["plan"],
        dict,
    )

    assert isinstance(
        result["script"],
        dict,
    )

    assert isinstance(
        result["storyboard"],
        dict,
    )

    assert result["error"] is None


def test_orchestrator_serialized_result_contains_expected_data():
    orchestrator = Orchestrator()

    result = orchestrator.run(
        create_video_request(),
    )

    assert (
        result["request"]["prompt"]
        == "Create a professional AI product introduction video."
    )

    assert result["plan"]["duration"] == 60

    assert (
        len(result["script"]["scenes"])
        == 5
    )

    assert (
        len(result["storyboard"]["scenes"])
        == 5
    )


# ---------------------------------------------------------------------------
# Failure propagation
# ---------------------------------------------------------------------------

def test_orchestrator_propagates_planner_error():
    class FailingPlanner:
        def create_plan(self, request):
            raise RuntimeError(
                "Planning failed."
            )

    orchestrator = Orchestrator(
        planner=FailingPlanner(),
    )

    with pytest.raises(
        RuntimeError,
        match="Planning failed.",
    ):
        orchestrator.run(
            create_video_request(),
        )


def test_orchestrator_propagates_script_error():
    class WorkingPlanner:
        def create_plan(self, request):
            return VideoPlan(
                objective="Create a professional product video.",
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=1,
            )

    class FailingScriptAgent:
        def create_script(self, plan):
            raise RuntimeError(
                "Script generation failed."
            )

    orchestrator = Orchestrator(
        planner=WorkingPlanner(),
        script_agent=FailingScriptAgent(),
    )

    with pytest.raises(
        RuntimeError,
        match="Script generation failed.",
    ):
        orchestrator.run(
            create_video_request(),
        )


def test_orchestrator_propagates_storyboard_error():
    class WorkingPlanner:
        def create_plan(self, request):
            return VideoPlan(
                objective="Create a professional product video.",
                target_audience="Customers",
                tone="professional",
                style="modern",
                duration=60,
                scene_count=1,
            )

    class WorkingScriptAgent:
        def create_script(self, plan):
            return Script(
                scenes=[
                    {
                        "scene_id": 1,
                        "purpose": "Introduce the product.",
                        "duration": 60,
                        "narration": "Welcome.",
                    },
                ]
            )

    class FailingStoryboardAgent:
        def create_storyboard(self, script):
            raise RuntimeError(
                "Storyboard generation failed."
            )

    orchestrator = Orchestrator(
        planner=WorkingPlanner(),
        script_agent=WorkingScriptAgent(),
        storyboard_agent=FailingStoryboardAgent(),
    )

    with pytest.raises(
        RuntimeError,
        match="Storyboard generation failed.",
    ):
        orchestrator.run(
            create_video_request(),
        )


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def test_orchestrator_reports_configured():
    orchestrator = Orchestrator()

    assert orchestrator.is_configured() is True