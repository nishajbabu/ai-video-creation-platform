"""
Project application service.

This module contains project-related business logic.

The service converts between Pydantic API schemas and SQLAlchemy
database models while delegating persistence to ProjectRepository.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.models.project import ProjectModel
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import Project


class ProjectService:
    """
    Application service responsible for project operations.

    Business logic lives here.
    Database persistence is delegated to ProjectRepository.

    Dependency flow:

        Project schema
            ↓
        ProjectService
            ↓
        ProjectModel
            ↓
        ProjectRepository
            ↓
        Database
    """

    def __init__(
        self,
        repository: ProjectRepository,
    ):
        """
        Initialize the project service.
        """

        self.repository = repository

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_model(
        project: Project,
    ) -> ProjectModel:
        """
        Convert a Pydantic Project into a SQLAlchemy ProjectModel.
        """

        return ProjectModel(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @staticmethod
    def _to_schema(
        project: ProjectModel,
    ) -> Project:
        """
        Convert a SQLAlchemy ProjectModel into a Pydantic Project.

        SQLite may return DateTime values without timezone information.
        Project timestamps are defined as UTC, so naive timestamps are
        normalized back to timezone-aware UTC timestamps.
        """

        created_at = project.created_at
        updated_at = project.updated_at

        if created_at.tzinfo is None:
            created_at = created_at.replace(
                tzinfo=timezone.utc,
            )

        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(
                tzinfo=timezone.utc,
            )

        return Project(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            status=project.status,
            created_at=created_at,
            updated_at=updated_at,
        )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_project(
        self,
        project: Project,
    ) -> Project:
        """
        Create and persist a project.

        Raises:
            ValueError:
                If a project with the same ID already exists.
        """

        if self.repository.exists(
            project.project_id,
        ):
            raise ValueError(
                f"Project '{project.project_id}' already exists."
            )

        now = datetime.now(timezone.utc)

        project.created_at = now
        project.updated_at = now

        model = self._to_model(
            project,
        )

        saved_model = self.repository.create(
            model,
        )

        return self._to_schema(
            saved_model,
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_project(
        self,
        project_id: str,
    ) -> Optional[Project]:
        """
        Return a project by ID.

        Returns None when the project does not exist.
        """

        model = self.repository.get(
            project_id,
        )

        if model is None:
            return None

        return self._to_schema(
            model,
        )

    def list_projects(self) -> List[Project]:
        """
        Return all stored projects.
        """

        models = self.repository.list()

        return [
            self._to_schema(model)
            for model in models
        ]

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_project(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Project]:
        """
        Update selected project fields.

        Returns:
            Updated project if found, otherwise None.
        """

        model = self.repository.get(
            project_id,
        )

        if model is None:
            return None

        if name is not None:
            model.name = name

        if description is not None:
            model.description = description

        if status is not None:
            model.status = status

        model.updated_at = datetime.now(
            timezone.utc,
        )

        updated_model = self.repository.update(
            model,
        )

        return self._to_schema(
            updated_model,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_project(
        self,
        project_id: str,
    ) -> bool:
        """
        Delete a project.

        Returns:
            True if the project existed and was deleted.
            False otherwise.
        """

        model = self.repository.get(
            project_id,
        )

        if model is None:
            return False

        self.repository.delete(
            model,
        )

        return True

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(
        self,
        project_id: str,
    ) -> bool:
        """
        Check whether a project exists.
        """

        return self.repository.exists(
            project_id,
        )

    def clear(self) -> None:
        """
        Clear all projects.

        This operation is intentionally repository-dependent.
        """

        for model in self.repository.list():
            self.repository.delete(
                model,
            )