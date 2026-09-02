"""
Database model registry.

Importing the models from this module ensures that all SQLAlchemy
models are registered with Base.metadata before database tables
are created.
"""

from app.models.asset import AssetModel
from app.models.project import ProjectModel
from app.models.scene import SceneModel
from app.models.video import VideoModel


__all__ = [
    "AssetModel",
    "ProjectModel",
    "SceneModel",
    "VideoModel",
]