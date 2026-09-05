"""
Integration tests for the FastAPI application.

These tests verify the public API behavior through HTTP requests.

Project and video endpoints use the database-backed service layer.

Generation endpoint tests use a deterministic test generation service
so that integration tests do not make real external LLM requests.

The API tests use an isolated in-memory SQLite database so tests
never modify the development database.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_generation_service
from app.db.database import Base
from app.db.session import get_db
from app.main import app
from app.models.project import ProjectModel
from app.models.video import VideoModel


# ---------------------------------------------------------------------------
# Test generation service
# ---------------------------------------------------------------------------

class TestGenerationService:
    """
    Deterministic generation service used by API integration tests.

    The real GenerationService may invoke external LLM providers.
    Integration tests should verify the API contract without depending
    on external provider availability, quotas, credentials, or latency.
    """

    def start_generation(
        self,
        request,
    ) -> dict:
        """
        Return a deterministic completed generation result.
        """

        return {
            "workflow_id": "test_workflow_001",
            "status": "completed",
            "request": request.model_dump(),
            "plan": {
                "objective": "Test video generation plan.",
                "target_audience": request.target_audience,
                "tone": request.tone,
                "style": request.style,
                "duration": request.duration,
                "scene_count": 3,
                "content_requirements": [],
                "generation_notes": [],
            },
            "script": {
                "scenes": [
                    {
                        "scene_id": 1,
                        "purpose": "Introduce the video topic.",
                        "duration": 20,
                        "narration": "This is the introduction.",
                    },
                    {
                        "scene_id": 2,
                        "purpose": "Explain the main topic.",
                        "duration": 20,
                        "narration": "This explains the main topic.",
                    },
                    {
                        "scene_id": 3,
                        "purpose": "Conclude the video.",
                        "duration": 20,
                        "narration": "This concludes the video.",
                    },
                ],
            },
            "storyboard": {
                "scenes": [
                    {
                        "scene_id": 1,
                        "order": 1,
                        "duration": 20,
                        "purpose": "Introduce the video topic.",
                        "narration": "This is the introduction.",
                        "visual_description": "Introduction visual.",
                        "visual_prompt": (
                            "Create an introduction visual."
                        ),
                        "visual_type": "image",
                        "text_overlay": None,
                        "asset_requirements": [
                            {
                                "asset_type": "image",
                                "description": (
                                    "Introduction image."
                                ),
                                "source": "ai_or_library",
                            }
                        ],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": (
                                "clear and professional"
                            ),
                            "background_music": False,
                        },
                        "transition": "fade",
                        "status": "planned",
                    },
                    {
                        "scene_id": 2,
                        "order": 2,
                        "duration": 20,
                        "purpose": "Explain the main topic.",
                        "narration": "This explains the main topic.",
                        "visual_description": "Main topic visual.",
                        "visual_prompt": (
                            "Create a main topic visual."
                        ),
                        "visual_type": "image",
                        "text_overlay": None,
                        "asset_requirements": [
                            {
                                "asset_type": "image",
                                "description": (
                                    "Main topic image."
                                ),
                                "source": "ai_or_library",
                            }
                        ],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": (
                                "clear and professional"
                            ),
                            "background_music": False,
                        },
                        "transition": "crossfade",
                        "status": "planned",
                    },
                    {
                        "scene_id": 3,
                        "order": 3,
                        "duration": 20,
                        "purpose": "Conclude the video.",
                        "narration": "This concludes the video.",
                        "visual_description": "Conclusion visual.",
                        "visual_prompt": (
                            "Create a conclusion visual."
                        ),
                        "visual_type": "image",
                        "text_overlay": None,
                        "asset_requirements": [
                            {
                                "asset_type": "image",
                                "description": (
                                    "Conclusion image."
                                ),
                                "source": "ai_or_library",
                            }
                        ],
                        "knowledge_requirements": [],
                        "audio_requirements": {
                            "required": True,
                            "voice_style": (
                                "clear and professional"
                            ),
                            "background_music": False,
                        },
                        "transition": None,
                        "status": "planned",
                    },
                ],
            },
            "error": None,
        }


# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """
    Create an isolated in-memory SQLite database for one test.

    StaticPool ensures that the same SQLite connection is reused
    across FastAPI/TestClient execution.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(
        bind=engine,
    )

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()

        Base.metadata.drop_all(
            bind=engine,
        )

        engine.dispose()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------

