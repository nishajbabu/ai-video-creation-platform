"""
Integration tests for SceneRepository.

These tests verify that SceneRepository correctly persists,
retrieves, updates, deletes, and queries SceneModel records.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.project import ProjectModel
from app.models.video import VideoModel
from app.models.scene import SceneModel
from app.repositories.scene_repository import SceneRepository


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
        description="Scene repository test project.",
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


def create_scene(
    video_id: str = "video_001",
    order: int = 1,
    duration: int = 20,
    purpose: str = "Introduce the topic.",
) -> SceneModel:
    """
    Create a valid SceneModel.
    """

    return SceneModel(
        video_id=video_id,
        order=order,
        duration=duration,
        purpose=purpose,
        narration="This scene introduces the topic.",
        visual_description="A clean professional introduction.",
        visual_prompt="Professional product introduction scene.",
        visual_type="image",
        status="planned",
        has_asset_requirements=False,
        has_audio_requirements=True,
    )


def create_test_video(
    session,
    video_id: str = "video_001",
    project_id: str = "project_001",
) -> VideoModel:
    """
    Create and persist a project and video for scene tests.
    """

    project = create_project(
        project_id,
    )

    session.add(project)
    session.commit()

    video = create_video(
        video_id,
        project_id,
    )

    session.add(video)
    session.commit()
    session.refresh(video)

    return video


# ===========================================================================
# SceneRepository - Create
# ===========================================================================

def test_scene_repository_can_create_scene(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = create_scene(
        video.video_id,
    )

    result = repository.create(
        scene,
    )

    assert result.scene_id is not None
    assert result.video_id == "video_001"
    assert result.order == 1
    assert result.duration == 20


def test_scene_repository_generates_scene_id(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = create_scene(
        video.video_id,
    )

    assert scene.scene_id is None

    result = repository.create(
        scene,
    )

    assert result.scene_id is not None
    assert result.scene_id > 0


def test_scene_repository_preserves_scene_content(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = create_scene(
        video.video_id,
        order=3,
        duration=25,
        purpose="Explain the product.",
    )

    result = repository.create(
        scene,
    )

    assert result.order == 3
    assert result.duration == 25
    assert result.purpose == "Explain the product."
    assert result.narration == (
        "This scene introduces the topic."
    )
    assert result.visual_type == "image"
    assert result.status == "planned"


# ===========================================================================
# SceneRepository - Get
# ===========================================================================

def test_scene_repository_gets_scene(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = repository.create(
        create_scene(
            video.video_id,
        ),
    )

    result = repository.get(
        scene.scene_id,
    )

    assert result is not None
    assert result.scene_id == scene.scene_id
    assert result.video_id == video.video_id


def test_scene_repository_get_returns_none_for_missing_scene(session):
    repository = SceneRepository(session)

    result = repository.get(
        999999,
    )

    assert result is None


# ===========================================================================
# SceneRepository - List
# ===========================================================================

def test_scene_repository_lists_scenes(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    repository.create(
        create_scene(
            video.video_id,
            order=1,
        ),
    )

    repository.create(
        create_scene(
            video.video_id,
            order=2,
        ),
    )

    result = repository.list()

    assert len(result) == 2
    assert result[0].order == 1
    assert result[1].order == 2


def test_scene_repository_lists_scenes_by_video(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    repository.create(
        create_scene(
            video.video_id,
            order=1,
        ),
    )

    repository.create(
        create_scene(
            video.video_id,
            order=2,
        ),
    )

    result = repository.list_by_video(
        video.video_id,
    )

    assert len(result) == 2

    assert [
        scene.order
        for scene in result
    ] == [
        1,
        2,
    ]


def test_scene_repository_returns_empty_for_video_without_scenes(
    session,
):
    video = create_test_video(session)

    repository = SceneRepository(session)

    result = repository.list_by_video(
        video.video_id,
    )

    assert result == []


def test_scene_repository_orders_scenes_by_timeline(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    repository.create(
        create_scene(
            video.video_id,
            order=3,
        ),
    )

    repository.create(
        create_scene(
            video.video_id,
            order=1,
        ),
    )

    repository.create(
        create_scene(
            video.video_id,
            order=2,
        ),
    )

    result = repository.list_by_video(
        video.video_id,
    )

    assert [
        scene.order
        for scene in result
    ] == [
        1,
        2,
        3,
    ]


def test_scene_repository_list_empty_database(session):
    repository = SceneRepository(session)

    result = repository.list()

    assert result == []


# ===========================================================================
# SceneRepository - Update
# ===========================================================================

def test_scene_repository_updates_scene(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = repository.create(
        create_scene(
            video.video_id,
        ),
    )

    scene.duration = 30
    scene.purpose = "Updated purpose."

    result = repository.update(
        scene,
    )

    assert result.duration == 30
    assert result.purpose == "Updated purpose."


def test_scene_repository_persists_update(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = repository.create(
        create_scene(
            video.video_id,
        ),
    )

    scene.status = "ready"

    repository.update(
        scene,
    )

    stored = repository.get(
        scene.scene_id,
    )

    assert stored is not None
    assert stored.status == "ready"


# ===========================================================================
# SceneRepository - Delete
# ===========================================================================

def test_scene_repository_deletes_scene(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    scene = repository.create(
        create_scene(
            video.video_id,
        ),
    )

    assert repository.get(
        scene.scene_id,
    ) is not None

    repository.delete(
        scene,
    )

    assert repository.get(
        scene.scene_id,
    ) is None

    assert repository.exists(
        scene.scene_id,
    ) is False


# ===========================================================================
# SceneRepository - Exists
# ===========================================================================

def test_scene_repository_exists(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    assert repository.exists(
        999999,
    ) is False

    scene = repository.create(
        create_scene(
            video.video_id,
        ),
    )

    assert repository.exists(
        scene.scene_id,
    ) is True


# ===========================================================================
# SceneRepository - Video helpers
# ===========================================================================

def test_scene_repository_exists_for_video(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    assert repository.exists_for_video(
        video.video_id,
    ) is False

    repository.create(
        create_scene(
            video.video_id,
        ),
    )

    assert repository.exists_for_video(
        video.video_id,
    ) is True


def test_scene_repository_exists_for_video_returns_false(
    session,
):
    video = create_test_video(session)

    repository = SceneRepository(session)

    assert repository.exists_for_video(
        video.video_id,
    ) is False


def test_scene_repository_counts_scenes_for_video(session):
    video = create_test_video(session)

    repository = SceneRepository(session)

    repository.create(
        create_scene(
            video.video_id,
            order=1,
        ),
    )

    repository.create(
        create_scene(
            video.video_id,
            order=2,
        ),
    )

    repository.create(
        create_scene(
            video.video_id,
            order=3,
        ),
    )

    assert repository.count_for_video(
        video.video_id,
    ) == 3


def test_scene_repository_count_is_zero_for_empty_video(
    session,
):
    video = create_test_video(session)

    repository = SceneRepository(session)

    assert repository.count_for_video(
        video.video_id,
    ) == 0