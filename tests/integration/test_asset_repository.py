"""
Integration tests for AssetRepository.

These tests verify that AssetRepository correctly persists,
retrieves, updates, deletes, and queries AssetModel records.
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.project import ProjectModel
from app.models.video import VideoModel
from app.models.scene import SceneModel
from app.models.asset import AssetModel
from app.repositories.asset_repository import AssetRepository


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
        description="Asset repository test project.",
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
    session,
    video_id: str = "video_001",
) -> SceneModel:
    """
    Create and persist a valid SceneModel.
    """

    scene = SceneModel(
        video_id=video_id,
        order=1,
        duration=20,
        purpose="Introduce the product.",
        narration="Welcome to the product.",
        visual_description="A professional product introduction.",
        visual_prompt="Professional product introduction scene.",
        visual_type="image",
        status="planned",
        has_asset_requirements=False,
        has_audio_requirements=True,
    )

    session.add(scene)
    session.commit()
    session.refresh(scene)

    return scene


def create_test_scene(
    session,
) -> SceneModel:
    """
    Create the required project, video, and scene hierarchy.
    """

    project = create_project()

    session.add(project)
    session.commit()

    video = create_video()

    session.add(video)
    session.commit()

    session.refresh(video)

    return create_scene(
        session,
        video.video_id,
    )


def create_asset(
    scene_id: int | None = None,
    asset_type: str = "image",
    description: str = "Product reference image.",
    source: str = "library",
) -> AssetModel:
    """
    Create a valid AssetModel.
    """

    return AssetModel(
        scene_id=scene_id,
        asset_type=asset_type,
        description=description,
        source=source,
        file_path=None,
        url=None,
        created_at=datetime.now(timezone.utc),
    )


# ===========================================================================
# AssetRepository - Create
# ===========================================================================

def test_asset_repository_can_create_asset(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = create_asset(
        scene_id=scene.scene_id,
    )

    result = repository.create(
        asset,
    )

    assert result.asset_id is not None
    assert result.scene_id == scene.scene_id
    assert result.asset_type == "image"
    assert result.description == "Product reference image."


def test_asset_repository_generates_asset_id(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = create_asset(
        scene_id=scene.scene_id,
    )

    assert asset.asset_id is None

    result = repository.create(
        asset,
    )

    assert result.asset_id is not None
    assert result.asset_id > 0


def test_asset_repository_preserves_asset_information(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = create_asset(
        scene_id=scene.scene_id,
        asset_type="logo",
        description="Company logo.",
        source="user_upload",
    )

    result = repository.create(
        asset,
    )

    assert result.asset_type == "logo"
    assert result.description == "Company logo."
    assert result.source == "user_upload"


# ===========================================================================
# AssetRepository - Get
# ===========================================================================

def test_asset_repository_gets_asset(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    result = repository.get(
        asset.asset_id,
    )

    assert result is not None
    assert result.asset_id == asset.asset_id
    assert result.scene_id == scene.scene_id


def test_asset_repository_get_returns_none_for_missing_asset(session):
    repository = AssetRepository(session)

    result = repository.get(
        999999,
    )

    assert result is None


# ===========================================================================
# AssetRepository - List
# ===========================================================================

def test_asset_repository_lists_assets(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
            description="First asset.",
        ),
    )

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
            description="Second asset.",
        ),
    )

    result = repository.list()

    assert len(result) == 2
    assert result[0].description == "First asset."
    assert result[1].description == "Second asset."


def test_asset_repository_lists_assets_by_scene(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
            description="First asset.",
        ),
    )

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
            description="Second asset.",
        ),
    )

    result = repository.list_by_scene(
        scene.scene_id,
    )

    assert len(result) == 2

    descriptions = [
        asset.description
        for asset in result
    ]

    assert descriptions == [
        "First asset.",
        "Second asset.",
    ]


def test_asset_repository_returns_empty_for_scene_without_assets(
    session,
):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    result = repository.list_by_scene(
        scene.scene_id,
    )

    assert result == []


def test_asset_repository_lists_unassigned_assets(session):
    repository = AssetRepository(session)

    repository.create(
        create_asset(
            scene_id=None,
            description="Unassigned asset.",
        ),
    )

    result = repository.list_unassigned()

    assert len(result) == 1
    assert result[0].description == "Unassigned asset."


def test_asset_repository_does_not_return_assigned_assets_as_unassigned(
    session,
):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
            description="Assigned asset.",
        ),
    )

    repository.create(
        create_asset(
            scene_id=None,
            description="Unassigned asset.",
        ),
    )

    result = repository.list_unassigned()

    assert len(result) == 1
    assert result[0].description == "Unassigned asset."


def test_asset_repository_list_empty_database(session):
    repository = AssetRepository(session)

    result = repository.list()

    assert result == []


# ===========================================================================
# AssetRepository - Update
# ===========================================================================

def test_asset_repository_updates_asset(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    asset.description = "Updated asset description."
    asset.source = "ai"

    result = repository.update(
        asset,
    )

    assert result.description == "Updated asset description."
    assert result.source == "ai"


def test_asset_repository_persists_update(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    asset.file_path = "/assets/product.png"
    asset.url = "https://example.com/product.png"

    repository.update(
        asset,
    )

    stored = repository.get(
        asset.asset_id,
    )

    assert stored is not None
    assert stored.file_path == "/assets/product.png"
    assert stored.url == "https://example.com/product.png"


# ===========================================================================
# AssetRepository - Delete
# ===========================================================================

def test_asset_repository_deletes_asset(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    asset = repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    assert repository.get(
        asset.asset_id,
    ) is not None

    repository.delete(
        asset,
    )

    assert repository.get(
        asset.asset_id,
    ) is None

    assert repository.exists(
        asset.asset_id,
    ) is False


# ===========================================================================
# AssetRepository - Exists
# ===========================================================================

def test_asset_repository_exists(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    assert repository.exists(
        999999,
    ) is False

    asset = repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    assert repository.exists(
        asset.asset_id,
    ) is True


# ===========================================================================
# AssetRepository - Scene helpers
# ===========================================================================

def test_asset_repository_exists_for_scene(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    assert repository.exists_for_scene(
        scene.scene_id,
    ) is False

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    assert repository.exists_for_scene(
        scene.scene_id,
    ) is True


def test_asset_repository_count_for_scene(session):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    repository.create(
        create_asset(
            scene_id=scene.scene_id,
        ),
    )

    assert repository.count_for_scene(
        scene.scene_id,
    ) == 3


def test_asset_repository_count_is_zero_for_empty_scene(
    session,
):
    scene = create_test_scene(session)

    repository = AssetRepository(session)

    assert repository.count_for_scene(
        scene.scene_id,
    ) == 0