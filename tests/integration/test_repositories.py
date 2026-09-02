"""
Integration tests for database repositories.

These tests verify that repository operations correctly persist,
retrieve, update, and delete SQLAlchemy models.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.project import ProjectModel
from app.models.video import VideoModel
from app.repositories.project_repository import ProjectRepository
from app.repositories.video_repository import VideoRepository


# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

@pytest.fixture
def session():
    """
    Create an isolated in-memory SQLite database for each test.
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

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(
            bind=engine,
        )
        engine.dispose()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def create_project(
    project_id: str = "project_001",
) -> ProjectModel:
    """
    Create a valid ProjectModel.
    """

    now = datetime.now(timezone.utc)

    return ProjectModel(
        project_id=project_id,
        name="Test Project",
        description="Repository integration test project.",
        status="draft",
        created_at=now,
        updated_at=now,
    )


def create_video(
    video_id: str = "video_001",
    project_id: str = "project_001",
) -> VideoModel:
    """
    Create a valid VideoModel.
    """

    return VideoModel(
        video_id=video_id,
        project_id=project_id,
        title="Test Video",
        duration=60,
        status="queued",
        resolution="1920x1080",
        fps=30,
        file_path=None,
        thumbnail_path=None,
        created_at=datetime.now(timezone.utc),
    )


# ===========================================================================
# ProjectRepository
# ===========================================================================

def test_project_repository_can_create_project(session):
    repository = ProjectRepository(session)

    project = create_project()

    result = repository.create(project)

    assert result.project_id == "project_001"
    assert result.name == "Test Project"

    stored = repository.get("project_001")

    assert stored is not None
    assert stored.project_id == "project_001"


def test_project_repository_get_returns_none_for_missing_project(session):
    repository = ProjectRepository(session)

    result = repository.get("missing_project")

    assert result is None


def test_project_repository_lists_projects(session):
    repository = ProjectRepository(session)

    repository.create(
        create_project("project_001"),
    )

    repository.create(
        create_project("project_002"),
    )

    result = repository.list()

    assert len(result) == 2
    assert result[0].project_id == "project_001"
    assert result[1].project_id == "project_002"


def test_project_repository_exists(session):
    repository = ProjectRepository(session)

    assert repository.exists("project_001") is False

    repository.create(
        create_project(),
    )

    assert repository.exists("project_001") is True


def test_project_repository_updates_project(session):
    repository = ProjectRepository(session)

    project = create_project()

    repository.create(project)

    project.name = "Updated Project"
    project.status = "active"

    result = repository.update(project)

    assert result.name == "Updated Project"
    assert result.status == "active"

    stored = repository.get("project_001")

    assert stored is not None
    assert stored.name == "Updated Project"
    assert stored.status == "active"


def test_project_repository_deletes_project(session):
    repository = ProjectRepository(session)

    repository.create(
        create_project(),
    )

    assert repository.get("project_001") is not None

    repository.delete(
        repository.get("project_001"),
    )

    assert repository.get("project_001") is None
    assert repository.exists("project_001") is False


def test_project_repository_list_empty_database(session):
    repository = ProjectRepository(session)

    result = repository.list()

    assert result == []


# ===========================================================================
# VideoRepository
# ===========================================================================

def test_video_repository_can_create_video(session):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project(),
    )

    video = create_video()

    result = video_repository.create(video)

    assert result.video_id == "video_001"
    assert result.project_id == "project_001"

    stored = video_repository.get("video_001")

    assert stored is not None
    assert stored.video_id == "video_001"


def test_video_repository_get_returns_none_for_missing_video(session):
    repository = VideoRepository(session)

    result = repository.get("missing_video")

    assert result is None


def test_video_repository_lists_videos(session):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project(),
    )

    video_repository.create(
        create_video("video_001"),
    )

    video_repository.create(
        create_video("video_002"),
    )

    result = video_repository.list()

    assert len(result) == 2
    assert result[0].video_id == "video_001"
    assert result[1].video_id == "video_002"


def test_video_repository_lists_videos_for_project(session):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project("project_001"),
    )

    project_repository.create(
        create_project("project_002"),
    )

    video_repository.create(
        create_video(
            "video_001",
            "project_001",
        ),
    )

    video_repository.create(
        create_video(
            "video_002",
            "project_001",
        ),
    )

    video_repository.create(
        create_video(
            "video_003",
            "project_002",
        ),
    )

    result = video_repository.list_by_project(
        "project_001",
    )

    assert len(result) == 2

    video_ids = [
        video.video_id
        for video in result
    ]

    assert video_ids == [
        "video_001",
        "video_002",
    ]


def test_video_repository_returns_empty_project_video_list(
    session,
):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project(),
    )

    result = video_repository.list_by_project(
        "project_001",
    )

    assert result == []


def test_video_repository_exists(session):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project(),
    )

    assert video_repository.exists(
        "video_001",
    ) is False

    video_repository.create(
        create_video(),
    )

    assert video_repository.exists(
        "video_001",
    ) is True


def test_video_repository_updates_video(session):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project(),
    )

    video = create_video()

    video_repository.create(video)

    video.status = "completed"
    video.file_path = "/videos/final.mp4"
    video.thumbnail_path = "/videos/final.jpg"

    result = video_repository.update(video)

    assert result.status == "completed"
    assert result.file_path == "/videos/final.mp4"
    assert result.thumbnail_path == "/videos/final.jpg"

    stored = video_repository.get("video_001")

    assert stored is not None
    assert stored.status == "completed"
    assert stored.file_path == "/videos/final.mp4"


def test_video_repository_deletes_video(session):
    project_repository = ProjectRepository(session)
    video_repository = VideoRepository(session)

    project_repository.create(
        create_project(),
    )

    video_repository.create(
        create_video(),
    )

    assert video_repository.get("video_001") is not None

    video_repository.delete(
        video_repository.get("video_001"),
    )

    assert video_repository.get("video_001") is None
    assert video_repository.exists("video_001") is False


def test_video_repository_list_empty_database(session):
    repository = VideoRepository(session)

    result = repository.list()

    assert result == []