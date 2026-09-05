"""
Unit tests for AssetService.

These tests verify asset business logic independently from the
database by using a mocked repository.
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.models.asset import AssetModel
from app.services.asset_service import AssetService


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def create_asset(
    asset_id: int | None = None,
    scene_id: int | None = 1,
) -> AssetModel:
    """
    Create a valid AssetModel for unit tests.
    """

    return AssetModel(
        asset_id=asset_id,
        scene_id=scene_id,
        asset_type="image",
        description="Product image.",
        source="library",
        file_path=None,
        url=None,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repository():
    """
    Provide a mocked AssetRepository.
    """

    return Mock()


@pytest.fixture
def service(repository):
    """
    Create AssetService with the mocked repository.
    """

    return AssetService(
        repository=repository,
    )


# ===========================================================================
# Create
# ===========================================================================

def test_asset_service_can_be_created(repository):
    service = AssetService(
        repository=repository,
    )

    assert service is not None
    assert service.repository is repository


def test_asset_service_creates_asset(
    service,
    repository,
):
    asset = create_asset()

    repository.create.return_value = asset

    result = service.create_asset(
        asset,
    )

    assert result is asset

    repository.create.assert_called_once_with(
        asset,
    )


def test_asset_service_rejects_duplicate_asset(
    service,
    repository,
):
    asset = create_asset(
        asset_id=1,
    )

    repository.exists.return_value = True

    with pytest.raises(
        ValueError,
        match="Asset '1' already exists.",
    ):
        service.create_asset(
            asset,
        )

    repository.create.assert_not_called()


def test_asset_service_allows_new_asset_without_id(
    service,
    repository,
):
    asset = create_asset(
        asset_id=None,
    )

    repository.create.return_value = asset

    result = service.create_asset(
        asset,
    )

    assert result is asset

    repository.exists.assert_not_called()
    repository.create.assert_called_once_with(
        asset,
    )


# ===========================================================================
# Read
# ===========================================================================

def test_asset_service_gets_asset(
    service,
    repository,
):
    asset = create_asset(
        asset_id=1,
    )

    repository.get.return_value = asset

    result = service.get_asset(
        1,
    )

    assert result is asset

    repository.get.assert_called_once_with(
        1,
    )


def test_asset_service_returns_none_for_missing_asset(
    service,
    repository,
):
    repository.get.return_value = None

    result = service.get_asset(
        999,
    )

    assert result is None

    repository.get.assert_called_once_with(
        999,
    )


def test_asset_service_lists_assets(
    service,
    repository,
):
    assets = [
        create_asset(1),
        create_asset(2),
    ]

    repository.list.return_value = assets

    result = service.list_assets()

    assert result == assets

    repository.list.assert_called_once_with()


def test_asset_service_gets_assets_for_scene(
    service,
    repository,
):
    assets = [
        create_asset(1, scene_id=10),
        create_asset(2, scene_id=10),
    ]

    repository.list_by_scene.return_value = assets

    result = service.get_assets_for_scene(
        10,
    )

    assert result == assets

    repository.list_by_scene.assert_called_once_with(
        10,
    )


def test_asset_service_lists_unassigned_assets(
    service,
    repository,
):
    assets = [
        create_asset(1, scene_id=None),
        create_asset(2, scene_id=None),
    ]

    repository.list_unassigned.return_value = assets

    result = service.list_unassigned_assets()

    assert result == assets

    repository.list_unassigned.assert_called_once_with()


# ===========================================================================
# Update
# ===========================================================================

def test_asset_service_updates_asset(
    service,
    repository,
):
    asset = create_asset(
        asset_id=1,
        scene_id=10,
    )

    repository.get.return_value = asset
    repository.update.return_value = asset

    result = service.update_asset(
        1,
        asset_type="logo",
        description="Updated logo.",
        source="upload",
        file_path="/assets/logo.png",
        url="https://example.com/logo.png",
    )

    assert result is asset
    assert asset.asset_type == "logo"
    assert asset.description == "Updated logo."
    assert asset.source == "upload"
    assert asset.file_path == "/assets/logo.png"
    assert asset.url == "https://example.com/logo.png"

    repository.get.assert_called_once_with(
        1,
    )

    repository.update.assert_called_once_with(
        asset,
    )


def test_asset_service_updates_only_supplied_fields(
    service,
    repository,
):
    asset = create_asset(
        asset_id=1,
        scene_id=10,
    )

    repository.get.return_value = asset

    service.update_asset(
        1,
        description="New description.",
    )

    assert asset.description == "New description."

    assert asset.asset_type == "image"
    assert asset.source == "library"
    assert asset.file_path is None
    assert asset.url is None
    assert asset.scene_id == 10

    repository.update.assert_called_once_with(
        asset,
    )


def test_asset_service_updates_scene(
    service,
    repository,
):
    asset = create_asset(
        asset_id=1,
        scene_id=10,
    )

    repository.get.return_value = asset

    result = service.update_asset(
        1,
        scene_id=20,
    )

    assert result.scene_id == 20

    repository.update.assert_called_once_with(
        asset,
    )


def test_asset_service_returns_none_when_updating_missing_asset(
    service,
    repository,
):
    repository.get.return_value = None

    result = service.update_asset(
        999,
        description="Does not exist.",
    )

    assert result is None

    repository.update.assert_not_called()


# ===========================================================================
# Delete
# ===========================================================================

def test_asset_service_deletes_asset(
    service,
    repository,
):
    asset = create_asset(
        asset_id=1,
    )

    repository.get.return_value = asset

    result = service.delete_asset(
        1,
    )

    assert result is True

    repository.get.assert_called_once_with(
        1,
    )

    repository.delete.assert_called_once_with(
        asset,
    )


def test_asset_service_delete_missing_asset_returns_false(
    service,
    repository,
):
    repository.get.return_value = None

    result = service.delete_asset(
        999,
    )

    assert result is False

    repository.delete.assert_not_called()


# ===========================================================================
# Utility
# ===========================================================================

def test_asset_service_checks_asset_exists(
    service,
    repository,
):
    repository.exists.return_value = True

    result = service.exists(
        1,
    )

    assert result is True

    repository.exists.assert_called_once_with(
        1,
    )


def test_asset_service_checks_assets_for_scene(
    service,
    repository,
):
    repository.exists_for_scene.return_value = True

    result = service.exists_for_scene(
        10,
    )

    assert result is True

    repository.exists_for_scene.assert_called_once_with(
        10,
    )


def test_asset_service_counts_assets_for_scene(
    service,
    repository,
):
    repository.count_for_scene.return_value = 3

    result = service.count_for_scene(
        10,
    )

    assert result == 3

    repository.count_for_scene.assert_called_once_with(
        10,
    )