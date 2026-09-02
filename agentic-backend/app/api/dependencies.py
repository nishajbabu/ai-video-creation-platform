"""
FastAPI dependency providers.

This module exposes shared application dependencies to API routes.

Dependency flow:

    Environment
        ↓
    LLMConfig
        ↓
    KeyManager
        ↓
    LLMService
        ↓
    Orchestrator
        ↓
    GenerationService


    Database Session
        ↓
    Repository
        ↓
    Application Service
"""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import Orchestrator
from app.core.startup import initialize_llm_environment
from app.db.session import get_db
from app.llm.config import LLMConfig
from app.llm.key_manager import KeyManager
from app.llm.service import LLMService
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.scene_repository import SceneRepository
from app.repositories.video_repository import VideoRepository
from app.services.asset_service import AssetService
from app.services.generation_service import GenerationService
from app.services.project_service import ProjectService
from app.services.video_service import VideoService


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm_config() -> LLMConfig:
    """
    Return the application's shared LLM configuration.
    """

    initialize_llm_environment()

    return LLMConfig()


# ---------------------------------------------------------------------------
# LLM key manager
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm_key_manager() -> KeyManager:
    """
    Return the application's shared LLM key manager.
    """

    config = get_llm_config()

    return KeyManager(
        config.get_keys(),
    )


# ---------------------------------------------------------------------------
# LLM service
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """
    Return the application's shared LLM service.
    """

    key_manager = get_llm_key_manager()

    return LLMService(
        key_manager,
    )


# ---------------------------------------------------------------------------
# Project service
# ---------------------------------------------------------------------------

def get_project_service(
    db: Session = Depends(get_db),
) -> ProjectService:
    """
    Provide ProjectService backed by the current database session.
    """

    repository = ProjectRepository(
        db,
    )

    return ProjectService(
        repository,
    )


# ---------------------------------------------------------------------------
# Video service
# ---------------------------------------------------------------------------

def get_video_service(
    db: Session = Depends(get_db),
) -> VideoService:
    """
    Provide VideoService backed by the current database session.
    """

    repository = VideoRepository(
        db,
    )

    return VideoService(
        repository,
    )


# ---------------------------------------------------------------------------
# Scene repository
# ---------------------------------------------------------------------------

def get_scene_repository(
    db: Session = Depends(get_db),
) -> SceneRepository:
    """
    Provide SceneRepository backed by the current database session.
    """

    return SceneRepository(
        db,
    )


# ---------------------------------------------------------------------------
# Asset service
# ---------------------------------------------------------------------------

def get_asset_service(
    db: Session = Depends(get_db),
) -> AssetService:
    """
    Provide AssetService backed by the current database session.
    """

    repository = AssetRepository(
        db,
    )

    return AssetService(
        repository,
    )


# ---------------------------------------------------------------------------
# Generation service
# ---------------------------------------------------------------------------

def get_generation_service(
    llm_service: LLMService = Depends(
        get_llm_service,
    ),
) -> GenerationService:
    """
    Provide GenerationService backed by the shared LLM service.

    The shared LLMService is injected into the Orchestrator.

    The Orchestrator then shares the same LLMService with:
        - PlannerAgent
        - ScriptAgent
        - StoryboardAgent
    """

    orchestrator = Orchestrator(
        llm_service=llm_service,
    )

    return GenerationService(
        orchestrator=orchestrator,
    )


# ---------------------------------------------------------------------------
# Dependency cache management
# ---------------------------------------------------------------------------

def clear_dependency_cache() -> None:
    """
    Clear cached LLM dependencies.

    This is primarily useful for:

        - automated tests
        - configuration reloads
        - controlled application reinitialization
    """

    get_llm_service.cache_clear()
    get_llm_key_manager.cache_clear()
    get_llm_config.cache_clear()