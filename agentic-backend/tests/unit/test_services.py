import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.project import ProjectModel
from app.models.video import VideoModel
from app.repositories.project_repository import ProjectRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.project import Project
from app.schemas.requests import VideoRequest
from app.schemas.video import Video
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService
from app.services.video_service import VideoService


# ===========================================================================
# Database fixture
# ===========================================================================

@pytest.fixture
def db_session():
    """
    Create an isolated SQLite database for each service test.
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
    )

    Base.metadata.create_all(
        bind=engine,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
        )
        engine.dispose()


@pytest.fixture
def project_service(db_session):
    """
    Create a ProjectService backed by an isolated test database.
    """

    repository = ProjectRepository(
        db_session,
    )

    return ProjectService(
        repository=repository,
    )


@pytest.fixture
def video_service(db_session):
    """
    Create a VideoService backed by an isolated test database.
    """

    repository = VideoRepository(
        db_session,
    )

    return VideoService(
        repository=repository,
    )


# ===========================================================================
# Shared test helpers
# ===========================================================================

def create_video_request() -> VideoRequest:
    """
    Create a valid VideoRequest for service tests.
    """

    return VideoRequest(
        prompt="Create a professional AI product introduction video.",
        duration=60,
        style="professional",
        target_audience="Potential customers",
        tone="confident",
    )


def create_project(
    project_id: str = "proj_001",
    name: str = "AI Chatbot Introduction",
) -> Project:
    """
    Create a valid Project for service tests.
    """

    return Project(
        project_id=project_id,
        name=name,
        description="AI chatbot product introduction.",
    )


def create_video(
    video_id: str = "video_001",
    project_id: str = "proj_001",
    title: str = "AI Chatbot Introduction",
    duration: int = 60,
) -> Video:
    """
    Create a valid Video for service tests.
    """

    return Video(
        video_id=video_id,
        project_id=project_id,
        title=title,
        duration=duration,
    )


# ===========================================================================
# GenerationService tests
# ===========================================================================

# ---------------------------------------------------------------------------
# GenerationService initialization
# ---------------------------------------------------------------------------

def test_generation_service_can_be_created_without_orchestrator():
    service = GenerationService()

    assert service.orchestrator is None
    assert service.is_configured() is False


def test_generation_service_reports_configured_orchestrator():
    class FakeOrchestrator:
        pass

    orchestrator = FakeOrchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    assert service.orchestrator is orchestrator
    assert service.is_configured() is True


# ---------------------------------------------------------------------------
# Generation without orchestrator
# ---------------------------------------------------------------------------

def test_generation_service_accepts_request_without_orchestrator():
    service = GenerationService()

    request = create_video_request()

    result = service.start_generation(
        request,
    )

    assert result["status"] == "accepted"
    assert result["prompt"] == request.prompt
    assert result["duration"] == request.duration
    assert result["workflow_started"] is False


# ---------------------------------------------------------------------------
# Generation with orchestrator
# ---------------------------------------------------------------------------

def test_generation_service_delegates_to_orchestrator():
    class FakeOrchestrator:
        def __init__(self):
            self.received_request = None

        def run(self, request):
            self.received_request = request

            return {
                "status": "completed",
                "workflow_started": True,
                "project_id": "proj_001",
            }

    orchestrator = FakeOrchestrator()

    service = GenerationService(
        orchestrator=orchestrator,
    )

    request = create_video_request()

    result = service.start_generation(
        request,
    )

    assert orchestrator.received_request is request
    assert result["status"] == "completed"
    assert result["workflow_started"] is True
    assert result["project_id"] == "proj_001"


# ---------------------------------------------------------------------------
# Result normalization
# ---------------------------------------------------------------------------

def test_normalize_result_accepts_dictionary():
    service = GenerationService()

    result = service._normalize_result(
        {
            "status": "completed",
            "video_id": "video_001",
        }
    )

    assert result == {
        "status": "completed",
        "video_id": "video_001",
    }


def test_normalize_result_accepts_pydantic_model():
    class FakeModel:
        def model_dump(self):
            return {
                "status": "completed",
                "video_id": "video_002",
            }

    service = GenerationService()

    result = service._normalize_result(
        FakeModel(),
    )

    assert result["status"] == "completed"
    assert result["video_id"] == "video_002"


def test_normalize_result_accepts_legacy_pydantic_style_model():
    class FakeModel:
        def dict(self):
            return {
                "status": "completed",
                "video_id": "video_003",
            }

    service = GenerationService()

    result = service._normalize_result(
        FakeModel(),
    )

    assert result["status"] == "completed"
    assert result["video_id"] == "video_003"


def test_normalize_result_wraps_unknown_result_type():
    service = GenerationService()

    result = service._normalize_result(
        "workflow-result",
    )

    assert result == {
        "status": "completed",
        "result": "workflow-result",
    }


# ---------------------------------------------------------------------------
# Orchestrator failure propagation
# ---------------------------------------------------------------------------

def test_generation_service_propagates_orchestrator_error():
    class FakeOrchestrator:
        def run(self, request):
            raise RuntimeError(
                "Workflow execution failed."
            )

    service = GenerationService(
        orchestrator=FakeOrchestrator(),
    )

    request = create_video_request()

    with pytest.raises(
        RuntimeError,
        match="Workflow execution failed.",
    ):
        service.start_generation(
            request,
        )


# ===========================================================================
# ProjectService tests
# ===========================================================================

# ---------------------------------------------------------------------------
# ProjectService initialization
# ---------------------------------------------------------------------------

def test_project_service_can_be_created(project_service):
    service = project_service

    assert service.list_projects() == []


# ---------------------------------------------------------------------------
# Project creation
# ---------------------------------------------------------------------------

def test_project_service_creates_project(project_service):
    service = project_service

    project = create_project()

    result = service.create_project(
        project,
    )

    assert result == project
    assert result.project_id == "proj_001"
    assert result.name == "AI Chatbot Introduction"
    assert service.exists("proj_001") is True


def test_project_service_rejects_duplicate_project(project_service):
    service = project_service

    service.create_project(
        create_project()
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        service.create_project(
            create_project()
        )


# ---------------------------------------------------------------------------
# Project retrieval
# ---------------------------------------------------------------------------

def test_project_service_gets_project(project_service):
    service = project_service

    project = create_project()

    service.create_project(
        project,
    )

    result = service.get_project(
        "proj_001",
    )

    assert result == project


def test_project_service_returns_none_for_missing_project(
    project_service,
):
    service = project_service

    result = service.get_project(
        "does_not_exist",
    )

    assert result is None


def test_project_service_lists_projects(project_service):
    service = project_service

    service.create_project(
        create_project(
            "proj_001",
            "Project One",
        )
    )

    service.create_project(
        create_project(
            "proj_002",
            "Project Two",
        )
    )

    projects = service.list_projects()

    assert len(projects) == 2
    assert projects[0].project_id == "proj_001"
    assert projects[1].project_id == "proj_002"


# ---------------------------------------------------------------------------
# Project update
# ---------------------------------------------------------------------------

def test_project_service_updates_project(project_service):
    service = project_service

    service.create_project(
        create_project()
    )

    result = service.update_project(
        "proj_001",
        name="Updated AI Chatbot",
        description="Updated description.",
        status="generating",
    )

    assert result is not None
    assert result.name == "Updated AI Chatbot"
    assert result.description == "Updated description."
    assert result.status == "generating"


def test_project_service_returns_none_when_updating_missing_project(
    project_service,
):
    service = project_service

    result = service.update_project(
        "does_not_exist",
        name="Updated Project",
    )

    assert result is None


# ---------------------------------------------------------------------------
# Project deletion
# ---------------------------------------------------------------------------

def test_project_service_deletes_project(project_service):
    service = project_service

    service.create_project(
        create_project()
    )

    deleted = service.delete_project(
        "proj_001",
    )

    assert deleted is True
    assert service.exists("proj_001") is False
    assert service.get_project("proj_001") is None


def test_project_service_delete_missing_project_returns_false(
    project_service,
):
    service = project_service

    deleted = service.delete_project(
        "does_not_exist",
    )

    assert deleted is False


# ---------------------------------------------------------------------------
# Project reset
# ---------------------------------------------------------------------------

def test_project_service_clear_removes_all_projects(
    project_service,
):
    service = project_service

    service.create_project(
        create_project("proj_001")
    )

    service.create_project(
        create_project("proj_002")
    )

    service.clear()

    assert service.list_projects() == []


# ===========================================================================
# VideoService tests
# ===========================================================================

# ---------------------------------------------------------------------------
# VideoService initialization
# ---------------------------------------------------------------------------

def test_video_service_can_be_created(video_service):
    service = video_service

    assert service.list_videos() == []


# ---------------------------------------------------------------------------
# Video creation
# ---------------------------------------------------------------------------

def test_video_service_creates_video(video_service):
    service = video_service

    video = create_video()

    result = service.create_video(
        video,
    )

    assert result == video
    assert result.video_id == "video_001"
    assert result.project_id == "proj_001"
    assert service.exists("video_001") is True


def test_video_service_rejects_duplicate_video(video_service):
    service = video_service

    service.create_video(
        create_video()
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        service.create_video(
            create_video()
        )


# ---------------------------------------------------------------------------
# Video retrieval
# ---------------------------------------------------------------------------

def test_video_service_gets_video(video_service):
    service = video_service

    video = create_video()

    service.create_video(
        video,
    )

    result = service.get_video(
        "video_001",
    )

    assert result == video


def test_video_service_returns_none_for_missing_video(
    video_service,
):
    service = video_service

    result = service.get_video(
        "does_not_exist",
    )

    assert result is None


def test_video_service_lists_videos(video_service):
    service = video_service

    service.create_video(
        create_video(
            "video_001",
            "proj_001",
            "Video One",
        )
    )

    service.create_video(
        create_video(
            "video_002",
            "proj_001",
            "Video Two",
        )
    )

    videos = service.list_videos()

    assert len(videos) == 2
    assert videos[0].video_id == "video_001"
    assert videos[1].video_id == "video_002"


# ---------------------------------------------------------------------------
# Project video retrieval
# ---------------------------------------------------------------------------

def test_video_service_gets_videos_for_project(video_service):
    service = video_service

    service.create_video(
        create_video(
            "video_001",
            "proj_001",
            "Project One Video",
        )
    )

    service.create_video(
        create_video(
            "video_002",
            "proj_001",
            "Project One Video Two",
        )
    )

    service.create_video(
        create_video(
            "video_003",
            "proj_002",
            "Project Two Video",
        )
    )

    videos = service.get_videos_for_project(
        "proj_001",
    )

    assert len(videos) == 2
    assert videos[0].video_id == "video_001"
    assert videos[1].video_id == "video_002"


def test_video_service_returns_empty_list_for_project_without_videos(
    video_service,
):
    service = video_service

    videos = service.get_videos_for_project(
        "does_not_exist",
    )

    assert videos == []


# ---------------------------------------------------------------------------
# Video status update
# ---------------------------------------------------------------------------

def test_video_service_updates_video_status(video_service):
    service = video_service

    service.create_video(
        create_video()
    )

    result = service.update_video_status(
        "video_001",
        "rendering",
    )

    assert result is not None
    assert result.status == "rendering"


def test_video_service_returns_none_when_updating_missing_status(
    video_service,
):
    service = video_service

    result = service.update_video_status(
        "does_not_exist",
        "rendering",
    )

    assert result is None


# ---------------------------------------------------------------------------
# Video file update
# ---------------------------------------------------------------------------

def test_video_service_updates_video_file(video_service):
    service = video_service

    service.create_video(
        create_video()
    )

    result = service.update_video_file(
        "video_001",
        file_path="output/video_001.mp4",
        thumbnail_path="output/video_001.jpg",
    )

    assert result is not None
    assert result.file_path == "output/video_001.mp4"
    assert result.thumbnail_path == "output/video_001.jpg"


def test_video_service_updates_only_file_path(video_service):
    service = video_service

    service.create_video(
        create_video()
    )

    result = service.update_video_file(
        "video_001",
        file_path="output/video_001.mp4",
    )

    assert result is not None
    assert result.file_path == "output/video_001.mp4"
    assert result.thumbnail_path is None


def test_video_service_returns_none_when_updating_missing_file(
    video_service,
):
    service = video_service

    result = service.update_video_file(
        "does_not_exist",
        file_path="output/video.mp4",
    )

    assert result is None


# ---------------------------------------------------------------------------
# Video deletion
# ---------------------------------------------------------------------------

def test_video_service_deletes_video(video_service):
    service = video_service

    service.create_video(
        create_video()
    )

    deleted = service.delete_video(
        "video_001",
    )

    assert deleted is True
    assert service.exists("video_001") is False
    assert service.get_video("video_001") is None


def test_video_service_delete_missing_video_returns_false(
    video_service,
):
    service = video_service

    deleted = service.delete_video(
        "does_not_exist",
    )

    assert deleted is False


# ---------------------------------------------------------------------------
# Video reset
# ---------------------------------------------------------------------------

def test_video_service_clear_removes_all_videos(
    video_service,
):
    service = video_service

    service.create_video(
        create_video("video_001")
    )

    service.create_video(
        create_video("video_002")
    )

    service.clear()

    assert service.list_videos() == []
