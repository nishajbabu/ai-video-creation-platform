import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import Base
from app.models import (
    AssetModel,
    ProjectModel,
    SceneModel,
    VideoModel,
)


# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
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

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(
        bind=engine,
    )


# ---------------------------------------------------------------------------
# ProjectModel tests
# ---------------------------------------------------------------------------

def test_project_model_table_name():
    assert ProjectModel.__tablename__ == "projects"


def test_project_model_columns():
    columns = set(
        ProjectModel.__table__.columns.keys()
    )

    expected = {
        "project_id",
        "name",
        "description",
        "status",
        "created_at",
        "updated_at",
    }

    assert expected.issubset(columns)


def test_project_model_can_be_persisted(db_session):
    from datetime import datetime, timezone

    project = ProjectModel(
        project_id="proj_001",
        name="AI Product Video",
        description="Product introduction project.",
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_session.add(project)
    db_session.commit()

    result = db_session.get(
        ProjectModel,
        "proj_001",
    )

    assert result is not None
    assert result.project_id == "proj_001"
    assert result.name == "AI Product Video"
    assert result.status == "draft"


# ---------------------------------------------------------------------------
# VideoModel tests
# ---------------------------------------------------------------------------

def test_video_model_table_name():
    assert VideoModel.__tablename__ == "videos"


def test_video_model_columns():
    columns = set(
        VideoModel.__table__.columns.keys()
    )

    expected = {
        "video_id",
        "project_id",
        "title",
        "duration",
        "status",
        "resolution",
        "fps",
        "file_path",
        "thumbnail_path",
        "created_at",
    }

    assert expected.issubset(columns)


def test_video_model_has_project_foreign_key():
    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in (
            VideoModel.__table__
            .columns["project_id"]
            .foreign_keys
        )
    }

    assert "projects.project_id" in foreign_keys


def test_video_model_can_be_persisted(db_session):
    from datetime import datetime, timezone

    project = ProjectModel(
        project_id="proj_001",
        name="AI Product Video",
        description="Product introduction.",
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    video = VideoModel(
        video_id="video_001",
        project_id="proj_001",
        title="Product Introduction",
        duration=60,
        status="queued",
        resolution="1920x1080",
        fps=30,
        created_at=datetime.now(timezone.utc),
    )

    db_session.add(project)
    db_session.add(video)
    db_session.commit()

    result = db_session.get(
        VideoModel,
        "video_001",
    )

    assert result is not None
    assert result.project_id == "proj_001"
    assert result.duration == 60
    assert result.status == "queued"


# ---------------------------------------------------------------------------
# SceneModel tests
# ---------------------------------------------------------------------------

def test_scene_model_table_name():
    assert SceneModel.__tablename__ == "scenes"


def test_scene_model_columns():
    columns = set(
        SceneModel.__table__.columns.keys()
    )

    expected = {
        "scene_id",
        "video_id",
        "order",
        "duration",
        "purpose",
        "narration",
        "visual_description",
        "visual_prompt",
        "visual_type",
        "status",
        "has_asset_requirements",
        "has_audio_requirements",
        "created_at",
        "updated_at",
    }

    assert expected.issubset(columns)


def test_scene_model_has_video_foreign_key():
    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in (
            SceneModel.__table__
            .columns["video_id"]
            .foreign_keys
        )
    }

    assert "videos.video_id" in foreign_keys


