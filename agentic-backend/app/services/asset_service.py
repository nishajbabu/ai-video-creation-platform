"""
Asset application service.

This module contains business logic for managing generated-scene
assets.

Business rules live in this service while database persistence
is delegated to AssetRepository.
"""

from typing import List, Optional

from app.models.asset import AssetModel
from app.repositories.asset_repository import AssetRepository


class AssetService:
    """
    Application service responsible for asset operations.

    Business logic lives here.
    Database persistence is delegated to AssetRepository.
    """

    def __init__(
        self,
        repository: AssetRepository,
    ):
        """
        Initialize the asset service.
        """

        self.repository = repository

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_asset(
        self,
        asset: AssetModel,
    ) -> AssetModel:
        """
        Create and persist an asset.

        Raises:
            ValueError:
                If an asset with the same ID already exists.
        """

        if asset.asset_id is not None:
            if self.repository.exists(
                asset.asset_id,
            ):
                raise ValueError(
                    f"Asset '{asset.asset_id}' already exists."
                )

        return self.repository.create(
            asset,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_asset(
        self,
        asset_id: int,
    ) -> Optional[AssetModel]:
        """
        Return an asset by ID.

        Returns None when the asset does not exist.
        """

        return self.repository.get(
            asset_id,
        )

    def list_assets(self) -> List[AssetModel]:
        """
        Return all stored assets.
        """

        return self.repository.list()

    def get_assets_for_scene(
        self,
        scene_id: int,
    ) -> List[AssetModel]:
        """
        Return all assets belonging to a scene.
        """

        return self.repository.list_by_scene(
            scene_id,
        )

    def list_unassigned_assets(
        self,
    ) -> List[AssetModel]:
        """
        Return assets that are not assigned to a scene.
        """

        return self.repository.list_unassigned()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_asset(
        self,
        asset_id: int,
        *,
        asset_type: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[str] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        scene_id: Optional[int] = None,
    ) -> Optional[AssetModel]:
        """
        Update selected asset fields.

        Returns:
            Updated asset if found, otherwise None.
        """

        asset = self.repository.get(
            asset_id,
        )

        if asset is None:
            return None

        if asset_type is not None:
            asset.asset_type = asset_type

        if description is not None:
            asset.description = description

        if source is not None:
            asset.source = source

        if file_path is not None:
            asset.file_path = file_path

        if url is not None:
            asset.url = url

        if scene_id is not None:
            asset.scene_id = scene_id

        self.repository.update(
            asset,
        )

        return asset

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_asset(
        self,
        asset_id: int,
    ) -> bool:
        """
        Delete an asset.

        Returns:
            True if the asset existed and was deleted.
            False otherwise.
        """

        asset = self.repository.get(
            asset_id,
        )

        if asset is None:
            return False

        self.repository.delete(
            asset,
        )

        return True

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(
        self,
        asset_id: int,
    ) -> bool:
        """
        Check whether an asset exists.
        """

        return self.repository.exists(
            asset_id,
        )

    def exists_for_scene(
        self,
        scene_id: int,
    ) -> bool:
        """
        Check whether a scene has at least one asset.
        """

        return self.repository.exists_for_scene(
            scene_id,
        )

    def count_for_scene(
        self,
        scene_id: int,
    ) -> int:
        """
        Return the number of assets belonging to a scene.
        """

        return self.repository.count_for_scene(
            scene_id,
        )