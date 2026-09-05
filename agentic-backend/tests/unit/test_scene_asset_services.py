"""
Unit tests for SceneService and AssetService.

These tests verify application-service behavior using mocked
repositories. Database persistence is tested separately by the
repository integration tests.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.models.asset import AssetModel
from app.models.scene import SceneModel
from app.services.asset_service import AssetService
from app.services.scene_service import SceneService


# ===========================================================================
# Test helpers
# ===========================================================================

def create_scene(
    scene_id: int = 1,
    video_id: str = "video_001",
    order: int = 1,
) -> SceneModel:
    """
    Create a valid SceneModel for unit tests.
    """

    now = datetime.now(timezone.utc)

    return SceneModel(
        scene_id=scene_id,
        video_id=video_id,
        order=order,
        duration=10,
        purpose="Introduce the product.",
        narration="This is the product introduction.",
        visual_description="A modern product presentation.",
        visual_prompt="Professional product presentation.",
        visual_type="image",
        status="planned",
        has_asset_requirements=False,
        has_audio_requirements=False,
        created_at=now,
        updated_at=now,
    )


def create_asset(
    asset_id: int = 1,
    scene_id: int | None = 1,
) -> AssetModel:
    """
    Create a valid AssetModel for unit tests.
    """

    return AssetModel(
        asset_id=asset_id,
        scene_id=scene_id,
        asset_type="image",
        description="Product logo.",
        source="uploaded",
        file_path="/assets/logo.png",
        url=None,
        created_at=datetime.now(timezone.utc),
    )


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def scene_repository():
    """
    Create a mocked SceneRepository.
    """

    return Mock()


@pytest.fixture
def scene_service(scene_repository):
    """
    Create a SceneService using the mocked repository.
    """

    return SceneService(
        scene_repository,
    )


@pytest.fixture
def asset_repository():
    """
    Create a mocked AssetRepository.
    """

    return Mock()


@pytest.fixture
def asset_service(asset_repository):
    """
    Create an AssetService using the mocked repository.
    """

    return AssetService(
        asset_repository,
    )


# ===========================================================================
# SceneService
# ===========================================================================

def test_scene_service_can_be_created(
    scene_repository,
):
    service = SceneService(
        scene_repository,
    )

    assert service.repository is scene_repository


def test_scene_service_creates_scene(
    scene_service,
    scene_repository,
):
    scene = create_scene()

    scene_repository.create.return_value = scene

    result = scene_service.create_scene(
        scene,
    )

    assert result is scene

    scene_repository.create.assert_called_once_with(
        scene,
    )


def test_scene_service_gets_scene(
    scene_service,
    scene_repository,
):
    scene = create_scene()

    scene_repository.get.return_value = scene

    result = scene_service.get_scene(
        1,
    )

    assert result is scene

    scene_repository.get.assert_called_once_with(
        1,
    )


def test_scene_service_returns_none_for_missing_scene(
    scene_service,
    scene_repository,
):
    scene_repository.get.return_value = None

    result = scene_service.get_scene(
        999,
    )

    assert result is None

    scene_repository.get.assert_called_once_with(
        999,
    )


def test_scene_service_lists_scenes(
    scene_service,
    scene_repository,
):
    scenes = [
        create_scene(1, "video_001", 1),
        create_scene(2, "video_001", 2),
    ]

    scene_repository.list.return_value = scenes

    result = scene_service.list_scenes()

    assert result == scenes

    scene_repository.list.assert_called_once_with()


def test_scene_service_lists_scenes_for_video(
    scene_service,
    scene_repository,
):
    scenes = [
        create_scene(1, "video_001", 1),
        create_scene(2, "video_001", 2),
    ]

    scene_repository.list_by_video.return_value = scenes

    result = scene_service.list_scenes_for_video(
        "video_001",
    )

    assert result == scenes

    scene_repository.list_by_video.assert_called_once_with(
        "video_001",
    )


def test_scene_service_updates_scene(
    scene_service,
    scene_repository,
):
    scene = create_scene()

    scene_repository.get.return_value = scene
    scene_repository.update.return_value = scene

    result = scene_service.update_scene(
        1,
        purpose="Updated purpose.",
        narration="Updated narration.",
        visual_description="Updated visual.",
        visual_prompt="Updated prompt.",
        visual_type="video",
        status="rendering",
        duration=20,
        order=2,
    )

    assert result is scene
    assert scene.purpose == "Updated purpose."
    assert scene.narration == "Updated narration."
    assert scene.visual_description == "Updated visual."
    assert scene.visual_prompt == "Updated prompt."
    assert scene.visual_type == "video"
    assert scene.status == "rendering"
    assert scene.duration == 20
    assert scene.order == 2

    scene_repository.get.assert_called_once_with(
        1,
    )

    scene_repository.update.assert_called_once_with(
        scene,
    )


def test_scene_service_returns_none_when_updating_missing_scene(
    scene_service,
    scene_repository,
):
    scene_repository.get.return_value = None

    result = scene_service.update_scene(
        999,
        purpose="Updated",
    )

    assert result is None

    scene_repository.get.assert_called_once_with(
        999,
    )

    scene_repository.update.assert_not_called()


def test_scene_service_deletes_scene(
    scene_service,
    scene_repository,
):
    scene = create_scene()

    scene_repository.get.return_value = scene

    result = scene_service.delete_scene(
        1,
    )

    assert result is True

    scene_repository.get.assert_called_once_with(
        1,
    )

    scene_repository.delete.assert_called_once_with(
        scene,
    )


def test_scene_service_delete_missing_scene_returns_false(
    scene_service,
    scene_repository,
):
    scene_repository.get.return_value = None

    result = scene_service.delete_scene(
        999,
    )

    assert result is False

    scene_repository.get.assert_called_once_with(
        999,
    )

    scene_repository.delete.assert_not_called()


def test_scene_service_checks_existence(
    scene_service,
    scene_repository,
):
    scene_repository.exists.return_value = True

    result = scene_service.exists(
        1,
    )

    assert result is True

    scene_repository.exists.assert_called_once_with(
        1,
    )


def test_scene_service_checks_video_scenes(
    scene_service,
    scene_repository,
):
    scene_repository.exists_for_video.return_value = True

    result = scene_service.has_scenes_for_video(
        "video_001",
    )

    assert result is True

    scene_repository.exists_for_video.assert_called_once_with(
        "video_001",
    )


def test_scene_service_counts_video_scenes(
    scene_service,
    scene_repository,
):
    scene_repository.count_for_video.return_value = 3

    result = scene_service.count_scenes_for_video(
        "video_001",
    )

    assert result == 3

    scene_repository.count_for_video.assert_called_once_with(
        "video_001",
    )


# ===========================================================================
# AssetService
# ===========================================================================

def test_asset_service_can_be_created(
    asset_repository,
):
    service = AssetService(
        asset_repository,
    )

    assert service.repository is asset_repository


def test_asset_service_creates_asset(
    asset_service,
    asset_repository,
):
    asset = create_asset()

    asset_repository.exists.return_value = False
    asset_repository.create.return_value = asset

    result = asset_service.create_asset(
        asset,
    )

    assert result is asset

    asset_repository.create.assert_called_once_with(
        asset,
    )


def test_asset_service_rejects_duplicate_asset(
    asset_service,
    asset_repository,
):
    asset = create_asset(
        asset_id=1,
    )

    asset_repository.exists.return_value = True

    with pytest.raises(
        ValueError,
        match="Asset '1' already exists.",
    ):
        asset_service.create_asset(
            asset,
        )

    asset_repository.create.assert_not_called()


def test_asset_service_creates_asset_without_existing_id(
    asset_service,
    asset_repository,
):
    asset = create_asset(
        asset_id=None,
    )

    asset_repository.create.return_value = asset

    result = asset_service.create_asset(
        asset,
    )

    assert result is asset

    asset_repository.exists.assert_not_called()

    asset_repository.create.assert_called_once_with(
        asset,
    )


def test_asset_service_gets_asset(
    asset_service,
    asset_repository,
):
    asset = create_asset()

    asset_repository.get.return_value = asset

    result = asset_service.get_asset(
        1,
    )

    assert result is asset

    asset_repository.get.assert_called_once_with(
        1,
    )


def test_asset_service_returns_none_for_missing_asset(
    asset_service,
    asset_repository,
):
    asset_repository.get.return_value = None

    result = asset_service.get_asset(
        999,
    )

    assert result is None

    asset_repository.get.assert_called_once_with(
        999,
    )


def test_asset_service_lists_assets(
    asset_service,
    asset_repository,
):
    assets = [
        create_asset(1),
        create_asset(2),
    ]

    asset_repository.list.return_value = assets

    result = asset_service.list_assets()

    assert result == assets

    asset_repository.list.assert_called_once_with()


def test_asset_service_gets_assets_for_scene(
    asset_service,
    asset_repository,
):
    assets = [
        create_asset(1, 1),
        create_asset(2, 1),
    ]

    asset_repository.list_by_scene.return_value = assets

    result = asset_service.get_assets_for_scene(
        1,
    )

    assert result == assets

    asset_repository.list_by_scene.assert_called_once_with(
        1,
    )


def test_asset_service_lists_unassigned_assets(
    asset_service,
    asset_repository,
):
    assets = [
        create_asset(1, None),
        create_asset(2, None),
    ]

    asset_repository.list_unassigned.return_value = assets

    result = asset_service.list_unassigned_assets()

    assert result == assets

    asset_repository.list_unassigned.assert_called_once_with()


def test_asset_service_updates_asset(
    asset_service,
    asset_repository,
):
    asset = create_asset()

    asset_repository.get.return_value = asset
    asset_repository.update.return_value = asset

    result = asset_service.update_asset(
        1,
        asset_type="video",
        description="Updated asset.",
        source="generated",
        file_path="/assets/updated.mp4",
        url="https://example.com/asset",
        scene_id=2,
    )

    assert result is asset
    assert asset.asset_type == "video"
    assert asset.description == "Updated asset."
    assert asset.source == "generated"
    assert asset.file_path == "/assets/updated.mp4"
    assert asset.url == "https://example.com/asset"
    assert asset.scene_id == 2

    asset_repository.get.assert_called_once_with(
        1,
    )

    asset_repository.update.assert_called_once_with(
        asset,
    )


def test_asset_service_returns_none_when_updating_missing_asset(
    asset_service,
    asset_repository,
):
    asset_repository.get.return_value = None

    result = asset_service.update_asset(
        999,
        description="Updated",
    )

    assert result is None

    asset_repository.get.assert_called_once_with(
        999,
    )

    asset_repository.update.assert_not_called()


def test_asset_service_deletes_asset(
    asset_service,
    asset_repository,
):
    asset = create_asset()

    asset_repository.get.return_value = asset

    result = asset_service.delete_asset(
        1,
    )

    assert result is True

    asset_repository.get.assert_called_once_with(
        1,
    )

    asset_repository.delete.assert_called_once_with(
        asset,
    )


def test_asset_service_delete_missing_asset_returns_false(
    asset_service,
    asset_repository,
):
    asset_repository.get.return_value = None

    result = asset_service.delete_asset(
        999,
    )

    assert result is False

    asset_repository.get.assert_called_once_with(
        999,
    )

    asset_repository.delete.assert_not_called()


def test_asset_service_checks_existence(
    asset_service,
    asset_repository,
):
    asset_repository.exists.return_value = True

    result = asset_service.exists(
        1,
    )

    assert result is True

    asset_repository.exists.assert_called_once_with(
        1,
    )


def test_asset_service_checks_scene_assets(
    asset_service,
    asset_repository,
):
    asset_repository.exists_for_scene.return_value = True

    result = asset_service.exists_for_scene(
        1,
    )

    assert result is True

    asset_repository.exists_for_scene.assert_called_once_with(
        1,
    )


def test_asset_service_counts_scene_assets(
    asset_service,
    asset_repository,
):
    asset_repository.count_for_scene.return_value = 4

    result = asset_service.count_for_scene(
        1,
    )

    assert result == 4

    asset_repository.count_for_scene.assert_called_once_with(
        1,
    )