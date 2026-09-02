# Agentic Backend

A modular FastAPI backend for an agentic AI video-generation system.

The backend provides the API, orchestration layer, LLM abstraction, database persistence, project/video/scene/asset management, and integration contracts required by downstream media-generation services.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Workflow](#core-workflow)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [LLM Provider System](#llm-provider-system)
- [Provider Priority](#provider-priority)
- [Environment Configuration](#environment-configuration)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Swagger API Documentation](#swagger-api-documentation)
- [Testing](#testing)
- [Running Specific Tests](#running-specific-tests)
- [Database](#database)
- [Video Generation Workflow](#video-generation-workflow)
- [Separation of Concerns](#separation-of-concerns)
- [Error Handling](#error-handling)
- [Current Limitations](#current-limitations)
- [Development Guidelines](#development-guidelines)
- [Security Guidelines](#security-guidelines)
- [Troubleshooting](#troubleshooting)
- [Project Status](#project-status)
- [Verification Checklist](#verification-checklist)
- [Author](#author)
- [License](#license)

---

## Overview

Agentic Backend is the backend component of an agentic AI video-generation platform.

The system accepts a natural-language video request and passes it through an agentic workflow:

```text
Client
  |
  v
FastAPI
  |
  v
Generation API
  |
  v
GenerationService
  |
  v
Orchestrator
  |
  +----------------+
  |                |
  v                v
Planner         Script Agent
  |                |
  +-------+--------+
          |
          v
   Storyboard Agent
          |
          v
     Scene Data
          |
          +--------------------+
          |                    |
          v                    v
    Asset Module        Media Generation
```

The backend is intentionally separated into API, service, repository, model, schema, agent, and LLM layers. This keeps business logic independent from HTTP and database implementation details.

---

## Architecture

The project follows a layered architecture.

```text
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │      API Routes      │
                    └──────────┬───────────┘
                               │
                               v
                    ┌──────────────────────┐
                    │   Application        │
                    │      Services        │
                    └──────────┬───────────┘
                               │
                               v
                    ┌──────────────────────┐
                    │      Agents /        │
                    │    Orchestrator      │
                    └──────────┬───────────┘
                               │
                               v
                    ┌──────────────────────┐
                    │      LLMService      │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              v                v                v
           OpenAI           Gemini            Groq
              │
              v
          Anthropic
```

**Database Flow:**

```text
API
 |
 v
Service
 |
 v
Repository
 |
 v
SQLAlchemy
 |
 v
Database
```

---

## Core Workflow

A video request enters through:

```http
POST /generation
```

The request is represented by `VideoRequest`.

The workflow then follows:

```text
VideoRequest
     |
     v
GenerationService
     |
     v
Orchestrator
     |
     v
Planner
     |
     v
Script Agent
     |
     v
Storyboard Agent
     |
     v
Scenes
```

The resulting scene information can then be consumed by downstream media-generation systems.

---

## Features

### API Layer

- FastAPI application
- Swagger/OpenAPI documentation
- Health endpoint
- Project endpoints
- Video endpoints
- Scene endpoints
- Asset endpoints
- Generation endpoint

### Agentic Layer

- Orchestrator
- Planner Agent
- Script Agent
- Storyboard Agent
- Multi-stage generation workflow

### LLM Layer

- Provider abstraction
- Multiple API keys per provider
- Provider priority
- API-key health tracking
- Retry handling
- Provider fallback
- Structured generation
- Centralized LLM service

Supported providers:

- OpenAI
- Google Gemini
- Groq
- Anthropic

### Persistence Layer

- SQLAlchemy
- Repository pattern
- Project persistence
- Video persistence
- Scene persistence
- Asset persistence

### Validation

- Pydantic schemas
- Request validation
- Response validation
- Domain-level validation

### Testing

The current backend test suite contains:

```text
664 passed
```

The tests cover API, services, repositories, agents, LLM components, schemas, and integration workflows.

---

## Tech Stack

| Category               | Technology                                  |
| ----------------------- | -------------------------------------------- |
| Language                | Python                                       |
| API Framework           | FastAPI                                      |
| ASGI Server             | Uvicorn                                      |
| Validation              | Pydantic                                     |
| ORM                     | SQLAlchemy                                   |
| Database                | Configurable through project database layer  |
| Testing                 | Pytest                                       |
| LLM Providers           | OpenAI, Gemini, Groq, Anthropic              |
| API Documentation       | OpenAPI / Swagger UI                         |
| Environment Management  | Environment variables / `.env`               |
| Version Control         | Git                                          |

---

## Project Structure

```text
agentic-backend/
│
├── app/
│   │
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── script.py
│   │   └── storyboard.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   │
│   │   └── routes/
│   │       ├── health.py
│   │       ├── projects.py
│   │       ├── videos.py
│   │       ├── scenes.py
│   │       ├── assets.py
│   │       └── generation.py
│   │
│   ├── core/
│   │   ├── dependencies.py
│   │   └── startup.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── session.py
│   │
│   ├── llm/
│   │   ├── base.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── key_manager.py
│   │   ├── retry.py
│   │   ├── service.py
│   │   │
│   │   └── providers/
│   │       ├── openai_provider.py
│   │       ├── gemini_provider.py
│   │       ├── groq_provider.py
│   │       └── anthropic_provider.py
│   │
│   ├── models/
│   │   ├── project.py
│   │   ├── video.py
│   │   ├── scene.py
│   │   └── asset.py
│   │
│   ├── repositories/
│   │   ├── project_repository.py
│   │   ├── video_repository.py
│   │   ├── scene_repository.py
│   │   └── asset_repository.py
│   │
│   ├── schemas/
│   │   ├── requests.py
│   │   ├── responses.py
│   │   ├── project.py
│   │   ├── video.py
│   │   ├── scene.py
│   │   ├── asset.py
│   │   ├── media_generation.py
│   │   ├── plan.py
│   │   ├── script.py
│   │   └── storyboard.py
│   │
│   ├── services/
│   │   ├── project_service.py
│   │   ├── video_service.py
│   │   ├── asset_service.py
│   │   └── generation_service.py
│   │
│   └── main.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## API Endpoints

### Health

```http
GET /
```

Returns basic application information.

---

### Projects

Project-related endpoints are available under:

```text
/projects
```

---

### Videos

**List videos**

```http
GET /videos
```

Returns all generated video records.

**Get video**

```http
GET /videos/{video_id}
```

**Get media-generation inputs**

```http
GET /videos/{video_id}/media-inputs
```

Returns scene information required by the downstream media-generation module.

Example:

```json
{
  "video_id": "video-001",
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "A short introduction.",
      "visual_prompt": "A modern city at sunrise.",
      "voice": null
    }
  ]
}
```

---

### Scenes

**List scenes**

```http
GET /scenes
```

**List scenes for a video**

```http
GET /scenes/video/{video_id}
```

**Get scene**

```http
GET /scenes/{scene_id}
```

---

### Assets

**List assets**

```http
GET /assets
```

**Create asset**

```http
POST /assets
```

Example:

```json
{
  "scene_id": null,
  "asset_type": "image",
  "description": "Product reference image",
  "source": "user_upload",
  "file_path": null,
  "url": "https://example.com/product.jpg"
}
```

**Get asset**

```http
GET /assets/{asset_id}
```

**Get assets for a scene**

```http
GET /assets/scene/{scene_id}
```

**Get unassigned assets**

```http
GET /assets/unassigned
```

---

### Generation

**Start generation**

```http
POST /generation
```

Request:

```json
{
  "prompt": "Create a short educational video about solar energy.",
  "duration": 10,
  "style": "clean educational",
  "target_audience": "general audience",
  "tone": "informative",
  "supporting_files": []
}
```

The minimum valid request is:

```json
{
  "prompt": "Explain solar energy.",
  "duration": 10
}
```

The prompt must contain at least 10 characters.

---

## LLM Provider System

The backend does not allow agents to directly depend on individual LLM SDKs.

Instead, agents communicate through:

```text
LLMService
```

The service handles:

```text
Agent
  |
  v
LLMService
  |
  v
KeyManager
  |
  +------ OpenAI
  |
  +------ Gemini
  |
  +------ Groq
  |
  +------ Anthropic
```

This provides a single abstraction point for all LLM calls.

---

## Provider Priority

The default provider priority is:

```text
OpenAI
   ↓
Gemini
   ↓
Groq
   ↓
Anthropic
```

Multiple API keys can be configured for each provider. For example:

```env
OPENAI_API_KEY_1=...
OPENAI_API_KEY_2=...

GEMINI_API_KEY_1=...
GEMINI_API_KEY_2=...

GROQ_API_KEY_1=...
GROQ_API_KEY_2=...

ANTHROPIC_API_KEY_1=...
ANTHROPIC_API_KEY_2=...
```

The key manager tracks key health and allows failed keys to be temporarily avoided.

---

## Environment Configuration

Create a local `.env` file.

Do **not** commit the real `.env` file to GitHub.

Example:

```env
# -------------------------------------------------
# OpenAI
# -------------------------------------------------

OPENAI_API_KEY_1=your-openai-key
OPENAI_API_KEY_2=your-second-openai-key

OPENAI_MODEL=gpt-4o-mini


# -------------------------------------------------
# Gemini
# -------------------------------------------------

GEMINI_API_KEY_1=your-gemini-key
GEMINI_API_KEY_2=your-second-gemini-key

GEMINI_MODEL=gemini-2.5-flash


# -------------------------------------------------
# Groq
# -------------------------------------------------

GROQ_API_KEY_1=your-groq-key
GROQ_API_KEY_2=your-second-groq-key

GROQ_MODEL=llama-3.3-70b-versatile


# -------------------------------------------------
# Anthropic
# -------------------------------------------------

ANTHROPIC_API_KEY_1=your-anthropic-key
ANTHROPIC_API_KEY_2=your-second-anthropic-key

ANTHROPIC_MODEL=claude-3-5-haiku-latest
```

Use `.env.example` to document required variables without exposing credentials.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Ilavarasan-v/Agentic-Backend.git
cd Agentic-Backend
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell activation is blocked, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create:

```text
.env
```

and add the required provider credentials.

Example:

```env
OPENAI_API_KEY_1=your-key
GEMINI_API_KEY_1=your-key
GROQ_API_KEY_1=your-key
ANTHROPIC_API_KEY_1=your-key
```

Only configure the providers you actually have access to.

---

## Running the Application

Start the development server:

```powershell
uvicorn app.main:app --reload
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

The API is now available at:

```text
http://127.0.0.1:8000
```

---

## Swagger API Documentation

FastAPI automatically generates interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

The Swagger UI allows you to:

- Inspect endpoints
- View request schemas
- Submit API requests
- Inspect responses
- Test validation
- Test database-backed endpoints

Alternative OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

---

## Testing

Run the complete test suite:

```powershell
pytest -q
```

Current baseline:

```text
664 passed
```

A successful run should look approximately like:

```text
664 passed in ...
```

---

## Running Specific Tests

Run integration tests:

```powershell
pytest tests/integration -q
```

Run unit tests:

```powershell
pytest tests/unit -q
```

Run a specific test file:

```powershell
pytest tests/integration/test_api_workflow.py -q
```

Run with verbose output:

```powershell
pytest -v
```

---

## Database

Database persistence follows the repository pattern.

The flow is:

```text
API Route
    |
    v
Service
    |
    v
Repository
    |
    v
SQLAlchemy
    |
    v
Database
```

For example:

```text
Asset API
    ↓
AssetService
    ↓
AssetRepository
    ↓
AssetModel
    ↓
assets table
```

The same pattern is used for projects, videos, and scenes.

---

## Video Generation Workflow

The intended generation workflow is:

```text
POST /generation
        |
        v
VideoRequest
        |
        v
GenerationService
        |
        v
Orchestrator
        |
        v
Planner
        |
        v
Script Agent
        |
        v
Storyboard Agent
        |
        v
Scene Information
        |
        v
Downstream Media Generation
```

The backend is responsible for preparing and orchestrating the generation workflow. The actual visual/video rendering is intended to be handled by downstream media-generation components.

---

## Separation of Concerns

The project intentionally separates responsibilities.

### Routes

Routes handle:

- HTTP requests
- HTTP responses
- Dependency injection
- Status codes
- API validation

Routes should not contain business logic.

### Services

Services contain application/business logic.

Example:

```text
AssetService
VideoService
ProjectService
GenerationService
```

### Repositories

Repositories contain database operations.

Example:

```text
AssetRepository
VideoRepository
ProjectRepository
SceneRepository
```

Repositories should not contain application-level workflow logic.

### Models

Models represent persistent database entities.

Examples:

```text
ProjectModel
VideoModel
SceneModel
AssetModel
```

### Schemas

Pydantic schemas define API/domain contracts.

Examples:

```text
VideoRequest
Video
Scene
Asset
Plan
Script
Storyboard
```

### Agents

Agents implement the AI workflow.

Examples:

```text
Planner
Script Agent
Storyboard Agent
Orchestrator
```

---

## Error Handling

The LLM layer uses application-specific exceptions rather than exposing raw provider SDK errors throughout the application.

Examples include:

```text
LLMError
LLMQuotaExceededError
LLMAuthenticationError
LLMInvalidRequestError
AllLLMProvidersExhaustedError
```

This allows the application to distinguish between:

- Authentication failures
- Quota failures
- Invalid requests
- Provider failures
- Exhausted fallback providers

---

## Current Limitations

### LLM API Credits

The generation endpoint requires access to at least one configured LLM provider with available API credits/quota.

If all configured providers are unavailable, the generation request will fail with an error similar to:

```text
All available LLM providers and API keys failed
for this structured request.
```

This is an external provider/account limitation rather than a FastAPI routing problem. The rest of the backend can still be tested independently.

---

## Development Guidelines

### 1. Keep routes thin

Avoid putting business logic inside route handlers.

Bad:

```python
@router.post("/something")
def endpoint():
    # complex business logic
```

Prefer:

```text
Route
  ↓
Service
  ↓
Repository / Agent
```

### 2. Do not call LLM providers directly from agents

Use:

```python
LLMService
```

instead of directly creating provider clients. This preserves:

- Fallback
- Retries
- Key management
- Centralized error handling

### 3. Keep database access inside repositories

Services should use repositories rather than writing SQLAlchemy queries directly.

### 4. Validate API input with Pydantic

Request and response contracts should remain explicit.

### 5. Run tests before committing

Always run:

```powershell
pytest -q
```

before pushing changes.

The current stable baseline is:

```text
664 passed
```

If the count drops unexpectedly, investigate before committing.

---

## Security Guidelines

Never commit:

```text
.env
API keys
passwords
database credentials
private certificates
tokens
```

Use `.env.example` for documenting required environment variables.

Before pushing to GitHub:

```powershell
git status
```

and verify that `.env` is not listed.

---

## Troubleshooting

### Uvicorn does not start

Check that the virtual environment is active:

```powershell
.venv\Scripts\Activate.ps1
```

Then:

```powershell
uvicorn app.main:app --reload
```

### ModuleNotFoundError

Install dependencies:

```powershell
pip install -r requirements.txt
```

Verify the Python interpreter:

```powershell
python --version
```

Verify pip:

```powershell
python -m pip --version
```

### Swagger returns 404

Use:

```text
http://127.0.0.1:8000/docs
```

The project uses FastAPI's default Swagger route.

### `/videos` returns an empty list

This is expected when no video records have been created.

```json
[]
```

A video ID is required before querying:

```text
/videos/{video_id}
```

or:

```text
/videos/{video_id}/media-inputs
```

### Generation returns HTTP 500

Check the Uvicorn terminal.

The generation workflow depends on the configured LLM providers. If all providers have exhausted their quota or credits, generation cannot proceed until a working provider is available.

---

## Project Status

### Backend foundation — Complete

- FastAPI application
- API routing
- Dependency injection
- Service layer
- Repository layer
- SQLAlchemy models
- Pydantic schemas
- LLM abstraction
- Provider fallback
- Key management
- Agent orchestration
- Swagger documentation

### Testing — Passing

```text
664 tests passed
```

### External AI generation — Provider-dependent

Actual generation requires available LLM API credentials and quota.

### Downstream media generation

The backend exposes the integration contract required to pass scene information to the downstream media-generation module.

---

## Verification Checklist

Before considering the backend ready:

- [x] Application starts
- [x] Swagger loads
- [x] Health endpoint works
- [x] Project endpoints work
- [x] Video endpoints work
- [x] Scene endpoints work
- [x] Asset endpoints work
- [x] LLM abstraction is available
- [x] Provider fallback is implemented
- [x] Database repositories work
- [x] 664 tests pass
- [ ] External LLM generation requires valid provider quota
- [ ] Downstream media-generation service must be connected for final rendering

---

## Author

**Ilavarasan**

GitHub: [https://github.com/Ilavarasan-v/Agentic-Backend](https://github.com/Ilavarasan-v/Agentic-Backend)

---

---

## API Testing Guide

With the backend at the **664 passing tests** baseline, the API can be tested systematically through Swagger at:

```text
http://127.0.0.1:8000/docs
```

Some endpoints depend on IDs created by earlier endpoints, so follow the order below.

### 1. Health / Root

```http
GET /
```

No input required.

Expected:

```json
{
  "name": "Agentic Backend",
  "version": "0.1.0",
  "status": "running"
}
```

### 2. Projects

```http
GET /projects
```

No input. If no projects exist yet, an empty array is fine:

```json
[]
```

**Project creation**

If your Swagger exposes `POST /projects`, use:

```json
{
  "name": "Solar Energy Demo",
  "description": "A short educational video about solar energy."
}
```

Save the returned `project_id` (e.g. `project-001`). Use the actual ID returned by your API, not the example.

### 3. Videos

```http
GET /videos
```

No input. May initially return:

```json
[]
```

That's normal.

```http
GET /videos/{video_id}
```

Requires an existing video ID (e.g. `video-001`). Only use this if the video actually exists — otherwise a `404` is expected.

### 4. Scenes

```http
GET /scenes
```

No input. An empty array is okay if no scenes exist.

```http
GET /scenes/video/{video_id}
```

Enter an existing video ID (e.g. `video-001`). If the video has no scenes, `[]` is acceptable.

```http
GET /scenes/{scene_id}
```

Enter `scene_id: 1` — but it must actually exist, or you'll get:

```text
404 Scene '1' was not found.
```

That's expected behavior.

### 5. Assets

This section is easy to test since asset `1` should already exist.

```http
GET /assets
```

No input. Expected something like:

```json
[
  {
    "scene_id": null,
    "asset_type": "image",
    "description": "Test product image",
    "source": "user_upload",
    "file_path": null,
    "url": "https://example.com/test-image.jpg",
    "asset_id": 1,
    "created_at": "..."
  }
]
```

### 6. Create Asset

```http
POST /assets
```

Use:

```json
{
  "scene_id": null,
  "asset_type": "image",
  "description": "Solar panel reference image",
  "source": "user_upload",
  "file_path": null,
  "url": "https://example.com/solar-panel.jpg"
}
```

Expected: `201`, with a response similar to:

```json
{
  "scene_id": null,
  "asset_type": "image",
  "description": "Solar panel reference image",
  "source": "user_upload",
  "file_path": null,
  "url": "https://example.com/solar-panel.jpg",
  "asset_id": 2,
  "created_at": "..."
}
```

Save the returned `asset_id`.

### 7. Get Asset

```http
GET /assets/{asset_id}
```

Enter `asset_id: 1`. Since asset 1 already exists, this should return `200`.

### 8. Get Unassigned Assets

```http
GET /assets/unassigned
```

No input. Returns assets whose `scene_id` is `null`, e.g.:

```json
[
  {
    "scene_id": null,
    "asset_type": "image",
    "description": "Test product image",
    "source": "user_upload",
    "file_path": null,
    "url": "https://example.com/test-image.jpg",
    "asset_id": 1,
    "created_at": "..."
  }
]
```

**Important:** if `/assets/{asset_id}` is matched before `/assets/unassigned`, you may see:

```text
422
Input should be a valid integer
input: "unassigned"
```

Keep an eye on this endpoint — with correct route ordering, `/assets/unassigned` should return `200`.

### 9. Get Assets for Scene

```http
GET /assets/scene/{scene_id}
```

Enter `scene_id: 1`. If scene 1 exists but has no assets, `[]` is fine. If scene 1 doesn't exist yet, don't treat an empty result as proof of a problem — the repository may simply return no matching assets.

### 10. Video Media Inputs

```http
GET /videos/{video_id}/media-inputs
```

This is the important one — it's the backend → media-generation integration contract.

Requires a real video ID (e.g. `video-001`).

- Video doesn't exist → `404`
- Video exists but has no scenes → `404 No scenes were found for video '...'.`
- Everything exists → response like:

```json
{
  "video_id": "video-001",
  "project_id": "project-001",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "Solar energy comes from sunlight.",
      "visual_prompt": "Solar panels receiving sunlight on a modern rooftop.",
      "voice": null
    }
  ]
}
```

### 11. Generation

```http
POST /generation
```

This one can't currently be expected to succeed, since the configured LLM providers have exhausted their available credits — but request validation can still be verified.

Smallest valid request:

```json
{
  "prompt": "Explain solar energy.",
  "duration": 10
}
```

The prompt must be at least 10 characters, and `duration` must be at least 10 seconds.

You will likely get `500 Internal Server Error` until one of the configured LLM providers has usable quota. That's an external API-credit limitation, not evidence that the FastAPI endpoint itself is broken.

### Recommended Testing Sequence

```text
1.  GET  /
       ↓
2.  GET  /projects
       ↓
3.  POST /projects          ← if available
       ↓
4.  GET  /projects/{id}
       ↓
5.  GET  /videos
       ↓
6.  GET  /scenes
       ↓
7.  POST /assets
       ↓
8.  GET  /assets
       ↓
9.  GET  /assets/{asset_id}
       ↓
10. GET  /assets/unassigned
       ↓
11. GET  /assets/scene/{scene_id}
       ↓
12. GET  /scenes/video/{video_id}
       ↓
13. GET  /scenes/{scene_id}
       ↓
14. GET  /videos/{video_id}
       ↓
15. GET  /videos/{video_id}/media-inputs
       ↓
16. POST /generation       ← expected to fail until LLM quota is available
```

### What Counts as Success Right Now?

For the database/API endpoints:

| Result | Meaning |
| ------ | ------- |
| `200` | Good |
| `201` | Good, for creation |
| `404` for a deliberately nonexistent ID | Also good |
| `422` for deliberately invalid input | Good validation |
| `500` | Investigate |
