"""
Asset database repository.

This module contains database-specific operations for AssetModel.

The repository is responsible only for persistence. Business rules
remain in the service layer.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.asset import AssetModel


class AssetRepository:
    """
    Repository responsible for AssetModel persistence.
    """

    def __init__(
        self,
        session: Session,
    ):
        """
        Initialize the repository with a SQLAlchemy session.
        """

        self.session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        asset: AssetModel,
    ) -> AssetModel:
        """
        Persist a new asset.
        """

        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)

        return asset

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(
        self,
        asset_id: int,
    ) -> Optional[AssetModel]:
        """
        Return an asset by its database ID.

        Returns None when the asset does not exist.
        """

        return (
            self.session.query(AssetModel)
            .filter(
                AssetModel.asset_id == asset_id,
            )
            .first()
        )

    def list(self) -> List[AssetModel]:
        """
        Return all assets ordered by creation time.
        """

        return (
            self.session.query(AssetModel)
            .order_by(
                AssetModel.created_at,
            )
            .all()
        )

    def list_by_scene(
        self,
        scene_id: int,
    ) -> List[AssetModel]:
        """
        Return all assets belonging to a scene.
        """

        return (
            self.session.query(AssetModel)
            .filter(
                AssetModel.scene_id == scene_id,
            )
            .order_by(
                AssetModel.created_at,
            )
            .all()
        )

    def list_unassigned(self) -> List[AssetModel]:
        """
        Return assets that are not currently assigned to a scene.
        """

        return (
            self.session.query(AssetModel)
            .filter(
                AssetModel.scene_id.is_(None),
            )
            .order_by(
                AssetModel.created_at,
            )
            .all()
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        asset: AssetModel,
    ) -> AssetModel:
        """
        Persist changes made to an existing asset.
        """

        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)

        return asset

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        asset: AssetModel,
    ) -> None:
        """
        Delete an asset from the database.
        """

        self.session.delete(asset)
        self.session.commit()

    # ------------------------------------------------------------------
    # Existence
    # ------------------------------------------------------------------

    def exists(
        self,
        asset_id: int,
    ) -> bool:
        """
        Return whether an asset exists.
        """

        return (
            self.session.query(AssetModel)
            .filter(
                AssetModel.asset_id == asset_id,
            )
            .first()
            is not None
        )

    def exists_for_scene(
        self,
        scene_id: int,
    ) -> bool:
        """
        Return whether at least one asset exists for a scene.
        """

        return (
            self.session.query(AssetModel)
            .filter(
                AssetModel.scene_id == scene_id,
            )
            .first()
            is not None
        )

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def count_for_scene(
        self,
        scene_id: int,
    ) -> int:
        """
        Return the number of assets belonging to a scene.
        """

        return (
            self.session.query(AssetModel)
            .filter(
                AssetModel.scene_id == scene_id,
            )
            .count()
        )