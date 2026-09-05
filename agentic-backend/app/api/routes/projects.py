"""
Project API routes.

This module exposes HTTP endpoints for creating and retrieving
video-generation projects.

Business logic is delegated to ProjectService.
Database persistence is handled by ProjectRepository.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_project_service
from app.schemas.project import Project
from app.services.project_service import ProjectService


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


# ---------------------------------------------------------------------------
# Create project
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    project: Project,
    service: ProjectService = Depends(
        get_project_service,
    ),
) -> Project:
    """
    Create a new project.
    """

    try:
        return service.create_project(
            project,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# List projects
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[Project],
)
def list_projects(
    service: ProjectService = Depends(
        get_project_service,
    ),
) -> List[Project]:
    """
    Return all projects.
    """

    return service.list_projects()


# ---------------------------------------------------------------------------
# Get project
# ---------------------------------------------------------------------------

@router.get(
    "/{project_id}",
    response_model=Project,
)
def get_project(
    project_id: str,
    service: ProjectService = Depends(
        get_project_service,
    ),
) -> Project:
    """
    Return a project by its identifier.
    """

    project = service.get_project(
        project_id,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Project '{project_id}' "
                "was not found."
            ),
        )

    return project