@pytest.fixture
def client(db_session):
    """
    Create a TestClient using the isolated test database.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[
        get_db
    ] = override_get_db

    app.dependency_overrides[
        get_generation_service
    ] = lambda: TestGenerationService()

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

def create_project_payload(
    project_id: str = "api_project_001",
) -> dict:
    """
    Create a valid project payload for API tests.
    """

    return {
        "project_id": project_id,
        "name": "API Integration Test Project",
        "description": (
            "Project created during API integration testing."
        ),
        "status": "draft",
    }


def create_generation_payload() -> dict:
    """
    Create a valid VideoRequest payload.

    VideoRequest requires the complete set of generation fields,
    not only the prompt.
    """

    return {
        "prompt": (
            "Create a professional AI product introduction video."
        ),
        "duration": 60,
        "style": "professional",
        "target_audience": "Potential customers",
        "tone": "confident",
    }


def create_project_model(
    project_id: str = "api_project_001",
) -> ProjectModel:
    """
    Create a valid ProjectModel for database-backed API tests.
    """

    now = datetime.now(timezone.utc)

    return ProjectModel(
        project_id=project_id,
        name="API Integration Test Project",
        description=(
            "Project created during API integration testing."
        ),
        status="draft",
        created_at=now,
        updated_at=now,
    )


def create_video_model(
    video_id: str = "api_video_001",
    project_id: str = "api_project_001",
) -> VideoModel:
    """
    Create a valid VideoModel for database-backed API tests.
    """

    return VideoModel(
        video_id=video_id,
        project_id=project_id,
        title="API Test Video",
        duration=60,
        status="completed",
        resolution="1920x1080",
        fps=30,
        file_path="/videos/api_test.mp4",
        thumbnail_path="/videos/api_test.jpg",
        created_at=datetime.now(timezone.utc),
    )


# ===========================================================================
# Root endpoint
# ===========================================================================

def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Agentic Backend"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


# ===========================================================================
# Health endpoints
# ===========================================================================

def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Agentic Backend is healthy."
    assert data["data"]["status"] == "healthy"
    assert "timestamp" in data["data"]


def test_liveness_endpoint(client):
    response = client.get("/health/live")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Application is alive."
    assert data["data"]["status"] == "alive"


def test_readiness_endpoint(client):
    response = client.get("/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["message"] == "Application is ready."
    assert data["data"]["status"] == "ready"


# ===========================================================================
# Generation endpoint
# ===========================================================================

def test_generation_endpoint_runs_complete_workflow(client):
    payload = create_generation_payload()

    response = client.post(
        "/generation",
        json=payload,
    )

    assert response.status_code == 202

    data = response.json()

    assert data["success"] is True
    assert (
        data["message"]
        == "Video generation workflow completed."
    )

    result = data["data"]

    assert result["status"] == "completed"
    assert result["request"]["prompt"] == payload["prompt"]
    assert result["request"]["duration"] == payload["duration"]

    assert result["plan"] is not None
    assert result["script"] is not None
    assert result["storyboard"] is not None
    assert result["error"] is None


def test_generation_endpoint_preserves_request_data(client):
    payload = create_generation_payload()

    response = client.post(
        "/generation",
        json=payload,
    )

    assert response.status_code == 202

    data = response.json()
    result = data["data"]

    assert result["status"] == "completed"

    request_data = result["request"]

    assert request_data["prompt"] == payload["prompt"]
    assert request_data["duration"] == payload["duration"]
    assert request_data["style"] == payload["style"]
    assert (
        request_data["target_audience"]
        == payload["target_audience"]
    )
    assert request_data["tone"] == payload["tone"]


def test_generation_endpoint_rejects_invalid_request(client):
    payload = {
        "prompt": "",
        "duration": 60,
        "style": "professional",
        "target_audience": "Potential customers",
        "tone": "confident",
    }

    response = client.post(
        "/generation",
        json=payload,
    )

    assert response.status_code == 422


def test_generation_endpoint_requires_prompt(client):
    payload = {
        "duration": 60,
        "style": "professional",
        "target_audience": "Potential customers",
        "tone": "confident",
    }

    response = client.post(
        "/generation",
        json=payload,
    )

    assert response.status_code == 422


# ===========================================================================
# Project endpoints
# ===========================================================================

def test_create_project(client):
    payload = create_project_payload()

    response = client.post(
        "/projects",
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["project_id"] == "api_project_001"
    assert data["name"] == "API Integration Test Project"
    assert (
        data["description"]
        == "Project created during API integration testing."
    )
    assert data["status"] == "draft"

    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_project_rejects_duplicate_project(client):
    payload = create_project_payload()

    first_response = client.post(
        "/projects",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/projects",
        json=payload,
    )

    assert second_response.status_code == 409

    data = second_response.json()

    assert "already exists" in data["detail"]


def test_list_projects(client):
    client.post(
        "/projects",
        json=create_project_payload(),
    )

    response = client.get("/projects")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["project_id"] == "api_project_001"


def test_list_projects_returns_empty_list_when_empty(client):
    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == []


def test_get_project(client):
    client.post(
        "/projects",
        json=create_project_payload(
            "api_project_002",
        ),
    )

    response = client.get(
        "/projects/api_project_002",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["project_id"] == "api_project_002"


def test_get_missing_project_returns_404(client):
    response = client.get(
        "/projects/does_not_exist",
    )

    assert response.status_code == 404

    data = response.json()

    assert (
        data["detail"]
        == "Project 'does_not_exist' was not found."
    )


# ===========================================================================
# Video endpoints
# ===========================================================================

def test_list_videos_returns_empty_list_when_empty(client):
    response = client.get("/videos")

    assert response.status_code == 200
    assert response.json() == []


def test_list_videos_returns_existing_videos(
    client,
    db_session,
):
    """
    Verify that the video API reads videos from the database.
    """

    project = create_project_model()

    db_session.add(project)
    db_session.commit()

    video = create_video_model()

    db_session.add(video)
    db_session.commit()

    response = client.get("/videos")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    assert data[0]["video_id"] == "api_video_001"


def test_get_video(
    client,
    db_session,
):
    """
    Verify that a video can be retrieved from the database.
    """

    project = create_project_model()

    db_session.add(project)
    db_session.commit()

    video = create_video_model(
        "api_video_002",
    )

    db_session.add(video)
    db_session.commit()

    response = client.get(
        "/videos/api_video_002",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["video_id"] == "api_video_002"
    assert data["project_id"] == "api_project_001"
    assert data["title"] == "API Test Video"
    assert data["duration"] == 60
    assert data["status"] == "completed"


def test_get_missing_video_returns_404(client):
    response = client.get(
        "/videos/does_not_exist",
    )

    assert response.status_code == 404

    data = response.json()

    assert (
        data["detail"]
        == "Video 'does_not_exist' was not found."
    )


# ===========================================================================
# OpenAPI
# ===========================================================================

def test_openapi_contains_expected_api_paths(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    expected_paths = {
        "/",
        "/health",
        "/health/live",
        "/health/ready",
        "/generation",
        "/projects",
        "/projects/{project_id}",
        "/videos",
        "/videos/{video_id}",
    }

    assert expected_paths.issubset(
        set(paths.keys()),
    )