def test_scene_model_can_be_persisted(db_session):
    from datetime import datetime, timezone

    project = ProjectModel(
        project_id="proj_001",
        name="AI Product Video",
        description="Product introduction.",
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    video = VideoModel(
        video_id="video_001",
        project_id="proj_001",
        title="Product Introduction",
        duration=60,
        created_at=datetime.now(timezone.utc),
    )

    scene = SceneModel(
        video_id="video_001",
        order=1,
        duration=10,
        purpose="Introduce the product",
        narration="Welcome to our AI product.",
        visual_description="AI product interface.",
        visual_prompt="Modern AI SaaS interface.",
        visual_type="image",
        status="planned",
    )

    db_session.add(project)
    db_session.add(video)
    db_session.add(scene)
    db_session.commit()

    result = db_session.get(
        SceneModel,
        scene.scene_id,
    )

    assert result is not None
    assert result.video_id == "video_001"
    assert result.order == 1
    assert result.duration == 10
    assert result.status == "planned"


# ---------------------------------------------------------------------------
# AssetModel tests
# ---------------------------------------------------------------------------

def test_asset_model_table_name():
    assert AssetModel.__tablename__ == "assets"


def test_asset_model_columns():
    columns = set(
        AssetModel.__table__.columns.keys()
    )

    expected = {
        "asset_id",
        "scene_id",
        "asset_type",
        "description",
        "source",
        "file_path",
        "url",
        "created_at",
    }

    assert expected.issubset(columns)


def test_asset_model_has_scene_foreign_key():
    foreign_keys = {
        foreign_key.target_fullname
        for foreign_key in (
            AssetModel.__table__
            .columns["scene_id"]
            .foreign_keys
        )
    }

    assert "scenes.scene_id" in foreign_keys


def test_asset_model_can_be_persisted(db_session):
    from datetime import datetime, timezone

    project = ProjectModel(
        project_id="proj_001",
        name="AI Product Video",
        description="Product introduction.",
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    video = VideoModel(
        video_id="video_001",
        project_id="proj_001",
        title="Product Introduction",
        duration=60,
        created_at=datetime.now(timezone.utc),
    )

    scene = SceneModel(
        video_id="video_001",
        order=1,
        duration=10,
        purpose="Introduce the product",
        narration="Welcome to our AI product.",
        visual_description="AI product interface.",
        visual_prompt="Modern AI SaaS interface.",
        visual_type="image",
        status="planned",
    )

    asset = AssetModel(
        scene_id=None,
        asset_type="logo",
        description="Company logo",
        source="user_upload",
        file_path="uploads/logo.png",
    )

    db_session.add(project)
    db_session.add(video)
    db_session.add(scene)
    db_session.flush()

    asset.scene_id = scene.scene_id

    db_session.add(asset)
    db_session.commit()

    result = db_session.get(
        AssetModel,
        asset.asset_id,
    )

    assert result is not None
    assert result.scene_id == scene.scene_id
    assert result.asset_type == "logo"
    assert result.source == "user_upload"
    assert result.file_path == "uploads/logo.png"


# ---------------------------------------------------------------------------
# Complete relationship chain
# ---------------------------------------------------------------------------

def test_complete_project_video_scene_asset_chain(db_session):
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    project = ProjectModel(
        project_id="proj_chain",
        name="Complete Workflow",
        description="End-to-end database relationship test.",
        status="draft",
        created_at=now,
        updated_at=now,
    )

    video = VideoModel(
        video_id="video_chain",
        project_id="proj_chain",
        title="Complete Video",
        duration=60,
        created_at=now,
    )

    scene = SceneModel(
        video_id="video_chain",
        order=1,
        duration=10,
        purpose="Opening scene",
        narration="Welcome.",
        visual_description="Opening product shot.",
        visual_prompt="Professional product presentation.",
        visual_type="image",
        status="planned",
    )

    db_session.add(project)
    db_session.add(video)
    db_session.add(scene)
    db_session.flush()

    asset = AssetModel(
        scene_id=scene.scene_id,
        asset_type="logo",
        description="Product logo",
        source="user_upload",
        file_path="uploads/logo.png",
    )

    db_session.add(asset)
    db_session.commit()

    stored_project = db_session.get(
        ProjectModel,
        "proj_chain",
    )

    stored_video = db_session.get(
        VideoModel,
        "video_chain",
    )

    stored_scene = db_session.get(
        SceneModel,
        scene.scene_id,
    )

    stored_asset = db_session.get(
        AssetModel,
        asset.asset_id,
    )

    assert stored_project is not None
    assert stored_video is not None
    assert stored_scene is not None
    assert stored_asset is not None

    assert stored_video.project_id == stored_project.project_id
    assert stored_scene.video_id == stored_video.video_id
    assert stored_asset.scene_id == stored_scene.scene_id