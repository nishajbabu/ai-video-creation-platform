"""
Project database repository.

This module contains database-specific operations for ProjectModel.

The repository is responsible only for persistence. Business rules
remain in ProjectService.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.project import ProjectModel


class ProjectRepository:
    """
    Repository responsible for ProjectModel persistence.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a SQLAlchemy session.
        """

        self.session = session

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        project: ProjectModel,
    ) -> ProjectModel:
        """
        Persist a new project.
        """

        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)

        return project

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(
        self,
        project_id: str,
    ) -> Optional[ProjectModel]:
        """
        Return a project by ID.

        Returns None when the project does not exist.
        """

        return (
            self.session.query(ProjectModel)
            .filter(
                ProjectModel.project_id == project_id,
            )
            .first()
        )

    def list(self) -> List[ProjectModel]:
        """
        Return all projects.
        """

        return (
            self.session.query(ProjectModel)
            .order_by(ProjectModel.created_at)
            .all()
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        project: ProjectModel,
    ) -> ProjectModel:
        """
        Persist changes made to an existing project.
        """

        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)

        return project

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        project: ProjectModel,
    ) -> None:
        """
        Delete a project from the database.
        """

        self.session.delete(project)
        self.session.commit()

    # ------------------------------------------------------------------
    # Existence
    # ------------------------------------------------------------------

    def exists(
        self,
        project_id: str,
    ) -> bool:
        """
        Return whether a project exists.
        """

        return (
            self.session.query(ProjectModel)
            .filter(
                ProjectModel.project_id == project_id,
            )
            .first()
            is not None
        )