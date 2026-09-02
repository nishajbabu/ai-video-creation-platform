"""
Public schema interface for the Agentic Video Creation Backend.

This module exposes the schemas that are intended to be imported
directly by other application modules.
"""

from app.schemas.errors import (
    ErrorDetail,
    ErrorResponse,
)

from app.schemas.plan import (
    VideoPlan,
)

from app.schemas.requests import (
    VideoRequest,
)

from app.schemas.responses import (
    APIResponse,
)

from app.schemas.scene import (
    AssetRequirement,
    AudioRequirement,
    Scene,
)

from app.schemas.script import (
    Script,
    ScriptScene,
)

from app.schemas.storyboard import (
    Storyboard,
)

from app.schemas.video import (
    Video,
)


__all__ = [
    "APIResponse",
    "AssetRequirement",
    "AudioRequirement",
    "ErrorDetail",
    "ErrorResponse",
    "Scene",
    "Script",
    "ScriptScene",
    "Storyboard",
    "Video",
    "VideoPlan",
    "VideoRequest",
]