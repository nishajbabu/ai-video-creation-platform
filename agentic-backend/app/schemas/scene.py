from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


VisualType = Literal[
    "image",
    "video",
    "animation",
    "stock",
    "user_asset",
]

SceneStatus = Literal[
    "planned",
    "assets_pending",
    "ready",
    "failed",
]


class AssetRequirement(BaseModel):
    """
    Describes an asset that a scene requires.

    This is a requirement, not the generated asset itself.
    The media/asset module will use this information to retrieve
    or generate the actual asset.
    """

    asset_type: Literal[
        "image",
        "video",
        "document",
        "logo",
        "other",
    ]

    description: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Description of the required asset.",
    )

    source: Literal[
        "ai",
        "library",
        "user_upload",
        "rag",
        "ai_or_library",
    ] = Field(
        default="ai_or_library",
        description="Expected source of the asset.",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("asset description must not be blank")

        return value


class AudioRequirement(BaseModel):
    """
    Describes the audio requirements for a scene.

    The actual audio generation is handled by the downstream
    audio/TTS module.
    """

    required: bool = True

    voice_style: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Desired voice characteristics.",
    )

    background_music: bool = Field(
        default=False,
        description="Whether background music is required.",
    )


class Scene(BaseModel):
    """
    Shared scene contract produced by the Storyboard Agent.

    This object is consumed by downstream modules such as:
    - RAG / asset retrieval
    - AI image/video generation
    - TTS/audio generation
    - Video editor
    - Frontend
    """

    scene_id: int = Field(
        ...,
        ge=1,
        description="Stable unique identifier for the scene.",
    )

    order: int = Field(
        ...,
        ge=1,
        description="Position of the scene in the final video.",
    )

    duration: int = Field(
        ...,
        ge=1,
        le=600,
        description="Target duration of the scene in seconds.",
    )

    purpose: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Purpose of the scene within the video.",
    )

    narration: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Narration associated with this scene.",
    )

    visual_description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Human-readable description of what should be shown.",
    )

    visual_prompt: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="Prompt that can be passed to a visual-generation system.",
    )

    visual_type: VisualType = Field(
        default="image",
        description="Type of visual content required.",
    )

    text_overlay: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional text that should appear on screen.",
    )

    asset_requirements: List[AssetRequirement] = Field(
        default_factory=list,
        description="Assets required to construct the scene.",
    )

    knowledge_requirements: List[str] = Field(
        default_factory=list,
        description="Information that may need to be retrieved from documents/RAG.",
    )

    audio_requirements: AudioRequirement = Field(
        default_factory=AudioRequirement,
        description="Audio/TTS requirements for the scene.",
    )

    transition: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Transition to use after this scene.",
    )

    status: SceneStatus = Field(
        default="planned",
        description="Current preparation status of the scene.",
    )

    @field_validator(
        "purpose",
        "narration",
        "visual_description",
        "visual_prompt",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("text fields must not be blank")

        return value

    @field_validator("knowledge_requirements")
    @classmethod
    def validate_knowledge_requirements(
        cls,
        values: List[str],
    ) -> List[str]:
        cleaned_values = []

        for value in values:
            value = value.strip()

            if not value:
                raise ValueError(
                    "knowledge requirements must not contain blank values"
                )

            cleaned_values.append(value)

        return cleaned_values